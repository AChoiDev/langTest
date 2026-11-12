/*
 * qbepy_wrapper.c - C wrapper implementation for QBE FFI
 */

#include "qbepy_wrapper.h"

/* Include QBE's main header for all type definitions */
#include "all.h"
#include "config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <setjmp.h>

/* Thread-local storage for error handling and output capture */
#if defined(_MSC_VER)
#define THREAD_LOCAL __declspec(thread)
#elif defined(__GNUC__) || defined(__clang__)
#define THREAD_LOCAL __thread
#else
#define THREAD_LOCAL _Thread_local
#endif

/* Error state */
static THREAD_LOCAL char qbepy_error_msg[QBEPY_ERROR_SIZE];
static THREAD_LOCAL jmp_buf qbepy_error_jmp;
static THREAD_LOCAL int qbepy_in_compile = 0;

/* Output buffer */
static THREAD_LOCAL char* qbepy_output_buf = NULL;
static THREAD_LOCAL size_t qbepy_output_len = 0;
static THREAD_LOCAL size_t qbepy_output_cap = 0;

/* External target definitions */
extern Target T_amd64_sysv;
extern Target T_amd64_apple;
extern Target T_arm64;
extern Target T_arm64_apple;
extern Target T_rv64;

/* Current target - normally defined in main.c */
Target T;

/* Debug flags - normally defined in main.c */
char debug['Z'+1] = {0};

/* Debug file path - normally defined in main.c */
char *dbgfile;

/* Deftgt is a macro defined in config.h that expands to one of the targets above */

/* Target list */
static Target* qbepy_targets[] = {
    &T_amd64_sysv,
    &T_amd64_apple,
    &T_arm64,
    &T_arm64_apple,
    &T_rv64,
    NULL
};

/*
 * Custom error handler - replaces QBE's err() function.
 * This is called via macro redefinition in the build.
 */
void
qbepy_err(char *s, ...)
{
    va_list ap;

    va_start(ap, s);
    vsnprintf(qbepy_error_msg, QBEPY_ERROR_SIZE, s, ap);
    va_end(ap);

    if (qbepy_in_compile) {
        longjmp(qbepy_error_jmp, 1);
    } else {
        /* Fallback if called outside compile context */
        fprintf(stderr, "qbepy error: %s\n", qbepy_error_msg);
        abort();
    }
}

/*
 * Output buffer management
 */
static void
output_init(void)
{
    qbepy_output_len = 0;
    if (qbepy_output_cap == 0) {
        qbepy_output_cap = 4096;
        qbepy_output_buf = malloc(qbepy_output_cap);
    }
    if (qbepy_output_buf) {
        qbepy_output_buf[0] = '\0';
    }
}

static void
output_write(const char* data, size_t len)
{
    if (!qbepy_output_buf) return;

    /* Grow buffer if needed */
    while (qbepy_output_len + len + 1 > qbepy_output_cap) {
        qbepy_output_cap *= 2;
        char* new_buf = realloc(qbepy_output_buf, qbepy_output_cap);
        if (!new_buf) {
            /* Memory allocation failed */
            return;
        }
        qbepy_output_buf = new_buf;
    }

    memcpy(qbepy_output_buf + qbepy_output_len, data, len);
    qbepy_output_len += len;
    qbepy_output_buf[qbepy_output_len] = '\0';
}

static void
output_printf(const char* fmt, ...)
{
    char buf[4096];
    va_list ap;

    va_start(ap, fmt);
    int len = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if (len > 0) {
        output_write(buf, len);
    }
}

/*
 * Custom output FILE* using fmemopen or memory buffer
 * We'll use a simpler approach: collect output via callbacks
 */

/* Output FILE for capturing assembly */
static THREAD_LOCAL FILE* qbepy_outf = NULL;

static FILE*
create_output_file(void)
{
#if defined(__linux__) || defined(__APPLE__) || defined(__FreeBSD__)
    /* Use open_memstream for dynamic buffer */
    return open_memstream(&qbepy_output_buf, &qbepy_output_len);
#else
    /* Fallback: use tmpfile */
    return tmpfile();
#endif
}

// Create input file to be used by the parse function
static FILE*
create_input_file(void *input, size_t input_len)
{
#if defined(__linux__) || defined(__APPLE__) || defined(__FreeBSD__)
    /* Use fmemopen for memory backed file */
    return fmemopen(input, input_len, "r");
#else
    /* Fallback: use tmpfile */
    return tmpfile();
#endif
}

static char*
finish_output_file(FILE* f, size_t* len)
{
#if defined(__linux__) || defined(__APPLE__) || defined(__FreeBSD__)
    fflush(f);
    fclose(f);
    *len = qbepy_output_len;
    char* result = qbepy_output_buf;
    qbepy_output_buf = NULL;
    qbepy_output_len = 0;
    qbepy_output_cap = 0;
    return result;
#else
    /* Read from tmpfile */
    fflush(f);
    long size = ftell(f);
    rewind(f);
    char* result = malloc(size + 1);
    if (result) {
        fread(result, 1, size, f);
        result[size] = '\0';
        *len = size;
    }
    fclose(f);
    return result;
#endif
}

/*
 * Callbacks for QBE's parse function
 */
static void
cb_dbgfile(char *fn)
{
    if (qbepy_outf) {
        emitdbgfile(fn, qbepy_outf);
    }
}

static void
cb_data(Dat *d)
{
    if (qbepy_outf) {
        emitdat(d, qbepy_outf);
        if (d->type == 1) { /* DEnd */
            fputs("/* end data */\n\n", qbepy_outf);
        }
    }
    freeall();
}

static void
cb_func(Fn *fn)
{
    /* Run the QBE compilation pipeline */
    /* This is essentially what main.c:func() does */

    T.abi0(fn);
    fillcfg(fn);
    filluse(fn);
    promote(fn);
    filluse(fn);
    ssa(fn);
    filluse(fn);
    ssacheck(fn);
    fillalias(fn);
    loadopt(fn);
    filluse(fn);
    fillalias(fn);
    coalesce(fn);
    filluse(fn);
    filldom(fn);
    ssacheck(fn);
    gvn(fn);
    fillcfg(fn);
    simplcfg(fn);
    filluse(fn);
    filldom(fn);
    gcm(fn);
    filluse(fn);
    ssacheck(fn);

    if (T.cansel) {
        ifconvert(fn);
        fillcfg(fn);
        filluse(fn);
        filldom(fn);
        ssacheck(fn);
    }

    T.abi1(fn);
    simpl(fn);
    fillcfg(fn);
    filluse(fn);
    T.isel(fn);
    fillcfg(fn);
    filllive(fn);
    fillloop(fn);
    fillcost(fn);
    spill(fn);
    rega(fn);
    fillcfg(fn);
    simpljmp(fn);
    fillcfg(fn);

    /* Link blocks */
    for (uint n = 0; ; n++) {
        if (n == fn->nblk - 1) {
            fn->rpo[n]->link = 0;
            break;
        } else {
            fn->rpo[n]->link = fn->rpo[n + 1];
        }
    }

    /* Emit assembly */
    if (qbepy_outf) {
        T.emitfn(fn, qbepy_outf);
        fprintf(qbepy_outf, "/* end function %s */\n\n", fn->name);
    }

    freeall();
}

/*
 * Public API implementation
 */

const char*
qbepy_get_error(void)
{
    return qbepy_error_msg;
}

void
qbepy_clear_error(void)
{
    qbepy_error_msg[0] = '\0';
}

int
qbepy_compile(
    const char* input,
    size_t input_len,
    const char* target,
    char** output,
    size_t* output_len
)
{
    FILE* inf = NULL;

    /* Initialize */
    *output = NULL;
    *output_len = 0;
    qbepy_clear_error();

    /* Set target */
    if (target && *target) {
        int found = 0;
        for (Target** t = qbepy_targets; *t; t++) {
            if (strcmp(target, (*t)->name) == 0) {
                T = **t;
                found = 1;
                break;
            }
        }
        if (!found) {
            snprintf(qbepy_error_msg, QBEPY_ERROR_SIZE,
                     "unknown target: %s", target);
            return QBEPY_ERROR;
        }
    } else {
        T = Deftgt;
    }

    /* Create input stream from string */
    if (input_len == 0) {
        input_len = strlen(input);
    }
    inf = create_input_file((void*)input, input_len);
    if (!inf) {
        snprintf(qbepy_error_msg, QBEPY_ERROR_SIZE,
                 "failed to create input stream");
        return QBEPY_ERROR;
    }

    /* Create output stream */
    qbepy_outf = create_output_file();
    if (!qbepy_outf) {
        fclose(inf);
        snprintf(qbepy_error_msg, QBEPY_ERROR_SIZE,
                 "failed to create output stream");
        return QBEPY_ERROR;
    }

    /* Set up error recovery */
    qbepy_in_compile = 1;
    if (setjmp(qbepy_error_jmp) != 0) {
        /* Error occurred - longjmp landed here */
        qbepy_in_compile = 0;
        fclose(inf);
        if (qbepy_outf) {
            fclose(qbepy_outf);
            qbepy_outf = NULL;
        }
        freeall();
        return QBEPY_ERROR;
    }

    /* Run QBE parser and compiler */
    parse(inf, "<input>", cb_dbgfile, cb_data, cb_func);

    /* Emit final output (target-specific) */
    T.emitfin(qbepy_outf);

    qbepy_in_compile = 0;
    fclose(inf);

    /* Get output */
    *output = finish_output_file(qbepy_outf, output_len);
    qbepy_outf = NULL;

    if (!*output) {
        snprintf(qbepy_error_msg, QBEPY_ERROR_SIZE,
                 "failed to capture output");
        return QBEPY_ERROR;
    }

    return QBEPY_OK;
}

void
qbepy_free(void* ptr)
{
    free(ptr);
}

const char*
qbepy_get_targets(void)
{
    return "amd64_sysv,amd64_apple,arm64,arm64_apple,rv64";
}

const char*
qbepy_get_default_target(void)
{
    return Deftgt.name;
}

const char*
qbepy_version(void)
{
    return "1.2";
}
