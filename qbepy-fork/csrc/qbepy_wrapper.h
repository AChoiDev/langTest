/*
 * qbepy_wrapper.h - C wrapper for QBE to enable FFI usage
 *
 * This wrapper provides a safe interface to QBE that:
 * 1. Intercepts errors via setjmp/longjmp instead of exit()
 * 2. Captures output to a buffer instead of stdout
 * 3. Provides a clean C API for CFFI bindings
 */

#ifndef QBEPY_WRAPPER_H
#define QBEPY_WRAPPER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Result codes */
#define QBEPY_OK 0
#define QBEPY_ERROR 1

/* Error buffer size */
#define QBEPY_ERROR_SIZE 2048

/* Get last error message (thread-local) */
const char* qbepy_get_error(void);

/* Clear error state */
void qbepy_clear_error(void);

/*
 * Compile QBE IL to assembly.
 *
 * Parameters:
 *   input      - QBE IL source code (null-terminated string)
 *   input_len  - Length of input (or 0 to use strlen)
 *   target     - Target architecture name, or NULL for default
 *                Valid targets: amd64_sysv, amd64_apple, arm64, arm64_apple, rv64
 *   output     - Pointer to receive output buffer (caller must free with qbepy_free)
 *   output_len - Pointer to receive output length
 *
 * Returns:
 *   QBEPY_OK on success, QBEPY_ERROR on failure.
 *   On failure, call qbepy_get_error() for the error message.
 */
int qbepy_compile(
    const char* input,
    size_t input_len,
    const char* target,
    char** output,
    size_t* output_len
);

/*
 * Free memory allocated by qbepy_compile.
 */
void qbepy_free(void* ptr);

/*
 * Get comma-separated list of available targets.
 */
const char* qbepy_get_targets(void);

/*
 * Get default target for current platform.
 */
const char* qbepy_get_default_target(void);

/*
 * Get QBE version string.
 */
const char* qbepy_version(void);

#ifdef __cplusplus
}
#endif

#endif /* QBEPY_WRAPPER_H */
