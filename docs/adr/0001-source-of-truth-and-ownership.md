# ADR 0001: Declarative ownership manifests

- Status: Accepted
- Date: 2026-11-25

## Context

The workstation will use pacman, Nix, AUR and Flatpak. Independently declaring
the same application in several provisioning layers makes upgrades and removal
ambiguous. Services also need explicit defaults, listeners and security
implications so that optional developer tools do not silently become
always-on services.

## Decision

Track package ownership in `config/packages.json`, profiles in
`config/profiles.json`, and intended service policy in `config/services.json`.
Each package has exactly one owner; ISO packages are pacman-owned and must
match `iso/packages.x86_64`. Provisioning layers must consume these manifests.
The standard-library validator and unit tests enforce the current data
invariants without introducing a runtime dependency.

## Consequences

- Package and service changes are reviewable independently from provisioning.
- New package managers or profile fields require updating the validator and
  tests.
- ArchISO's required initramfs packages and UEFI boot configuration are checked
  alongside package ownership to catch incomplete live-image profiles early.
- The manifests currently describe only the minimal live environment and
  planned service policy; they do not yet configure installed systems.
- This is a source-of-truth convention, not a claim that the full package set
  has been resolved or tested against a pinned Arch snapshot.
