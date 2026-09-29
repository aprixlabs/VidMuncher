import sys
import subprocess
from app.utils.debug import debug_print


def detect_system_gpus():
    raw_names = []

    if sys.platform == "win32":
        try:
            import winreg
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
                num_subkeys = winreg.QueryInfoKey(k)[0]
                for i in range(num_subkeys):
                    sub_key_name = winreg.EnumKey(k, i)
                    if sub_key_name.isdigit():
                        try:
                            with winreg.OpenKey(k, sub_key_name) as sub_k:
                                desc, _ = winreg.QueryValueEx(sub_k, "DriverDesc")
                                raw_names.append(desc)
                        except OSError:
                            pass
        except Exception as e:
            debug_print(f"Windows GPU detection error: {e}")

    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(
                ["lspci"],
                capture_output=True,
                text=True,
                check=True,
                timeout=3
            )
            for line in res.stdout.splitlines():
                if any(k in line.lower() for k in ["vga", "3d", "display"]):
                    raw_names.append(line)
        except Exception as e:
            debug_print(f"Linux GPU detection error: {e}")

    detected = []
    combined = " ".join(raw_names).lower()

    if "nvidia" in combined:
        detected.append("Nvidia")
    if "amd" in combined or "radeon" in combined:
        detected.append("AMD")
    if "intel" in combined:
        detected.append("Intel")

    debug_print(f"Detected GPU hardware: {detected} (raw: {raw_names})")
    return detected
