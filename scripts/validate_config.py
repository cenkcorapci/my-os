#!/usr/bin/env python3
"""Validate package ownership, profiles, service policy, and ISO package inputs."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MANIFEST = ROOT / "config" / "packages.json"
PROFILE_MANIFEST = ROOT / "config" / "profiles.json"
SERVICE_MANIFEST = ROOT / "config" / "services.json"
ISO_PACKAGE_LIST = ROOT / "iso" / "packages.x86_64"
MANAGERS = {"pacman", "nix", "aur", "flatpak"}
SERVICE_ACTIVATIONS = {"enabled", "disabled", "conditional"}
ARCHISO_REQUIRED_PACKAGES = {"mkinitcpio", "mkinitcpio-archiso"}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as manifest_file:
        value = json.load(manifest_file)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _iso_package_entries(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def validate_packages(
    package_manifest: dict[str, Any],
    profile_manifest: dict[str, Any],
    iso_packages: set[str],
) -> list[str]:
    errors: list[str] = []
    profiles = profile_manifest.get("profiles")
    if not isinstance(profiles, list):
        return ["profiles must be a list"]

    profile_names: set[str] = set()
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            errors.append(f"profiles[{index}] must be an object")
            continue
        name = profile.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"profiles[{index}].name must be a non-empty string")
        elif name in profile_names:
            errors.append(f"profile {name!r} is declared more than once")
        else:
            profile_names.add(name)
        if profile.get("status") not in {"implemented", "planned"}:
            errors.append(f"profiles[{index}].status must be implemented or planned")
        if not isinstance(profile.get("purpose"), str) or not profile["purpose"].strip():
            errors.append(f"profiles[{index}].purpose must be a non-empty string")

    packages = package_manifest.get("packages")
    if not isinstance(packages, list):
        return errors + ["packages must be a list"]

    names: set[str] = set()
    declared_iso_packages: set[str] = set()
    for index, package in enumerate(packages):
        label = f"packages[{index}]"
        if not isinstance(package, dict):
            errors.append(f"{label} must be an object")
            continue

        name = package.get("name")
        manager = package.get("manager")
        package_profiles = package.get("profiles")
        reason = package.get("reason")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.name must be a non-empty string")
            continue
        normalized_name = name.casefold()
        if normalized_name in names:
            errors.append(f"package {name!r} has more than one ownership entry")
        names.add(normalized_name)

        if not isinstance(manager, str) or manager not in MANAGERS:
            errors.append(f"{label}.manager must be one of {sorted(MANAGERS)}")
        if not isinstance(package_profiles, list) or not package_profiles:
            errors.append(f"{label}.profiles must be a non-empty list")
        else:
            for profile in package_profiles:
                if not isinstance(profile, str) or profile not in profile_names:
                    errors.append(f"{label} references unknown profile {profile!r}")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{label}.reason must be a non-empty string")

        in_iso = package.get("iso")
        if not isinstance(in_iso, bool):
            errors.append(f"{label}.iso must be a boolean")
        elif in_iso:
            declared_iso_packages.add(name)
            if manager != "pacman":
                errors.append(f"ISO package {name!r} must be owned by pacman")

    if declared_iso_packages != iso_packages:
        missing = sorted(declared_iso_packages - iso_packages)
        unowned = sorted(iso_packages - declared_iso_packages)
        if missing:
            errors.append(f"ISO manifest packages missing from packages.x86_64: {missing}")
        if unowned:
            errors.append(f"ISO packages lack pacman ownership entries: {unowned}")
    missing_archiso_packages = sorted(ARCHISO_REQUIRED_PACKAGES - iso_packages)
    if missing_archiso_packages:
        errors.append(f"ArchISO required packages missing from ISO: {missing_archiso_packages}")
    return errors


def validate_services(service_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = service_manifest.get("services")
    if not isinstance(services, list):
        return ["services must be a list"]

    names: set[str] = set()
    required_fields = {
        "name",
        "activation",
        "purpose",
        "listeners",
        "dependencies",
        "security_implications",
    }
    for index, service in enumerate(services):
        label = f"services[{index}]"
        if not isinstance(service, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = required_fields - service.keys()
        if missing:
            errors.append(f"{label} missing fields: {sorted(missing)}")
            continue

        name = service["name"]
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.name must be a non-empty string")
        elif name in names:
            errors.append(f"service {name!r} has more than one policy entry")
        else:
            names.add(name)
        if (
            not isinstance(service["activation"], str)
            or service["activation"] not in SERVICE_ACTIVATIONS
        ):
            errors.append(f"{label}.activation must be one of {sorted(SERVICE_ACTIVATIONS)}")
        for field in ("purpose", "security_implications"):
            if not isinstance(service[field], str) or not service[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        for field in ("listeners", "dependencies"):
            if not isinstance(service[field], list) or not all(
                isinstance(item, str) and item.strip() for item in service[field]
            ):
                errors.append(f"{label}.{field} must be a list of non-empty strings")
    return errors


def validate_repository(
    package_path: Path = PACKAGE_MANIFEST,
    profile_path: Path = PROFILE_MANIFEST,
    service_path: Path = SERVICE_MANIFEST,
    iso_package_path: Path = ISO_PACKAGE_LIST,
) -> list[str]:
    try:
        packages = _read_json(package_path)
        profiles = _read_json(profile_path)
        services = _read_json(service_path)
        iso_entries = _iso_package_entries(iso_package_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [str(error)]
    errors = []
    for name, manifest in (
        ("packages", packages),
        ("profiles", profiles),
        ("services", services),
    ):
        version = manifest.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version != 1:
            errors.append(f"{name} manifest version must be 1")
    errors.extend(validate_packages(packages, profiles, set(iso_entries)))
    duplicate_iso_entries = sorted(
        name for name, count in Counter(iso_entries).items() if count > 1
    )
    if duplicate_iso_entries:
        errors.append(f"ISO package list has duplicate entries: {duplicate_iso_entries}")
    boot_entry = ROOT / "iso" / "efiboot" / "loader" / "entries" / "01-personal-arch-linux.conf"
    loader_config = ROOT / "iso" / "efiboot" / "loader" / "loader.conf"
    network_manager_link = (
        ROOT
        / "iso"
        / "airootfs"
        / "etc"
        / "systemd"
        / "system"
        / "multi-user.target.wants"
        / "NetworkManager.service"
    )
    if not boot_entry.is_file():
        errors.append(f"UEFI systemd-boot entry is missing: {boot_entry}")
    if not loader_config.is_file():
        errors.append(f"UEFI systemd-boot loader config is missing: {loader_config}")
    autologin_config = (
        ROOT
        / "iso"
        / "airootfs"
        / "etc"
        / "systemd"
        / "system"
        / "getty@tty1.service.d"
        / "autologin.conf"
    )
    live_shadow = ROOT / "iso" / "airootfs" / "etc" / "shadow"
    if not autologin_config.is_file() or not live_shadow.is_file():
        errors.append("Local recovery-shell autologin configuration is incomplete")
    if live_shadow.is_file():
        root_entry = next(
            (
                line.split(":")
                for line in live_shadow.read_text(encoding="utf-8").splitlines()
                if line.startswith("root:")
            ),
            None,
        )
        if (
            root_entry is None
            or len(root_entry) < 9
            or not root_entry[2].isdigit()
            or int(root_entry[2]) <= 0
        ):
            errors.append("Live root account must not require a password change at autologin")
    initramfs_config = (
        ROOT / "iso" / "airootfs" / "etc" / "mkinitcpio.conf.d" / "archiso.conf"
    )
    if not initramfs_config.is_file():
        errors.append(f"ArchISO initramfs configuration is missing: {initramfs_config}")
    elif not re.search(
        r"(?m)^HOOKS=\([^)]*\barchiso\b[^)]*\)$",
        initramfs_config.read_text(encoding="utf-8"),
    ):
        errors.append("ArchISO initramfs hook must be enabled in the profile overlay")
    firstboot_mask = (
        ROOT
        / "iso"
        / "airootfs"
        / "etc"
        / "systemd"
        / "system"
        / "systemd-firstboot.service"
    )
    if not firstboot_mask.is_symlink() or str(firstboot_mask.readlink()) != "/dev/null":
        errors.append("Interactive systemd first-boot setup must be masked in the live image")
    gpt_auto_mask = (
        ROOT
        / "iso"
        / "airootfs"
        / "etc"
        / "systemd"
        / "system-generators"
        / "systemd-gpt-auto-generator"
    )
    if not gpt_auto_mask.is_symlink() or str(gpt_auto_mask.readlink()) != "/dev/null":
        errors.append("systemd GPT auto-root discovery must be masked in the live image")
    if not network_manager_link.is_symlink() or str(network_manager_link.readlink()) != (
        "/usr/lib/systemd/system/NetworkManager.service"
    ):
        errors.append("NetworkManager must be enabled by its systemd wants symlink in the ISO overlay")
    return errors + validate_services(services)


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Configuration manifests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
