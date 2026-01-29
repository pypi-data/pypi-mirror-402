import argparse
import asyncio
import logging
import platform
import signal
import sys
import threading
import typing as t

import jupyter_client
from jupyter_client import AsyncKernelClient, AsyncKernelManager

from .config import get_logger, setup_logging
from .kernel_manager import shutdown_kernel, start_kernel
from .message_handler import handle_kernel_output, handle_stdin_input

log = get_logger(__name__)

_T = t.TypeVar('_T')


async def _setup_streams() -> t.Tuple[
    asyncio.StreamReader, asyncio.StreamWriter
]:
    """Sets up asyncio StreamReader and StreamWriter for stdin/stdout."""
    loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(
        writer_transport, writer_protocol, None, loop
    )
    return reader, writer


async def _ignore_cancelled(coro: t.Awaitable[_T]) -> t.Optional[_T]:
    """
    Await `coro`, catching only CancelledError and returning None.
    Let any other exception propagate as normal.
    """
    try:
        return await coro
    except asyncio.CancelledError:
        # We explicitly ignore CancelledError
        return None


async def _run_multiplexer(
    km: AsyncKernelManager,
    client: AsyncKernelClient,
    shutdown_event: asyncio.Event,
) -> None:
    """Creates and manages the core I/O tasks."""
    reader, writer = await _setup_streams()
    loop = asyncio.get_running_loop()

    log.info('Creating I/O tasks...')
    # Task to read JSONL from stdin and route to kernel
    stdin_task = loop.create_task(
        _ignore_cancelled(
            handle_stdin_input(reader, client, km, shutdown_event),
        ),
        name='StdinHandler',
    )

    # Tasks to read from KERNEL channels and write JSONL to stdout
    output_tasks = [
        loop.create_task(
            _ignore_cancelled(
                handle_kernel_output('iopub', client, writer, shutdown_event),
            ),
            name='KernelOutput-iopub',
        ),
        loop.create_task(
            _ignore_cancelled(
                handle_kernel_output('stdin', client, writer, shutdown_event),
            ),
            name='KernelOutput-stdin',
        ),
        loop.create_task(
            _ignore_cancelled(
                handle_kernel_output('shell', client, writer, shutdown_event),
            ),
            name='KernelOutput-shell',
        ),
    ]

    log.info('Running I/O tasks. Multiplexer is active.')
    log.info('Input Format: JSON Lines (one JSON object per line on stdin)')
    log.info('Output Format: JSON Lines (iopub/stdin messages only to stdout)')

    await shutdown_event.wait()
    log.info('Shutdown signal received, proceeding with cleanup...')

    # Stop reading stdin
    if not stdin_task.done():
        log.debug('Cancelling stdin task...')
        stdin_task.cancel()

    try:
        await stdin_task
    finally:
        log.info('Waiting briefly for final kernel messages...')
        sleep_time = 10.0
        # PyPy needs more time to start up.
        if platform.python_implementation() == 'PyPy':
            sleep_time = 20.0
        await asyncio.sleep(sleep_time)

        # Cancel remaining kernel output tasks
        log.debug('Cancelling kernel output tasks...')
        for task in output_tasks:
            if not task.done():
                task.cancel()

        # Wait for all output tasks to finish cancellation
        await asyncio.gather(*[t for t in output_tasks])
        log.debug('Kernel output tasks finished.')


async def main_async(args: argparse.Namespace) -> None:
    """Asynchronous main function doing the setup and orchestration."""
    km = None
    client = None
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    # --- Setup Signal Handlers ---
    def request_shutdown(sig: signal.Signals) -> None:
        log.warning('Received signal %s, initiating shutdown...', sig.name)
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_shutdown, sig)
        except NotImplementedError:
            log.warning(
                'Cannot add signal handler for %s on this platform.', sig.name
            )

    try:
        km = await start_kernel(args.kernel_name)

        class HBChannel(
            jupyter_client.channels.HBChannel,
            jupyter_client.channelsabc.HBChannelABC,
        ):
            time_to_dead = 10

            def call_handlers(self, since_last_heartbeat: float) -> None:
                log.error(
                    'Heartbeat failed, last heartbeat %d second(s) ago',
                    since_last_heartbeat,
                )
                shutdown_event.set()

        client = km.client()
        client.hb_channel_class = HBChannel
        client.start_channels()
        log.info('Kernel client channels starting...')

        if not await km.is_alive():
            log.error(
                'Kernel process died unexpectedly after starting channels.'
            )
            try:
                client.stop_channels()  # Attempt to stop channels
            except Exception:
                pass  # Ignore errors here, focusing on kernel shutdown
            await shutdown_kernel(km)  # Ensure cleanup
            raise RuntimeError('Kernel died after channel startup')

        log.info('Kernel client channels started and kernel is alive.')

        # Run the core multiplexer loop
        await _run_multiplexer(km, client, shutdown_event)

    except Exception as e:
        log.critical('Core execution error', exc_info=True)
        # Ensure shutdown event is set to break loops if error occurred mid-run
        if not shutdown_event.is_set():
            shutdown_event.set()
        # Indicate failure
        raise
    finally:
        log.info('Starting final cleanup in main_async...')

        # Stop client channels first (if client exists)
        if client:
            log.info('Stopping kernel client channels...')
            try:
                client.stop_channels()
                log.info('Client channels stopped.')
            except Exception as e:
                log.warning('Error stopping client channels', exc_info=True)

        # Shutdown kernel process (if km exists)
        if km:
            await shutdown_kernel(km)  # Handles cleanup internally

        log.info('Multiplexer async main finished.')


# --- Entry Point ---
def main() -> None:
    """Synchronous entry point, parses args and runs asyncio loop."""
    parser = argparse.ArgumentParser(
        description='Multiplex Jupyter kernel protocol using JSON Lines (JSONL).',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Input Format (stdin):
  One valid JSON object per line, representing a Jupyter message.
  The script routes the message based on 'header.msg_type'.

Output Format (stdout):
  JSON Lines: One JSON object per line, representing messages received
  from the kernel's 'iopub' or 'stdin' channels only.
""",
    )
    parser.add_argument(
        'kernel_name',
        help="The name of the Jupyter kernel spec to start (e.g., 'python3', 'bash').",
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging.',
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    exit_code = 0
    try:
        asyncio.run(main_async(args))
        log.info('Program finished successfully.')
    except KeyboardInterrupt:
        log.info('Program interrupted by user (Ctrl+C).')
        exit_code = 1  # Indicate interruption
    except RuntimeError as e:
        log.critical('Runtime error', exc_info=True)
        exit_code = 1  # Indicate failure
    except Exception as e:
        # Catch any other unexpected exceptions during setup or teardown
        log.critical('Fatal top-level error', exc_info=True)
        exit_code = 1  # Indicate failure
    finally:
        logging.shutdown()  # Ensure logs are flushed
        sys.exit(exit_code)


if __name__ == '__main__':
    # This allows running the script directly (python src/cg_jupyter_mux/main.py ...)
    # for development/testing, although the primary entry point should be
    # the installed script ('cg-jupyter-mux') via pyproject.toml.
    main()
