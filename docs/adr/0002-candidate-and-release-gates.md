# ADR 0002: Separate ISO candidates from validated releases

- Status: Accepted
- Date: 2026-11-25

## Context

The primary `make create` command is required to resolve a coherent package
snapshot, build in isolation, install and test in UEFI QEMU, verify system
security and development behavior, record evidence, and promote atomically.
The repository does not yet implement those gates. Treating a bare `mkarchiso`
build as a release would overstate what has been validated.

## Decision

Expose `make build` for an unpublished candidate and `make boot ISO=...` for a
manual UEFI QEMU boot. Candidate directories are unique and builds are
serialized. Do not implement `make create` as an alias, and do not introduce a
stable pointer until all mandatory gates and a release manifest exist.
The ArchISO profile uses the documented `uefi.systemd-boot` mode and includes
the mandatory `mkinitcpio` and `mkinitcpio-archiso` packages.
Its layout and boot-profile fields follow the
[ArchISO profile documentation](https://gitlab.archlinux.org/archlinux/archiso/-/blob/master/docs/README.profile.rst);
no dotfiles, screenshots, or other project assets have been copied.

## Consequences

- A candidate is useful for developing the live environment but is not a
  validated install artifact.
- Build host availability and VM boot do not substitute for integration or
  physical hardware testing.
- The future release pipeline must implement snapshot retention, fresh test
  evidence, artifact hash matching, atomic promotion and prior-release
  preservation before exposing `make create`.
