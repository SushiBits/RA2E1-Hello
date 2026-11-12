
#include "R7FA2E1A9.h"

uint32_t SystemCoreClock = 4000000;

#ifndef HSE_VALUE
#define HSE_VALUE 8000000
#endif

#ifndef LSE_VALUE
#define LSE_VALUE 32768
#endif

#define HSI24_VALUE 24000000
#define HSI32_VALUE 32000000
#define HSI48_VALUE 48000000
#define HSI64_VALUE 64000000
#define MSI_VALUE 8000000
#define LSI_VALUE 32768

__attribute__((weak)) void SystemInit(void) {}

static uint32_t get_hsi_speed(void) {
    switch ((R_OPTIONS->OFS1 & OPTIONS_OFS1_HOCOFRQ1_Msk) >> OPTIONS_OFS1_HOCOFRQ1_Pos) {
        case OPTIONS_OFS1_HOCOFRQ1_24MHZ: return HSI24_VALUE;
        case OPTIONS_OFS1_HOCOFRQ1_32MHZ: return HSI32_VALUE;
        case OPTIONS_OFS1_HOCOFRQ1_48MHZ: return HSI48_VALUE;
        case OPTIONS_OFS1_HOCOFRQ1_64MHZ: return HSI64_VALUE;
        default: return HSI24_VALUE;
    }
}

void SystemCoreClockUpdate(void) {
    switch ((R_SYSC->SCKSCR & SYSC_SCKSCR_CKSEL_Msk) >> SYSC_SCKSCR_CKSEL_Pos) {
        case SYSC_SCKSCR_CKSEL_000: SystemCoreClock = get_hsi_speed(); break;
        case SYSC_SCKSCR_CKSEL_001: SystemCoreClock = MSI_VALUE; break;
        case SYSC_SCKSCR_CKSEL_010: SystemCoreClock = LSI_VALUE; break;
        case SYSC_SCKSCR_CKSEL_011: SystemCoreClock = HSE_VALUE; break;
        case SYSC_SCKSCR_CKSEL_100: SystemCoreClock = LSE_VALUE; break;
        default: SystemCoreClock = HSI24_VALUE; break;
    }
    uint32_t ickdiv = (R_SYSC->SCKDIVCR & SYSC_SCKDIVCR_ICK_Msk)>> SYSC_SCKDIVCR_ICK_Pos;
    SystemCoreClock >>= ickdiv;
}
