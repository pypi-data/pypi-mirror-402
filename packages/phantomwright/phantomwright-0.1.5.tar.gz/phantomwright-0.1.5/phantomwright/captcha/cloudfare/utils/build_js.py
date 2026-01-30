import json
from pathlib import Path

from .consts import ALL_CF_SELECTORS

observer_js = Path(__file__).parent.parent.joinpath("scripts", "observer.js").read_text(encoding="utf-8").replace("__CF_SELECTORS__", json.dumps(ALL_CF_SELECTORS))
shadow_root_js = Path(__file__).parent.parent.joinpath("scripts", "shadow_root.js").read_text(encoding="utf-8")