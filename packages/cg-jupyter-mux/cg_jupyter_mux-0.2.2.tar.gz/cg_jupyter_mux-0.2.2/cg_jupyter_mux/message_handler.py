import asyncio
import datetime
import json
import logging
import queue
import typing as t

from jupyter_client import AsyncKernelClient, AsyncKernelManager

from .config import MSG_TYPE_TO_SHELL

log = logging.getLogger(__name__)


def _json_default(obj: object) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


async def handle_kernel_output(
    channel_name: t.Literal['iopub', 'stdin', 'shell'],
    client: AsyncKernelClient,
    writer: asyncio.StreamWriter,
    shutdown_event: asyncio.Event,
) -> None:
    """Task to read messages from a kernel channel and write them to stdout as JSONL."""
    log.info(f'Starting listener for kernel output channel: {channel_name}')
    if channel_name == 'iopub':
        get_msg_func = client.get_iopub_msg
    elif channel_name == 'stdin':
        get_msg_func = client.get_stdin_msg
    elif channel_name == 'shell':
        get_msg_func = client.get_shell_msg
    else:
        raise Exception(
            f'Invalid channel name provided to output listener: {channel_name}'
        )

    try:
        while await client.is_alive():
            try:
                msg = await get_msg_func(timeout=1)
            except queue.Empty:
                continue

            output_line = json.dumps(msg, default=_json_default).encode('utf8')
            writer.write(output_line)
            writer.write(b'\n')
            await writer.drain()
            log.debug(
                'OUT (%s): %s',
                channel_name,
                msg.get('header', {}).get('msg_type', 'unknown'),
            )
    except asyncio.CancelledError:
        log.info(
            'Listener task for kernel output channel %s cancelled.',
            channel_name,
        )
        raise
    finally:
        log.info(
            'Stopping listener for kernel output channel: %s',
            channel_name,
        )
        shutdown_event.set()


async def _handle_single_stdin_line(
    client: AsyncKernelClient,
    km: AsyncKernelManager,
    line: bytes,
) -> None:
    log.debug('IN: %.150s...', line)
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        log.error(
            'Failed to decode JSON from stdin line: %.100s...',
            line,
        )
        return

    if not isinstance(msg, dict):
        log.warning(
            f'Received non-dict JSON object from stdin, skipping: %s',
            type(msg),
        )
        return

    msg_type = msg.get('header', {}).get('msg_type')
    if not msg_type:
        log.warning(
            "Received message without 'msg_type' in header, cannot route: %.100s...",
            line,
        )
        return

    if msg_type == 'interrupt_request':
        log.info("Received 'interrupt_request', interrupting kernel")
        await km.interrupt_kernel()
        return

    target_is_shell = MSG_TYPE_TO_SHELL.get(msg_type)

    if target_is_shell is None:
        log.warning(
            "Unknown or unroutable 'msg_type' received: '%s'. No target channel configured.",
            msg_type,
        )
        return

    if target_is_shell:
        kernel_channel = client.shell_channel
    else:
        kernel_channel = client.stdin_channel

    kernel_channel.send(msg)
    log.debug(
        "Routed '%s' to kernel '%s' channel.",
        msg_type,
        'shell' if target_is_shell else 'stdin',
    )


async def handle_stdin_input(
    reader: asyncio.StreamReader,
    client: AsyncKernelClient,
    km: AsyncKernelManager,
    shutdown_event: asyncio.Event,
) -> None:
    """Task to read JSONL messages from stdin and route them to the correct kernel channel."""
    log.info('Starting listener for stdin (JSONL format)')
    try:
        while not reader.at_eof():
            line = await reader.readline()
            if not line:
                break

            await _handle_single_stdin_line(client, km, line)

    except asyncio.CancelledError:
        log.info('Stdin listener task cancelled.')
        raise
    finally:
        log.info('Stdin closed, initiating shutdown...')
        shutdown_event.set()
