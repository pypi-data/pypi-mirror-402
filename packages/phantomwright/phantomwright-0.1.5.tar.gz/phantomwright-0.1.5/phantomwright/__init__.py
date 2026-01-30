"""
Patchright + Stealth Plugin + User Behavior Simulation + Cloudflare Captcha Solver = PhantomWright
"""

from ._impl import _core_debug_patch, _evaluate_patch, _inconsistency_patch

_evaluate_patch.do_patch()
_core_debug_patch.do_patch()
_inconsistency_patch.do_patch()