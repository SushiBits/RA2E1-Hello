/**
 * @file system_R7FA2E1A9.h
 */

#ifndef _SYSTEM_R7FA2E1A9_H_
#define _SYSTEM_R7FA2E1A9_H_

#include <stdint.h>
#include <sys/cdefs.h>

__BEGIN_DECLS

extern uint32_t SystemCoreClock;

void SystemInit(void);
void SystemCoreClockUpdate(void);

__END_DECLS

#endif // defined(_SYSTEM_R7FA2E1A9_H_)