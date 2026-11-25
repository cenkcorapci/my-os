# Candidate ISO integration testing

This procedure checks that an unpublished candidate can be built from the
checked-in profile and boots into the expected network-capable recovery shell.
It is not an installer test or a release-promotion gate.

## Host requirements

- x86_64 Arch Linux with `archiso` installed and working package mirrors.
- Root privileges for `mkarchiso` (`sudo make build`).
- For VM boot testing, `qemu-system-x86_64` and `edk2-ovmf`.
- Enough free disk space for the ISO and the temporary ArchISO work tree.

Alternatively, run the **ISO candidate integration** workflow from the
repository's GitHub Actions page. It runs `make lint test` and `make build` on
an isolated Linux runner, checks the ISO reaches the live recovery environment
in UEFI QEMU, and uploads the candidate and boot evidence for seven days. Only
use the artifact from a successful workflow run; this smoke test does not
replace the manual network and listener checks below.

Do not treat an emulated build or boot as physical-hardware validation. The
live image provides an unauthenticated root console; test only in an isolated
VM or on hardware under controlled physical access. The QEMU procedure below
does not attach a writable disk.

## Build and inspect

From the repository root, run:

```sh
make lint test
make doctor
sudo make build
```

`make doctor` must report the Linux x86_64 host and `mkarchiso` as available.
The build prints a unique candidate directory under `dist/candidate/`; select
the `.iso` in that directory for all remaining steps. Do not select an image
from the staging or work directories.

Check and record the artifact:

```sh
ISO=/absolute/path/to/dist/candidate/<candidate-id>/<image>.iso
test -s "$ISO"
file "$ISO"
sha256sum "$ISO"
```

The file must be a non-empty ISO image. Preserve the hash with the test record
so the boot result can be tied to the exact candidate.

## UEFI QEMU boot

Run the project boot target:

```sh
make boot ISO="$ISO"
```

In the VM, verify all of the following before stopping it:

1. The UEFI systemd-boot menu appears and offers the Personal Arch live entry.
2. The live kernel starts without a panic and reaches the tty1 root recovery
   shell without prompting for a password.
3. `systemctl is-active NetworkManager` returns `active`.
4. `ip link` shows a usable virtual network interface. With QEMU user-mode
   networking and working host connectivity, verify DHCP, routing, DNS, and a
   simple HTTPS request:

   ```sh
   nmcli device status
   ip route
   getent ahosts archlinux.org
   python3 -c 'from urllib.request import urlopen; print(urlopen("https://archlinux.org", timeout=10).status)'
   ```

   Record host/network limitations if these checks cannot reach the internet.
5. `ss -lntup` shows no unexpected listening services; in particular, SSH must
   not be listening by default.
6. The VM has no attached writable disk and no installer or disk changes are
   attempted.

The shell is intentionally unauthenticated and is not evidence of an installed
workstation. Exit QEMU after collecting the observations; its UEFI variables
are disposable and are not written back to the host.

## Results and failure handling

Record the UTC date, Git commit, candidate directory, ISO SHA-256, build-host
architecture, QEMU version, and pass/fail result for each numbered check.
Capture relevant error output without credentials, network secrets, or other
sensitive data. A failed build, missing boot entry, kernel failure, absent
NetworkManager, unexpected listener, or writable VM disk is a failed
integration run: retain the candidate only for diagnosis and do not describe it
as validated.

A passing run demonstrates only candidate construction and the live UEFI VM
boot path. It does not validate installation, persistence, disk handling,
physical hardware, package snapshot reproducibility, or release promotion.
