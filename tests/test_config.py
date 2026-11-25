from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.boot_iso import find_uefi_firmware
from scripts.validate_config import (
    ARCHISO_REQUIRED_PACKAGES,
    ROOT,
    validate_packages,
    validate_repository,
    validate_services,
)


class BootIsoTests(unittest.TestCase):
    def test_selects_first_complete_firmware_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            code = root / "OVMF_CODE.fd"
            variables = root / "OVMF_VARS.fd"
            code.touch()
            variables.touch()
            later_code = root / "later_CODE.fd"
            later_variables = root / "later_VARS.fd"
            later_code.touch()
            later_variables.touch()
            with patch(
                "scripts.boot_iso.FIRMWARE_PAIRS",
                ((code, variables), (later_code, later_variables)),
            ):
                self.assertEqual(find_uefi_firmware(), (code, variables))

    def test_ignores_incomplete_firmware_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            code = Path(temp_dir) / "OVMF_CODE.fd"
            code.touch()
            with patch("scripts.boot_iso.FIRMWARE_PAIRS", ((code, code.with_name("missing.fd")),)):
                self.assertIsNone(find_uefi_firmware())


class ConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packages = json.loads((ROOT / "config/packages.json").read_text(encoding="utf-8"))
        self.profiles = json.loads((ROOT / "config/profiles.json").read_text(encoding="utf-8"))
        self.services = json.loads((ROOT / "config/services.json").read_text(encoding="utf-8"))
        self.iso_packages = {
            line.strip()
            for line in (ROOT / "iso/packages.x86_64").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

    def test_checked_in_manifests_are_consistent(self) -> None:
        self.assertEqual(validate_repository(), [])

    def test_archiso_includes_required_packages_and_uefi_boot_files(self) -> None:
        self.assertTrue(ARCHISO_REQUIRED_PACKAGES <= self.iso_packages)
        self.assertTrue((ROOT / "iso/efiboot/loader/loader.conf").is_file())
        self.assertTrue(
            (ROOT / "iso/efiboot/loader/entries/01-personal-arch-linux.conf").is_file()
        )
        network_manager_link = (
            ROOT
            / "iso/airootfs/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
        )
        self.assertTrue(network_manager_link.is_symlink())
        self.assertEqual(
            network_manager_link.readlink(),
            Path("/usr/lib/systemd/system/NetworkManager.service"),
        )
        self.assertTrue(
            (ROOT / "iso/airootfs/etc/systemd/system/getty@tty1.service.d/autologin.conf")
            .is_file()
        )
        self.assertTrue((ROOT / "iso/airootfs/etc/shadow").is_file())

    def test_package_cannot_have_multiple_owners(self) -> None:
        packages = copy.deepcopy(self.packages)
        duplicate = copy.deepcopy(packages["packages"][0])
        duplicate["manager"] = "nix"
        packages["packages"].append(duplicate)

        errors = validate_packages(packages, self.profiles, self.iso_packages)

        self.assertTrue(any("more than one ownership entry" in error for error in errors))

    def test_profile_references_must_be_declared(self) -> None:
        packages = copy.deepcopy(self.packages)
        packages["packages"][0]["profiles"] = ["missing"]

        errors = validate_packages(packages, self.profiles, self.iso_packages)

        self.assertTrue(any("unknown profile" in error for error in errors))

    def test_manifest_version_is_checked(self) -> None:
        packages = copy.deepcopy(self.packages)
        packages["version"] = 2
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "packages.json"
            path.write_text(json.dumps(packages), encoding="utf-8")
            errors = validate_repository(package_path=path)

        self.assertTrue(any("packages manifest version must be 1" in error for error in errors))

    def test_iso_package_must_be_owned_by_pacman(self) -> None:
        packages = copy.deepcopy(self.packages)
        packages["packages"][0]["manager"] = "nix"

        errors = validate_packages(packages, self.profiles, self.iso_packages)

        self.assertTrue(any("must be owned by pacman" in error for error in errors))

    def test_service_requires_security_and_listener_metadata(self) -> None:
        services = copy.deepcopy(self.services)
        del services["services"][0]["security_implications"]

        errors = validate_services(services)

        self.assertTrue(any("missing fields" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
