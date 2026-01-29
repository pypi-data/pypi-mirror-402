import asyncio
import logging

from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import NoSuchKernel, find_kernel_specs

log = logging.getLogger(__name__)


async def start_kernel(kernel_name: str) -> AsyncKernelManager:
    """
    Starts a Jupyter kernel and returns the KernelManager instance.
    Raises exceptions on failure.
    """
    log.info("Attempting to start kernel: '%s'", kernel_name)
    km = AsyncKernelManager(kernel_name=kernel_name)
    try:
        await km.start_kernel()
        log.info(f"Kernel '%s' started successfully.", kernel_name)
        log.info(f'Connection file: %s', km.connection_file)
        # Perform a quick check if the kernel process is alive after start
        if not await km.is_alive():
            raise RuntimeError(
                f"Kernel '{kernel_name}' failed to stay alive after startup."
            )
    except NoSuchKernel:
        log.error("Error: Kernel spec '%s' not found!", kernel_name)
        try:
            specs = find_kernel_specs()
            log.info('Available kernel specs: %s', list(specs.keys()))
        except Exception as spec_e:  # pragma: no cover
            log.error('Could not list available kernel specs: %s', spec_e)
        raise
    except Exception as e:
        # Clean up potentially partially started kernel resources
        try:
            if km.has_kernel:
                await km.shutdown_kernel(now=True)
            await km.cleanup_resources()
        except Exception:
            log.warning(
                'Error during cleanup after failed kernel start',
                exc_info=True,
            )
        raise RuntimeError(f"Failed to start kernel '{kernel_name}'") from e
    else:
        return km


async def shutdown_kernel(km: AsyncKernelManager) -> None:
    """
    Shuts down the Jupyter kernel managed by the KernelManager.
    """
    if not km:
        log.warning('Shutdown called but KernelManager is None.')
        return

    kernel_id = getattr(km, 'kernel_id', 'unknown')
    log.debug('Initiating shutdown for kernel %s...', kernel_id)

    try:
        is_alive = await km.is_alive()
        if is_alive:
            log.info('Shutting down kernel process %s...', kernel_id)
            await km.shutdown_kernel(now=True)
            log.info('Kernel %s shutdown request sent.', kernel_id)
            # Give the kernel some time to actually shutdown
            await asyncio.sleep(0.1)
        else:
            log.info('Kernel process %s was already stopped.', kernel_id)
    except Exception:
        log.error(
            'Failed to shutdown kernel %s',
            kernel_id,
            exc_info=True,
        )

    # Always attempt resource cleanup (like connection file removal)
    log.debug('Cleaning up resources for kernel %s...', kernel_id)
    try:
        await km.cleanup_resources()
        log.debug('Resources cleaned up for kernel %s.', kernel_id)
    except Exception:
        log.warning(
            'Error cleaning up kernel manager resources for %s',
            kernel_id,
            exc_info=True,
        )
