/**
 * @file R7FA2E1A5.ld
 */

MEMORY {
    IROM (r x) : ORIGIN = 0x00000000, LENGTH = 128k
    IRAM (rw ) : ORIGIN = 0x20004000, LENGTH = 16k
}