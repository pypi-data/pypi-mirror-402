import subprocess
from pathlib import Path
import os

def run_mass(
    input_file,
    output_file,
    dim=2,
    method=3,
    n_x=300,
    k_type_x=1,
    b_x_ratio=1.0,
    n_y=300,
    k_type_y=1,
    b_y_ratio=1.0
):
    pkg_dir = Path(__file__).parent
    exe_dir = pkg_dir / "bin"
    dll_dir = pkg_dir / "bin_dll"

    exe_path = exe_dir / "mass_pkdv.exe"

    if not exe_path.exists():
        raise FileNotFoundError(f"Executable not found: {exe_path}")

    os.environ["PATH"] = str(dll_dir) + ";" + os.environ.get("PATH", "")

    cmd = [
        str(exe_path),
        str(input_file),
        str(output_file),
        str(dim),
        str(method),
        str(n_x),
        str(k_type_x),
        str(b_x_ratio),
        str(n_y),
        str(k_type_y),
        str(b_y_ratio),
    ]

    subprocess.run(cmd, check=True)
