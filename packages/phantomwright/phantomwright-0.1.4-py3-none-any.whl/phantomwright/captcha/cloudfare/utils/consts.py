from enum import Enum

CF_INTERSTITIAL_SELECTORS = [
    'script[src*="/cdn-cgi/challenge-platform/"]',
]

CF_TURNSTILE_SELECTORS = [
    'input[name="cf-turnstile-response"]',
    'script[src*="challenges.cloudflare.com/turnstile/v0"]',
]

ALL_CF_SELECTORS = CF_INTERSTITIAL_SELECTORS + CF_TURNSTILE_SELECTORS

class ChallengeType(Enum):
    INTERSTITIAL = "interstitial"
    TURNSTILE = "turnstile"
