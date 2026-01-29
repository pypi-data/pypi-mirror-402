import os

import phantomwright_driver._impl._transport as t

_patched = False


def do_patch() -> None:
    """
    Automatically enable Node.js debug mode if PHANTOMWRIGHT_DEBUG environment variable is set.

    Environment variables:
        PHANTOMWRIGHT_DEBUG: Set to "1" or "true" to enable debug mode
        PHANTOMWRIGHT_DEBUG_HOST: Debug host and port, e.g. "9229" or "0.0.0.0:9229" (default: 9229)
        PHANTOMWRIGHT_DEBUG_BREAK: Set to "0" or "false" to disable break on start
    """
    global _patched
    if _patched:
        return

    debug_env = os.environ.get("PHANTOMWRIGHT_DEBUG", "").lower()
    if debug_env not in ("1", "true"):
        return

    host = os.environ.get("PHANTOMWRIGHT_DEBUG_HOST", "9229")
    break_on_start = os.environ.get("PHANTOMWRIGHT_DEBUG_BREAK", "1").lower() not in ("0", "false")
    inspect_flag = f"--inspect-brk={host}" if break_on_start else f"--inspect={host}"

    orig_create = t.asyncio.create_subprocess_exec

    async def patched_create(*args, **kwargs):
        args = list(args)
        args.insert(1, inspect_flag)
        print(f"[PhantomWright Debug] Launching Node with: {args}")
        return await orig_create(*args, **kwargs)

    t.asyncio.create_subprocess_exec = patched_create
    _patched = True
