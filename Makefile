PYTHON ?= python3

.PHONY: help doctor lint test build boot

help:
	@printf '%s\n' \
		'Personal Arch development targets:' \
		'  make doctor      Check build-host requirements' \
		'  make lint        Validate manifests and Python/shell syntax' \
		'  make test        Run unit tests' \
		'  sudo make build  Build an unpublished ArchISO candidate' \
		'  make boot ISO=PATH  Boot an ISO in a UEFI QEMU VM'

doctor:
	$(PYTHON) scripts/doctor.py

lint:
	$(PYTHON) -m compileall -q scripts tests
	bash -n iso/profiledef.sh
	grep -Fqx 'arch="x86_64"' iso/profiledef.sh
	grep -Fqx "bootmodes=('uefi.systemd-boot')" iso/profiledef.sh
	$(PYTHON) scripts/validate_config.py

test:
	$(PYTHON) -m unittest discover -s tests -v

build:
	$(PYTHON) scripts/build_iso.py

boot:
	@test -n "$(ISO)" || { echo 'Set ISO to an explicit image path.' >&2; exit 2; }
	$(PYTHON) scripts/boot_iso.py --iso "$(ISO)"
