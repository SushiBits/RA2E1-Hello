
#include "R7FA2E1A9.h"

uint32_t SystemCoreClock = 4000000;

#ifndef HSE_VALUE
#define HSE_VALUE 8000000
#endif

#ifndef LSE_VALUE
#define LSE_VALUE 32768
#endif

#ifndef HSI_VALUE
#define HSI_VALUE 4000000
#endif

#ifndef MSI_VALUE
#define MSI_VALUE 8000000
#endif

#ifndef LSI_VALUE
#define LSI_VALUE 32768
#endif

__attribute__((weak)) void SystemInit(void) {}

void SystemCoreClockUpdate(void) {}
