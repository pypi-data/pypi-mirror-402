from typing import Literal, Union

from phantomwright.async_api import ElementHandle, Frame, Page
from .consts import CF_INTERSTITIAL_SELECTORS, CF_TURNSTILE_SELECTORS, ChallengeType

async def detect_cloudflare_challenge(
        captcha_container: Union[Page, Frame, ElementHandle],
        challenge_type: Literal['turnstile', 'interstitial'] = 'turnstile'
) -> bool:
    """
    Detect if a Cloudflare challenge is present in the provided captcha container by checking for specific predefined selectors

    :param captcha_container: Page, Frame, ElementHandle
    :param challenge_type: Type of challenge to detect ('turnstile' or 'interstitial')

    :return: True if Cloudflare challenge is detected, False otherwise
    """

    if challenge_type not in ('turnstile', 'interstitial'):
        raise ValueError("Invalid challenge_type: it must be either 'turnstile' or 'interstitial'")

    selectors = CF_TURNSTILE_SELECTORS if challenge_type == 'turnstile' else CF_INTERSTITIAL_SELECTORS
    for selector in selectors:
        try:
            element = captcha_container.locator(selector)
            if await element.count() == 0:
                continue
        except Exception as e:
            if 'Execution context was destroyed, most likely because of a navigation' in str(e):
                # logger.warning(
                #     'Execution context was destroyed while detecting Cloudflare challenge - counting as not detected')
                return False

        return True

    return False

async def detect_cf_challenge_type(page: Page):
    async def any_selector_hit(selectors):
        for sel in selectors:
            try:
                if await page.locator(sel).count() > 0:
                    return True
            except:
                continue
        return False

    if await any_selector_hit(CF_INTERSTITIAL_SELECTORS):
        return ChallengeType.INTERSTITIAL
    if await any_selector_hit(CF_TURNSTILE_SELECTORS):
        return ChallengeType.TURNSTILE
    return None
