"""
CFFI build script for qbepy.

This script compiles the vendored QBE source code along with our wrapper
to create a Python extension module.
"""

from __future__ import annotations

import platform
from pathlib import Path

from cffi import FFI

# Determine project root
PROJECT_ROOT = Path(__file__).parent
VENDOR_QBE = PROJECT_ROOT / "vendor" / "qbe"
CSRC = PROJECT_ROOT / "csrc"


def generate_config_h():
    """Generate config.h for QBE based on the current platform."""
    system = platform.system()
    machine = platform.machine().lower()

    # Determine default target based on platform and architecture
    if system == "Darwin":
        if machine in {"arm64", "aarch64"}:
            default_target = "T_arm64_apple"
        else:
            default_target = "T_amd64_apple"
    elif machine in {"arm64", "aarch64"}:
        default_target = "T_arm64"
    elif machine.startswith("riscv") or machine == "rv64":
        default_target = "T_rv64"
    else:
        # Default to amd64_sysv for x86_64 and unknown
        default_target = "T_amd64_sysv"

    config_h = VENDOR_QBE / "config.h"
    config_content = f"#define Deftgt {default_target}\n"

    # Only write if different (avoid unnecessary rebuilds)
    if config_h.exists():
        existing = config_h.read_text()
        if existing == config_content:
            return

    config_h.write_text(config_content)


# Generate config.h before CFFI setup
generate_config_h()

ffi = FFI()

# Define the C interface we expose to Python
ffi.cdef("""
    /* Result codes */
    #define QBEPY_OK 0
    #define QBEPY_ERROR 1

    /* Get last error message */
    const char* qbepy_get_error(void);

    /* Clear error state */
    void qbepy_clear_error(void);

    /* Compile QBE IL to assembly */
    int qbepy_compile(
        const char* input,
        size_t input_len,
        const char* target,
        char** output,
        size_t* output_len
    );

    /* Free memory allocated by qbepy_compile */
    void qbepy_free(void* ptr);

    /* Get comma-separated list of available targets */
    const char* qbepy_get_targets(void);

    /* Get default target for current platform */
    const char* qbepy_get_default_target(void);

    /* Get QBE version string */
    const char* qbepy_version(void);
""")

# Collect QBE source files (excluding main.c - we provide our own entry point)
qbe_sources = []
for src in VENDOR_QBE.glob("*.c"):
    if src.name != "main.c":
        qbe_sources.append(str(src))

# Add target-specific sources
for arch_dir in ["amd64", "arm64", "rv64"]:
    arch_path = VENDOR_QBE / arch_dir
    if arch_path.exists():
        for src in arch_path.glob("*.c"):
            qbe_sources.append(str(src))

# Add our wrapper
wrapper_source = str(CSRC / "qbepy_wrapper.c")

# All sources
sources = [*qbe_sources, wrapper_source]

# Compiler flags
extra_compile_args = ["-std=c99", "-O2", "-DQBEPY_LIBRARY"]
if platform.system() == "Darwin":
    extra_compile_args.append("-Wno-unused-function")
elif platform.system() == "Linux":
    extra_compile_args.extend(["-Wno-unused-function", "-D_GNU_SOURCE"])

# Include directories
include_dirs = [str(VENDOR_QBE), str(CSRC)]

ffi.set_source(
    "qbepy._qbe_ffi",
    """
    #include "qbepy_wrapper.h"
    """,
    sources=sources,
    include_dirs=include_dirs,
    define_macros=[("QBEPY_LIBRARY", "1")],
    extra_compile_args=extra_compile_args,
)

if __name__ == "__main__":
    ffi.compile(verbose=True)
