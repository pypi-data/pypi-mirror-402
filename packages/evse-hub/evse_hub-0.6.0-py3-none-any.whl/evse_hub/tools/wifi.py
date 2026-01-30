from __future__ import annotations

import subprocess

def wifi_is_associated(ifname: str = "wlan0") -> bool:
    """
    True if the kernel reports the interface is associated to an AP.
    Requires: iw
    """
    try:
        out = subprocess.check_output(
            ["iw", "dev", ifname, "link"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=1.0,
        )
    except Exception:
        return False

    return out.startswith("Connected to ")
