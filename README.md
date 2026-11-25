# Personal Arch

A network-first Arch Linux workstation project. This repository is being built
incrementally; it is **not yet a complete installer or a validated workstation
release**.

## Phase-one foundation

The current UEFI systemd-boot ArchISO boots to a local root shell with
NetworkManager, C++ tools, and the CUDA toolkit (`nvcc`). It does not install
Personal Arch to a disk or configure a desktop. The live console is
intentionally unauthenticated, as with standard Arch installation media, and
should only be booted where physical access is controlled.

The package manifest is the source of truth for package ownership. A package
must have one manager (`pacman`, `nix`, `aur`, or `flatpak`); packages included
in the ISO are also listed in `iso/packages.x86_64`. The service manifest
records intended activation, listeners, dependencies, and security impact.
Future provisioning must consume these manifests rather than independently
declaring ownership or service defaults.

## Requirements and commands

Use an x86_64 Arch Linux build host with `archiso` and Python 3. `qemu-system-x86`
and `edk2-ovmf` are needed to boot the resulting image in UEFI mode. On macOS,
install QEMU with `brew install qemu`; Homebrew QEMU does not bundle OVMF, so
use an existing OVMF/EDK2 code and variable firmware pair with `UEFI_CODE` and
`UEFI_VARS`.

```sh
make help
make doctor
make lint
make test
sudo make build
make boot ISO=/absolute/path/to/candidate.iso
make vm
```

`make build` creates an unpublished candidate under `dist/candidate/` and keeps
its working directory under `dist/work/`. Builds are serialized. `make boot`
requires an explicit ISO path and uses QEMU with UEFI firmware; it does not
perform an unattended install. `make vm` selects the newest candidate ISO by
default and allocates 8 GiB RAM and 4 CPUs; override with `ISO=PATH`,
`VM_RAM=MiB`, and `VM_CPUS=N`. For example:

```sh
make vm ISO=/path/to/candidate.iso VM_RAM=6144 VM_CPUS=4 \
  UEFI_CODE=/path/to/OVMF_CODE.fd UEFI_VARS=/path/to/OVMF_VARS.fd
```

On Apple Silicon, the x86_64 VM runs under software emulation and is slower
than native execution. The CUDA toolkit enables CUDA code compilation, but
this VM does not provide GPU passthrough; executing kernels requires compatible
NVIDIA hardware and a matching driver. The live root filesystem is ephemeral,
so changes made inside the VM are lost when it shuts down. `make toolchain-check`
compiles and runs a small C++ program and compiles a CUDA kernel without running
it; run it from a checkout inside the live environment.

The CUDA package adds about 2.7 GB compressed and 5.4 GB installed; the hosted
candidate ISO is about 4.6 GB, substantially larger than a recovery-only image.

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
- No desktop, NVIDIA kernel-driver selection, Nix/Home Manager, Ansible roles,
  or user workstation CLI yet.
- No validated Arch snapshot, release promotion, USB writer, or claim of
  reproducible/atomic system rollback.
- The expanded C++/CUDA candidate built, passed compiler smoke checks, and
  booted in UEFI QEMU. Manual network/listener checks, physical hardware
  testing, and performance measurements remain outstanding.

See the [architecture decisions](docs/adr/) and
[implementation roadmap](docs/implementation-roadmap.md) before extending
package ownership, service policy, or release behavior.
