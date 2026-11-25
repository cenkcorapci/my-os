PYTHON ?= python3
CXX ?= g++
NVCC ?= nvcc
VM_RAM ?= 8192
VM_CPUS ?= 4

.PHONY: help doctor lint test build boot vm toolchain-check

help:
	@printf '%s\n' \
		'Personal Arch development targets:' \
		'  make doctor      Check build-host requirements' \
		'  make lint        Validate manifests and Python/shell syntax' \
		'  make test        Run unit tests' \
		'  make toolchain-check  Compile C++ and CUDA smoke tests' \
		'  sudo make build  Build an unpublished ArchISO candidate' \
		'  make boot ISO=PATH  Boot an explicit ISO in a UEFI QEMU VM' \
		'  make vm [ISO=PATH]  Boot the latest candidate (8 GiB RAM, 4 CPUs)'

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

toolchain-check:
	@set -eu; \
	build_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$build_dir"' EXIT; \
	$(CXX) -std=c++20 -Wall -Wextra -Werror -O2 examples/cpp/hello.cpp -o "$$build_dir/hello"; \
	"$$build_dir/hello"; \
	$(NVCC) --std=c++20 -c examples/cuda/hello.cu -o "$$build_dir/hello-cuda.o"; \
	printf '%s\n' 'CUDA compiler smoke test passed (compile-only; no GPU required).'

build:
	$(PYTHON) scripts/build_iso.py

boot:
	@test -n "$(ISO)" || { echo 'Set ISO to an explicit image path.' >&2; exit 2; }
	$(PYTHON) scripts/boot_iso.py --iso "$(ISO)"

vm:
	@iso="$(ISO)"; \
	if [ -z "$$iso" ]; then \
		iso="$$(find dist/candidate -type f -name '*.iso' -print 2>/dev/null | sort | tail -n 1)"; \
	fi; \
	test -n "$$iso" || { echo 'No candidate ISO found; set ISO=PATH or build/download a candidate first.' >&2; exit 2; }; \
	if [ -n "$(UEFI_CODE)" ] || [ -n "$(UEFI_VARS)" ]; then \
		test -n "$(UEFI_CODE)" -a -n "$(UEFI_VARS)" || { echo 'Set both UEFI_CODE and UEFI_VARS.' >&2; exit 2; }; \
		$(PYTHON) scripts/boot_iso.py --iso "$$iso" --memory-mib "$(VM_RAM)" --cpus "$(VM_CPUS)" \
			--uefi-code "$(UEFI_CODE)" --uefi-vars "$(UEFI_VARS)"; \
	else \
		$(PYTHON) scripts/boot_iso.py --iso "$$iso" --memory-mib "$(VM_RAM)" --cpus "$(VM_CPUS)"; \
	fi
