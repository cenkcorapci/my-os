# Implementation roadmap

The repository started with only a short README and an MIT license; there was
no existing installer, package configuration, or workstation automation to
reuse. Implementation therefore starts with validated source-of-truth
manifests and a small live ISO profile, not a bulk copy of another dotfiles
repository. Review each phase independently and do not describe an image as
stable until it has passed its mandatory gates.

| Phase | Deliverable | Exit evidence |
|---|---|---|
| 1. Foundation (current) | Architecture decisions, profile/package/service manifests, validator, local lint/unit targets, candidate build and UEFI QEMU boot entry points, basic unprivileged CI. | Manifest tests pass; ArchISO image builds and boots in UEFI QEMU on an Arch build host. |
| 2. Network-first installer | Versioned Python TUI, network diagnostics, recovery shell, installer logging/redaction, archinstall integration where appropriate. | Network-failure tests, installer unit tests, no secret leakage in captured logs. |
| 3. Safe storage and boot | Disk inventory/exclusion, dry-run partition plan, typed confirmation, LUKS2/Btrfs/systemd-boot, optional swap and documented Secure Boot. | Destructive disk operations tested only against disposable loop devices and VM disks. |
| 4. Hardware profiles | CPU/GPU/VM detection, compatible driver selection, Bluetooth and docking behaviors. | VM coverage plus explicitly reported physical-hardware matrix. |
| 5. Desktop and daily applications | niri default, Sway fallback, Waybar/launcher/terminal, core apps, privacy and awake controls. | Functional UEFI VM session, service/listener audit, actual screenshots from the implemented VM. |
| 6. Nix, Home Manager and Ansible | Locked Nix flake, standalone Home Manager, privileged idempotent roles, ownership manifest integration. | Nix checks, Ansible idempotence, generation/rollback documentation. |
| 7. Development profiles | Scala/JVM, Python/ML, C++, Rust, quant, cloud, Kubernetes, containers and data profiles with examples. | Profile builds and functional local jobs without credentials or automatic service startup. |
| 8. Security and service policy | nftables, keyring/locking, VPN opt-in and conflict handling, threat model and security audit CLI. | Firewall/listener/service tests and secret-scanning checks. |
| 9. Release, USB, CLI and recovery | Snapshot resolver, immutable manifest, mandatory validation/promotion, safe whole-device USB writer, workstation CLI and recovery docs. | Failed gates cannot promote; USB logic tested only on disposable loop devices. |
| 10. Full validation | Integration, performance, hardware, docs, screenshots and stable release artifacts. | Published test outcomes, measurements, limitations and known-good release. |

## Phase-one boundaries

- `make build` produces only an unpublished ISO candidate. It does not update
  Arch packages, resolve or pin a repository snapshot, run a VM installer test,
  or promote a release.
- `make boot ISO=...` boots a chosen ISO in QEMU with temporary UEFI variables.
  It does not configure a virtual disk or assert that installation works.
- `make create`, `make create-thumbdrive`, and release promotion are not
  implemented yet. In particular, `make create` must not become a build alias.
- `config/packages.json` and `config/services.json` establish ownership and
  policy data shapes; only the minimal ISO package set is implemented.
- Screenshots and performance numbers will be added only after the relevant
  desktop exists and has actually been run.
