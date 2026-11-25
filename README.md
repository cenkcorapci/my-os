# Personal Arch

A network-first Arch Linux workstation project. This repository is being built
incrementally; it is **not yet a complete installer or a validated workstation
release**.

## Phase-one foundation

The initial implementation establishes a small UEFI systemd-boot ArchISO
profile, a package ownership manifest, a system-service policy manifest, and
repeatable local checks. The live image is intended to boot to a
local root recovery shell with NetworkManager enabled and no SSH server; it
does not yet install Personal Arch to a disk or configure a desktop. The live
console is intentionally unauthenticated, as with standard Arch installation
media, and should only be booted where physical access is controlled.

The package manifest is the source of truth for package ownership. A package
must have one manager (`pacman`, `nix`, `aur`, or `flatpak`); packages included
in the ISO are also listed in `iso/packages.x86_64`. The service manifest
records intended activation, listeners, dependencies, and security impact.
Future provisioning must consume these manifests rather than independently
declaring ownership or service defaults.

## Requirements and commands

Use an x86_64 Arch Linux build host with `archiso` and Python 3. `qemu-system-x86`
and `edk2-ovmf` are needed to boot the resulting image in UEFI mode.

```sh
make help
make doctor
make lint
make test
sudo make build
make boot ISO=/absolute/path/to/candidate.iso
```

`make build` creates an unpublished candidate under `dist/candidate/` and keeps
its working directory under `dist/work/`. Builds are serialized. `make boot`
requires an explicit ISO path and uses QEMU with UEFI firmware; it does not
perform an unattended install. Run checks without ArchISO/QEMU using
`make lint test`.

Follow the [integration testing procedure](docs/integration-testing.md) to
build, boot, and record evidence for a candidate ISO. A successful build alone
is not a validated release.

GitHub Actions runs the same lint and unit-test commands on pushes and pull
requests. The manually triggered **ISO candidate integration** workflow builds
with ArchISO, runs a UEFI QEMU boot smoke test, and uploads a short-lived
candidate artifact. It is not a release or installer validation.

The required `make create` release command is deliberately not implemented as
an alias for image creation: promotion must wait for the full mandatory
integration gates and immutable release-manifest workflow described in
[`docs/implementation-roadmap.md`](docs/implementation-roadmap.md).

## Current limitations

- No disk installer, partitioning, encryption, or destructive storage code.
- No desktop, hardware-driver selection, Nix/Home Manager, Ansible roles, or
  user workstation CLI yet.
- No validated Arch snapshot, release promotion, USB writer, or claim of
  reproducible/atomic system rollback.
- The candidate ISO has booted to the recovery shell in UEFI QEMU. Network and
  listener checks from the integration procedure, physical hardware testing,
  and performance measurements are still outstanding.

See the [architecture decisions](docs/adr/) and
[implementation roadmap](docs/implementation-roadmap.md) before extending
package ownership, service policy, or release behavior.
