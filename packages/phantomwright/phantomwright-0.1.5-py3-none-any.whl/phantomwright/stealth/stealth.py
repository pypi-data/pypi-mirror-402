# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Any, Dict, Union, Tuple, Optional, TypedDict
import warnings

from phantomwright_driver import async_api, sync_api


def from_file(name) -> str:
    return (Path(__file__).parent / "js" / name).read_text()


SCRIPTS: Dict[str, str] = {
    "generate_magic_arrays": from_file("generate.magic.arrays.js"),
    "utils": from_file("utils.js"),
    "chrome_app": from_file("evasions/chrome.app.js"),
    "chrome_csi": from_file("evasions/chrome.csi.js"),
    "chrome_hairline": from_file("evasions/chrome.hairline.js"),
    "chrome_load_times": from_file("evasions/chrome.load.times.js"),
    "chrome_runtime": from_file("evasions/chrome.runtime.js"),
    "iframe_content_window": from_file("evasions/iframe.contentWindow.js"),
    "media_codecs": from_file("evasions/media.codecs.js"),
    "navigator_hardware_concurrency": from_file("evasions/navigator.hardwareConcurrency.js"),
    "navigator_languages": from_file("evasions/navigator.languages.js"),
    "navigator_permissions": from_file("evasions/navigator.permissions.js"),
    "navigator_platform": from_file("evasions/navigator.platform.js"),
    "navigator_plugins": from_file("evasions/navigator.plugins.js"),
    "navigator_user_agent": from_file("evasions/navigator.userAgent.js"),
    "navigator_vendor": from_file("evasions/navigator.vendor.js"),
    "error_prototype": from_file("evasions/error.prototype.js"),
    "webgl_vendor": from_file("evasions/webgl.vendor.js"),
}


class Stealth:
    """
    Playwright stealth configuration that applies stealth strategies to Playwright.
    The stealth strategies are contained in ./js package and are basic javascript scripts that are executed
    on every page.goto() called.
    Note:
        All init scripts are combined by playwright into one script and then executed this means
        the scripts should not have conflicting constants/variables etc. !
        This also means scripts can be extended by overriding enabled_scripts generator:
        ```
        @property
        def enabled_scripts():
            yield 'console.log("first script")'
            yield from super().enabled_scripts()
            yield 'console.log("last script")'
        ```
    """

    _USER_AGENT_OVERRIDE_PIGGYBACK_KEY = "_stealth_user_agent"
    _SEC_CH_UA_OVERRIDE_PIGGYBACK_KEY = "_stealth_sec_ch_ua"

    def __init__(
        self,
        *,
        chrome_app: bool = True,
        chrome_csi: bool = True,
        chrome_load_times: bool = True,
        chrome_runtime: bool = False,
        hairline: bool = True,
        iframe_content_window: bool = True,
        media_codecs: bool = True,
        navigator_hardware_concurrency: bool = True,
        navigator_languages: bool = True,
        navigator_permissions: bool = True,
        navigator_platform: bool = True,
        navigator_plugins: bool = True,
        navigator_user_agent: bool = True,
        navigator_vendor: bool = True,
        error_prototype: bool = True,
        sec_ch_ua: bool = True,
        webgl_vendor: bool = True,
        navigator_languages_override: Tuple[str, str] = ("en-US", "en"),
        navigator_platform_override: str = "Win32",
        navigator_user_agent_override: Optional[str] = None,
        navigator_vendor_override: str = None,
        sec_ch_ua_override: Optional[str] = None,
        webgl_renderer_override: str = None,
        webgl_vendor_override: str = None,
        script_logging: bool = False,
    ):
        # scripts to load
        self.chrome_app: bool = chrome_app
        self.chrome_csi: bool = chrome_csi
        self.chrome_load_times: bool = chrome_load_times
        self.chrome_runtime: bool = chrome_runtime
        self.hairline: bool = hairline
        self.iframe_content_window: bool = iframe_content_window
        self.media_codecs: bool = media_codecs
        self.navigator_hardware_concurrency: int = navigator_hardware_concurrency
        self.navigator_languages: bool = navigator_languages
        self.navigator_permissions: bool = navigator_permissions
        self.navigator_platform: bool = navigator_platform
        self.navigator_plugins: bool = navigator_plugins
        self.navigator_user_agent: bool = navigator_user_agent
        self.navigator_vendor: bool = navigator_vendor
        self.error_prototype: bool = error_prototype
        self.sec_ch_ua: bool = sec_ch_ua
        self.webgl_vendor: bool = webgl_vendor

        # evasion options
        self.navigator_languages_override: Tuple[str, str] = navigator_languages_override or ("en-US", "en")
        self.navigator_platform_override: Optional[str] = navigator_platform_override
        self.navigator_user_agent_override: Optional[str] = navigator_user_agent_override
        self.navigator_vendor_override: str = navigator_vendor_override or None
        if sec_ch_ua_override is None and self.navigator_user_agent_override is not None:
            # we can get sec_ch_ua override for "free" here if we can parse the Chrome version string
            self.sec_ch_ua_override = self._get_greased_chrome_sec_ua_ch(self.navigator_user_agent_override)
        else:
            self.sec_ch_ua_override: Optional[str] = sec_ch_ua_override
        self.webgl_renderer_override: str = webgl_renderer_override or "Intel Iris OpenGL Engine"
        self.webgl_vendor_override: str = webgl_vendor_override or "Intel Inc."
        # other options
        self.script_logging = script_logging

    @property
    def script_payload(self) -> str:
        """
        Generates an immediately invoked function expression for all enabled scripts
        Returns: string of enabled scripts in IIFE
        """
        scripts_block = "\n".join(self.enabled_scripts)
        if len(scripts_block) == 0:
            return ""
        return "(() => {\n" + scripts_block + "\n})();"

    @property
    def options_payload(self) -> str:
        opts = {
            "navigator_hardware_concurrency": self.navigator_hardware_concurrency,
            "navigator_languages_override": self.navigator_languages_override,
            "navigator_platform": self.navigator_platform_override,
            "navigator_user_agent": self.navigator_user_agent_override,
            "navigator_vendor": self.navigator_vendor_override,
            "webgl_renderer": self.webgl_renderer_override,
            "webgl_vendor": self.webgl_vendor_override,
            "script_logging": self.script_logging,
        }
        return f"const opts = {json.dumps(opts)};"

    @property
    def enabled_scripts(self):
        evasion_script_block = "\n".join(self._evasion_scripts)
        if len(evasion_script_block) == 0:
            return ""

        yield self.options_payload
        yield SCRIPTS["utils"]
        yield SCRIPTS["generate_magic_arrays"]
        yield evasion_script_block

    @property
    def _evasion_scripts(self) -> str:
        if self.chrome_app:
            yield SCRIPTS["chrome_app"]
        if self.chrome_csi:
            yield SCRIPTS["chrome_csi"]
        if self.hairline:
            yield SCRIPTS["chrome_hairline"]
        if self.chrome_load_times:
            yield SCRIPTS["chrome_load_times"]
        if self.chrome_runtime:
            yield SCRIPTS["chrome_runtime"]
        if self.iframe_content_window:
            yield SCRIPTS["iframe_content_window"]
        if self.media_codecs:
            yield SCRIPTS["media_codecs"]
        if self.navigator_languages:
            yield SCRIPTS["navigator_languages"]
        if self.navigator_permissions:
            yield SCRIPTS["navigator_permissions"]
        if self.navigator_platform:
            yield SCRIPTS["navigator_platform"]
        if self.navigator_plugins:
            yield SCRIPTS["navigator_plugins"]
        if self.navigator_user_agent:
            yield SCRIPTS["navigator_user_agent"]
        if self.navigator_vendor:
            yield SCRIPTS["navigator_vendor"]
        if self.error_prototype:
            yield SCRIPTS["error_prototype"]
        if self.webgl_vendor:
            yield SCRIPTS["webgl_vendor"]

    async def apply_stealth_async(self, page_or_context: Union[async_api.Page, async_api.BrowserContext]) -> None:
        if len(self.script_payload) > 0:
            await page_or_context.add_init_script(self.script_payload)

    def apply_stealth_sync(self, page_or_context: Union[sync_api.Page, sync_api.BrowserContext]) -> None:
        if len(self.script_payload) > 0:
            page_or_context.add_init_script(self.script_payload)


class AllEvasionsDisabledKwargs(TypedDict):
    chrome_app: bool
    chrome_csi: bool
    chrome_load_times: bool
    chrome_runtime: bool
    hairline: bool
    iframe_content_window: bool
    media_codecs: bool
    navigator_hardware_concurrency: bool
    navigator_languages: bool
    navigator_permissions: bool
    navigator_platform: bool
    navigator_plugins: bool
    navigator_user_agent: bool
    navigator_vendor: bool
    error_prototype: bool
    sec_ch_ua: bool
    webgl_vendor: bool


ALL_EVASIONS_DISABLED_KWARGS: AllEvasionsDisabledKwargs = {
    "chrome_app": False,
    "chrome_csi": False,
    "chrome_load_times": False,
    "chrome_runtime": False,
    "hairline": False,
    "iframe_content_window": False,
    "media_codecs": False,
    "navigator_hardware_concurrency": False,
    "navigator_languages": False,
    "navigator_permissions": False,
    "navigator_platform": False,
    "navigator_plugins": False,
    "navigator_user_agent": False,
    "navigator_vendor": False,
    "error_prototype": False,
    "sec_ch_ua": False,
    "webgl_vendor": False,
}
