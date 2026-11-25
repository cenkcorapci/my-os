#!/usr/bin/env python3
"""Boot an explicitly selected ISO in a disposable UEFI QEMU virtual machine."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


FIRMWARE_PAIRS = (
    (
        Path("/usr/share/edk2/x64/OVMF_CODE.4m.fd"),
        Path("/usr/share/edk2/x64/OVMF_VARS.4m.fd"),
    ),
    (
        Path("/usr/share/OVMF/OVMF_CODE_4M.fd"),
        Path("/usr/share/OVMF/OVMF_VARS_4M.fd"),
    ),
    (
        Path("/usr/share/OVMF/OVMF_CODE.fd"),
        Path("/usr/share/OVMF/OVMF_VARS.fd"),
    ),
)


def find_uefi_firmware(
    code_path: Path | None = None,
    variables_path: Path | None = None,
) -> tuple[Path, Path] | None:
    if code_path is not None or variables_path is not None:
        if code_path is not None and variables_path is not None:
            if code_path.is_file() and variables_path.is_file():
                return code_path, variables_path
        return None
    return next(
        ((code, variables) for code, variables in FIRMWARE_PAIRS if code.is_file() and variables.is_file()),
        None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO image to boot")
    parser.add_argument("--memory-mib", type=int, default=4096, help="VM RAM in MiB (default: 4096)")
    parser.add_argument("--cpus", type=int, default=2, help="Number of guest CPUs (default: 2)")
    parser.add_argument("--uefi-code", type=Path, help="OVMF code firmware file")
    parser.add_argument("--uefi-vars", type=Path, help="OVMF variables firmware file")
    args = parser.parse_args()
    if args.memory_mib < 1:
        parser.error("--memory-mib must be a positive integer")
    if args.cpus < 1:
        parser.error("--cpus must be a positive integer")
    if (args.uefi_code is None) != (args.uefi_vars is None):
        parser.error("--uefi-code and --uefi-vars must be provided together")

    iso = Path(args.iso).expanduser().resolve()
    if not iso.is_file():
        parser.error(f"ISO does not exist: {iso}")

    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        print("ERROR: qemu-system-x86_64 not found.", file=sys.stderr)
        return 1
    firmware = find_uefi_firmware(
        args.uefi_code.expanduser() if args.uefi_code else None,
        args.uefi_vars.expanduser() if args.uefi_vars else None,
    )
    if firmware is None:
        print(
            "ERROR: UEFI OVMF firmware not found. Install edk2-ovmf or pass "
            "--uefi-code and --uefi-vars.",
            file=sys.stderr,
        )
        return 1

    code, variables = firmware
    with tempfile.TemporaryDirectory(prefix="personal-arch-uefi-") as temp_dir:
        vars_copy = Path(temp_dir) / "OVMF_VARS.fd"
        shutil.copyfile(variables, vars_copy)
        command = [
            qemu,
            "-machine",
            "q35",
            "-m",
            str(args.memory_mib),
            "-smp",
            str(args.cpus),
            "-drive",
            f"if=pflash,format=raw,readonly=on,file={code}",
            "-drive",
            f"if=pflash,format=raw,file={vars_copy}",
            "-drive",
            f"file={iso},media=cdrom,readonly=on",
            "-boot",
            "order=d",
            "-nic",
            "user,model=virtio-net-pci",
        ]
        if Path("/dev/kvm").exists():
            command[1:1] = ["-enable-kvm"]
        print(f"Booting {iso} with disposable UEFI variables.")
        if sys.platform == "darwin" and platform.machine() == "arm64":
            print(
                "NOTE: x86_64 runs under software emulation on Apple Silicon; "
                "CUDA GPU execution is unavailable in this VM."
            )
        return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
