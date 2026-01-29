#define _GNU_SOURCE

#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/uio.h>

typedef ssize_t (*write_fn)(int, const void *, size_t);
typedef ssize_t (*writev_fn)(int, const struct iovec *, int);
typedef int (*vfprintf_fn)(FILE *, const char *, va_list);
typedef int (*fputs_fn)(const char *, FILE *);
typedef size_t (*fwrite_fn)(const void *, size_t, size_t, FILE *);
typedef int (*fputc_fn)(int, FILE *);
typedef int (*puts_fn)(const char *);

struct line_buffer {
    char *data;
    size_t len;
    size_t cap;
    char *prefix_plain;
    char *prefix_color;
};

static write_fn real_write = NULL;
static write_fn real___write = NULL;
static write_fn real___write_nocancel = NULL;
static writev_fn real_writev = NULL;
static vfprintf_fn real_vfprintf = NULL;
static fputs_fn real_fputs = NULL;
static fwrite_fn real_fwrite = NULL;
static fputc_fn real_fputc = NULL;
static puts_fn real_puts = NULL;
static pthread_once_t init_once = PTHREAD_ONCE_INIT;

static struct line_buffer stdout_buf = {0};
static struct line_buffer stderr_buf = {0};
static pthread_mutex_t stdout_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t stderr_lock = PTHREAD_MUTEX_INITIALIZER;

static char *default_prefix_plain = NULL;
static char *default_prefix_color = NULL;

static __thread int yprint_in_hook = 0;
static __thread char *tls_prefix_plain = NULL;
static __thread char *tls_prefix_color = NULL;

static int color_mode = -1; /* -1 auto, 0 never, 1 always */

static const char *getenv_fallback(const char *primary, const char *legacy) {
    const char *value = getenv(primary);
    if (value && *value) {
        return value;
    }
    value = getenv(legacy);
    if (value && *value) {
        return value;
    }
    return NULL;
}

static void init_default_prefix(void) {
    const char *env = getenv_fallback("YPRINT_PREFIX_WIDTH", "PWATCH_PREFIX_WIDTH");
    if (!env) {
        return;
    }
    char *end = NULL;
    long width = strtol(env, &end, 10);
    if (!end || end == env || width <= 0) {
        return;
    }
    default_prefix_plain = (char *)malloc((size_t)width + 1);
    if (!default_prefix_plain) {
        return;
    }
    memset(default_prefix_plain, ' ', (size_t)width);
    default_prefix_plain[width] = '\0';
    default_prefix_color = strdup(default_prefix_plain);
}

static void init_color_mode(void) {
    const char *env = getenv_fallback("YPRINT_COLOR", "PWATCH_COLOR");
    if (!env) {
        color_mode = -1;
        return;
    }
    if (strcmp(env, "never") == 0) {
        color_mode = 0;
    } else if (strcmp(env, "always") == 0) {
        color_mode = 1;
    } else {
        color_mode = -1;
    }
}

static int color_enabled(int fd) {
    if (color_mode == 0) {
        return 0;
    }
    if (color_mode == 1) {
        return 1;
    }
    if (!isatty(fd)) {
        return 0;
    }
    const char *term = getenv("TERM");
    if (term && strstr(term, "256color")) {
        return 1;
    }
    const char *colorterm = getenv("COLORTERM");
    if (colorterm && *colorterm) {
        return 1;
    }
    return 0;
}

static void yprint_init(void) {
    real_write = (write_fn)dlsym(RTLD_NEXT, "write");
    real___write = (write_fn)dlsym(RTLD_NEXT, "__write");
    real___write_nocancel = (write_fn)dlsym(RTLD_NEXT, "__write_nocancel");
    real_writev = (writev_fn)dlsym(RTLD_NEXT, "writev");
    real_vfprintf = (vfprintf_fn)dlsym(RTLD_NEXT, "vfprintf");
    real_fputs = (fputs_fn)dlsym(RTLD_NEXT, "fputs");
    real_fwrite = (fwrite_fn)dlsym(RTLD_NEXT, "fwrite");
    real_fputc = (fputc_fn)dlsym(RTLD_NEXT, "fputc");
    real_puts = (puts_fn)dlsym(RTLD_NEXT, "puts");
    init_color_mode();
    init_default_prefix();
}

static write_fn resolve_write(write_fn preferred) {
    if (preferred) {
        return preferred;
    }
    if (real_write) {
        return real_write;
    }
    if (real___write) {
        return real___write;
    }
    if (real___write_nocancel) {
        return real___write_nocancel;
    }
    return NULL;
}

static ssize_t write_all(int fd, const char *buf, size_t len) {
    write_fn target = resolve_write(real_write);
    if (!target) {
        errno = ENOSYS;
        return -1;
    }
    size_t written = 0;
    while (written < len) {
        ssize_t rc = target(fd, buf + written, len - written);
        if (rc < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        if (rc == 0) {
            break;
        }
        written += (size_t)rc;
    }
    return (ssize_t)written;
}

static void buffer_ensure_capacity(struct line_buffer *buf, size_t extra) {
    size_t needed = buf->len + extra;
    if (needed <= buf->cap) {
        return;
    }
    size_t new_cap = buf->cap ? buf->cap * 2 : 256;
    while (new_cap < needed) {
        new_cap *= 2;
    }
    char *next = (char *)realloc(buf->data, new_cap);
    if (!next) {
        return;
    }
    buf->data = next;
    buf->cap = new_cap;
}

static void buffer_clear_prefix(struct line_buffer *buf) {
    if (buf->prefix_plain) {
        free(buf->prefix_plain);
        buf->prefix_plain = NULL;
    }
    if (buf->prefix_color) {
        free(buf->prefix_color);
        buf->prefix_color = NULL;
    }
}

static void buffer_set_prefix(struct line_buffer *buf) {
    if (buf->prefix_plain || buf->prefix_color) {
        return;
    }
    const char *plain = tls_prefix_plain ? tls_prefix_plain : default_prefix_plain;
    const char *color = tls_prefix_color ? tls_prefix_color : default_prefix_color;
    if (plain) {
        buf->prefix_plain = strdup(plain);
    }
    if (color) {
        buf->prefix_color = strdup(color);
    }
    if (!buf->prefix_plain) {
        buf->prefix_plain = strdup("");
    }
    if (!buf->prefix_color) {
        buf->prefix_color = strdup("");
    }
}

static int emit_line(int fd, struct line_buffer *buf) {
    const char *prefix = color_enabled(fd) ? buf->prefix_color : buf->prefix_plain;
    if (!prefix) {
        prefix = "";
    }
    if (write_all(fd, prefix, strlen(prefix)) < 0) {
        return -1;
    }
    if (write_all(fd, " | ", 3) < 0) {
        return -1;
    }
    if (buf->len > 0) {
        if (write_all(fd, buf->data, buf->len) < 0) {
            return -1;
        }
    }
    return 0;
}

static ssize_t yprint_write(int fd, const char *buf, size_t count) {
    struct line_buffer *line = (fd == STDOUT_FILENO) ? &stdout_buf : &stderr_buf;
    pthread_mutex_t *lock = (fd == STDOUT_FILENO) ? &stdout_lock : &stderr_lock;

    if (!resolve_write(real_write)) {
        return -1;
    }
    if (count == 0) {
        return 0;
    }

    pthread_mutex_lock(lock);

    size_t offset = 0;
    int rc = 0;
    while (offset < count) {
        const char *start = buf + offset;
        const char *newline = memchr(start, '\n', count - offset);
        size_t chunk = newline ? (size_t)(newline - start + 1) : (count - offset);

        if (line->len == 0) {
            buffer_set_prefix(line);
        }
        buffer_ensure_capacity(line, chunk);
        if (line->data) {
            memcpy(line->data + line->len, start, chunk);
            line->len += chunk;
        }

        offset += chunk;
        if (newline) {
            rc = emit_line(fd, line);
            line->len = 0;
            buffer_clear_prefix(line);
            if (rc < 0) {
                break;
            }
        }
    }

    pthread_mutex_unlock(lock);

    if (rc < 0) {
        return -1;
    }
    return (ssize_t)count;
}

void yprint_set_prefix(const char *plain, const char *color) {
    pthread_once(&init_once, yprint_init);

    if (tls_prefix_plain) {
        free(tls_prefix_plain);
        tls_prefix_plain = NULL;
    }
    if (tls_prefix_color) {
        free(tls_prefix_color);
        tls_prefix_color = NULL;
    }

    if (plain) {
        tls_prefix_plain = strdup(plain);
    }
    if (color) {
        tls_prefix_color = strdup(color);
    }
}

static int stream_fd(FILE *stream) {
    if (!stream) {
        return -1;
    }
    int fd = fileno(stream);
    if (fd == STDOUT_FILENO || fd == STDERR_FILENO) {
        return fd;
    }
    return -1;
}

static int yprint_vfprintf(FILE *stream, const char *format, va_list ap) {
    if (!real_vfprintf) {
        errno = ENOSYS;
        return -1;
    }
    int fd = stream_fd(stream);
    if (yprint_in_hook || fd < 0) {
        return real_vfprintf(stream, format, ap);
    }

    va_list ap_copy;
    va_copy(ap_copy, ap);
    int needed = vsnprintf(NULL, 0, format, ap_copy);
    va_end(ap_copy);
    if (needed < 0) {
        return real_vfprintf(stream, format, ap);
    }

    size_t size = (size_t)needed + 1;
    char *buf = (char *)malloc(size);
    if (!buf) {
        return real_vfprintf(stream, format, ap);
    }

    va_list ap_copy2;
    va_copy(ap_copy2, ap);
    vsnprintf(buf, size, format, ap_copy2);
    va_end(ap_copy2);

    int was_in_hook = yprint_in_hook;
    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, buf, (size_t)needed);
    yprint_in_hook = was_in_hook;

    free(buf);
    if (rc < 0) {
        return -1;
    }
    return (int)rc;
}

int vfprintf(FILE *stream, const char *format, va_list ap) {
    pthread_once(&init_once, yprint_init);
    return yprint_vfprintf(stream, format, ap);
}

int fprintf(FILE *stream, const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    int rc = vfprintf(stream, format, ap);
    va_end(ap);
    return rc;
}

int vprintf(const char *format, va_list ap) {
    return vfprintf(stdout, format, ap);
}

int printf(const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    int rc = vfprintf(stdout, format, ap);
    va_end(ap);
    return rc;
}

int fputs(const char *s, FILE *stream) {
    pthread_once(&init_once, yprint_init);
    if (!real_fputs) {
        errno = ENOSYS;
        return EOF;
    }
    if (yprint_in_hook || !s) {
        return real_fputs(s, stream);
    }
    int fd = stream_fd(stream);
    if (fd < 0) {
        return real_fputs(s, stream);
    }

    size_t len = strlen(s);
    int was_in_hook = yprint_in_hook;
    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, s, len);
    yprint_in_hook = was_in_hook;

    if (rc < 0) {
        return EOF;
    }
    return (int)rc;
}

size_t fwrite(const void *ptr, size_t size, size_t nmemb, FILE *stream) {
    pthread_once(&init_once, yprint_init);
    if (!real_fwrite) {
        errno = ENOSYS;
        return 0;
    }
    if (yprint_in_hook) {
        return real_fwrite(ptr, size, nmemb, stream);
    }
    int fd = stream_fd(stream);
    if (fd < 0) {
        return real_fwrite(ptr, size, nmemb, stream);
    }

    if (size == 0 || nmemb == 0) {
        return 0;
    }
    if (nmemb > SIZE_MAX / size) {
        return real_fwrite(ptr, size, nmemb, stream);
    }

    size_t total = size * nmemb;
    int was_in_hook = yprint_in_hook;
    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, (const char *)ptr, total);
    yprint_in_hook = was_in_hook;

    if (rc < 0) {
        return 0;
    }
    return (size_t)rc / size;
}

int fputc(int c, FILE *stream) {
    pthread_once(&init_once, yprint_init);
    if (!real_fputc) {
        errno = ENOSYS;
        return EOF;
    }
    if (yprint_in_hook) {
        return real_fputc(c, stream);
    }
    int fd = stream_fd(stream);
    if (fd < 0) {
        return real_fputc(c, stream);
    }

    unsigned char ch = (unsigned char)c;
    int was_in_hook = yprint_in_hook;
    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, (const char *)&ch, 1);
    yprint_in_hook = was_in_hook;

    if (rc < 0) {
        return EOF;
    }
    return (int)ch;
}

int putchar(int c) {
    return fputc(c, stdout);
}

int puts(const char *s) {
    pthread_once(&init_once, yprint_init);
    if (!real_puts) {
        errno = ENOSYS;
        return EOF;
    }
    if (yprint_in_hook || !s) {
        return real_puts(s);
    }
    int fd = stream_fd(stdout);
    if (fd < 0) {
        return real_puts(s);
    }

    int rc = fputs(s, stdout);
    if (rc == EOF) {
        return EOF;
    }
    if (fputc('\n', stdout) == EOF) {
        return EOF;
    }
    return rc + 1;
}

ssize_t write(int fd, const void *buf, size_t count) {
    pthread_once(&init_once, yprint_init);

    write_fn target = resolve_write(real_write);
    if (!target) {
        errno = ENOSYS;
        return -1;
    }

    if (yprint_in_hook || (fd != STDOUT_FILENO && fd != STDERR_FILENO)) {
        return target(fd, buf, count);
    }

    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, (const char *)buf, count);
    yprint_in_hook = 0;
    return rc;
}

ssize_t __write(int fd, const void *buf, size_t count) {
    pthread_once(&init_once, yprint_init);

    write_fn target = resolve_write(real___write);
    if (!target) {
        errno = ENOSYS;
        return -1;
    }

    if (yprint_in_hook || (fd != STDOUT_FILENO && fd != STDERR_FILENO)) {
        return target(fd, buf, count);
    }

    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, (const char *)buf, count);
    yprint_in_hook = 0;
    return rc;
}

ssize_t __write_nocancel(int fd, const void *buf, size_t count) {
    pthread_once(&init_once, yprint_init);

    write_fn target = resolve_write(real___write_nocancel);
    if (!target) {
        errno = ENOSYS;
        return -1;
    }

    if (yprint_in_hook || (fd != STDOUT_FILENO && fd != STDERR_FILENO)) {
        return target(fd, buf, count);
    }

    yprint_in_hook = 1;
    ssize_t rc = yprint_write(fd, (const char *)buf, count);
    yprint_in_hook = 0;
    return rc;
}

ssize_t writev(int fd, const struct iovec *iov, int iovcnt) {
    pthread_once(&init_once, yprint_init);

    if (yprint_in_hook || (fd != STDOUT_FILENO && fd != STDERR_FILENO)) {
        if (!real_writev) {
            errno = ENOSYS;
            return -1;
        }
        return real_writev(fd, iov, iovcnt);
    }

    yprint_in_hook = 1;
    ssize_t total = 0;
    for (int i = 0; i < iovcnt; i++) {
        if (!iov[i].iov_base || iov[i].iov_len == 0) {
            continue;
        }
        ssize_t rc = yprint_write(fd, (const char *)iov[i].iov_base, iov[i].iov_len);
        if (rc < 0) {
            yprint_in_hook = 0;
            return -1;
        }
        total += rc;
    }
    yprint_in_hook = 0;
    return total;
}

__attribute__((destructor))
static void yprint_shutdown(void) {
    pthread_once(&init_once, yprint_init);

    pthread_mutex_lock(&stdout_lock);
    if (stdout_buf.len > 0) {
        emit_line(STDOUT_FILENO, &stdout_buf);
        stdout_buf.len = 0;
        buffer_clear_prefix(&stdout_buf);
    }
    pthread_mutex_unlock(&stdout_lock);

    pthread_mutex_lock(&stderr_lock);
    if (stderr_buf.len > 0) {
        emit_line(STDERR_FILENO, &stderr_buf);
        stderr_buf.len = 0;
        buffer_clear_prefix(&stderr_buf);
    }
    pthread_mutex_unlock(&stderr_lock);
}
