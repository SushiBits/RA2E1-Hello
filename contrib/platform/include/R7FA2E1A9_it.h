/**
 * @file R7FA2E1A9_it.h
 * 
 * Startup header for RA2E1.
 */

#ifndef _R7FA2E1A9_IT_H_
#define _R7FA2E1A9_IT_H_

#include <sys/cdefs.h>

typedef void (*vector_t)(void);

__BEGIN_DECLS

extern vector_t vector[];

#define IRQN_HANDLER(idx, name) void name##_IRQHandler(void);
#define SKIP_HANDLER(idx)
#include "R7FA2E1A9_handlers.h"
#undef IRQN_HANDLER
#undef SKIP_HANDLER

__END_DECLS

#endif // defined(_R7FA2E1A9_IT_H_)