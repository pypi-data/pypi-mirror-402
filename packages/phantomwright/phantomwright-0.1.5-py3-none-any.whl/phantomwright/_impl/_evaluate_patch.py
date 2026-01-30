from functools import wraps

from phantomwright_driver.async_api import Page as AsyncPage
from phantomwright_driver.async_api import Frame as AsyncFrame
from phantomwright_driver.async_api import Locator as AsyncLocator
from phantomwright_driver.async_api import Worker as AsyncWorker
from phantomwright_driver.async_api import JSHandle as AsyncJSHandle
from phantomwright_driver.sync_api import Page as SyncPage
from phantomwright_driver.sync_api import Frame as SyncFrame
from phantomwright_driver.sync_api import Locator as SyncLocator
from phantomwright_driver.sync_api import Worker as SyncWorker
from phantomwright_driver.sync_api import JSHandle as SyncJSHandle


def _patch_sync_evaluate(cls, method_name: str) -> None:
    """Patch a sync evaluate method to default isolated_context to False."""
    original = getattr(cls, method_name)

    @wraps(original)
    def hooked(self, *args, **kwargs):
        kwargs.setdefault("isolated_context", False)
        return original(self, *args, **kwargs)

    setattr(cls, method_name, hooked)


def _patch_async_evaluate(cls, method_name: str) -> None:
    """Patch an async evaluate method to default isolated_context to False."""
    original = getattr(cls, method_name)

    @wraps(original)
    async def hooked(self, *args, **kwargs):
        kwargs.setdefault("isolated_context", False)
        return await original(self, *args, **kwargs)

    setattr(cls, method_name, hooked)


def do_patch() -> None:
    """Async / Sync version of evaluate override for Page, Frame, Locator, Worker, JSHandle."""
    # Sync patches
    _patch_sync_evaluate(SyncPage, "evaluate")
    _patch_sync_evaluate(SyncPage, "evaluate_handle")
    _patch_sync_evaluate(SyncFrame, "evaluate")
    _patch_sync_evaluate(SyncFrame, "evaluate_handle")
    _patch_sync_evaluate(SyncLocator, "evaluate")
    _patch_sync_evaluate(SyncLocator, "evaluate_handle")
    _patch_sync_evaluate(SyncWorker, "evaluate")
    _patch_sync_evaluate(SyncWorker, "evaluate_handle")
    _patch_sync_evaluate(SyncJSHandle, "evaluate")
    _patch_sync_evaluate(SyncJSHandle, "evaluate_handle")

    # Async patches
    _patch_async_evaluate(AsyncPage, "evaluate")
    _patch_async_evaluate(AsyncPage, "evaluate_handle")
    _patch_async_evaluate(AsyncFrame, "evaluate")
    _patch_async_evaluate(AsyncFrame, "evaluate_handle")
    _patch_async_evaluate(AsyncLocator, "evaluate")
    _patch_async_evaluate(AsyncLocator, "evaluate_handle")
    _patch_async_evaluate(AsyncWorker, "evaluate")
    _patch_async_evaluate(AsyncWorker, "evaluate_handle")
    _patch_async_evaluate(AsyncJSHandle, "evaluate")
    _patch_async_evaluate(AsyncJSHandle, "evaluate_handle")
