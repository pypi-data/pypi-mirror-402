"""Monkey patch to add warnings to add_init_script API.

This module patches the Playwright classes to emit warnings when add_init_script is called,
alerting users that this API has some behavioral differences from the original Playwright.
"""

import functools
import warnings

from phantomwright_driver.async_api import (
    BrowserContext as AsyncBrowserContext,
    Page as AsyncPage,
)
from phantomwright_driver.sync_api import (
    BrowserContext as SyncBrowserContext,
    Page as SyncPage,
)

_WARNING_MESSAGE = (
    "phantomwright.add_init_script doesn't fully align with playwright.add_init_script. "
    "Key differences:\n"
    "1. Cannot call exposed bindings: Init scripts execute before bindings from "
    "expose_function/expose_binding are available.\n"
    "2. Does not affect special URLs: Scripts won't run on about:blank, data: URIs, "
    "or file:// URLs because patchright uses routing-based injection."
)


def _wrap_with_warning(original_method, is_async=False):
    """Wrap a method to emit a warning before calling the original."""
    if is_async:
        @functools.wraps(original_method)
        async def wrapper(self, *args, **kwargs):
            warnings.warn(_WARNING_MESSAGE, UserWarning, stacklevel=2)
            return await original_method(self, *args, **kwargs)
    else:
        @functools.wraps(original_method)
        def wrapper(self, *args, **kwargs):
            warnings.warn(_WARNING_MESSAGE, UserWarning, stacklevel=2)
            return original_method(self, *args, **kwargs)
    return wrapper


def _apply_patches():
    """Apply monkey patches to Playwright classes."""
    # Patch async API
    AsyncBrowserContext.add_init_script = _wrap_with_warning(
        AsyncBrowserContext.add_init_script, is_async=True
    )
    AsyncPage.add_init_script = _wrap_with_warning(
        AsyncPage.add_init_script, is_async=True
    )

    # Patch sync API
    SyncBrowserContext.add_init_script = _wrap_with_warning(
        SyncBrowserContext.add_init_script, is_async=False
    )
    SyncPage.add_init_script = _wrap_with_warning(
        SyncPage.add_init_script, is_async=False
    )


def do_patch():
    """Apply monkey patches to Playwright classes."""
    _apply_patches()
