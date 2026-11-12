/**
 * @file main.c
 */

#include "R7FA2E1A9.h"

#include "systick.h"

void SystemInit(void) {
    R_SYSC->PRCR =
        (0xA5 << SYSC_PRCR_PRKEY_Pos) |
        (SYSC_PRCR_PRC0_1 << SYSC_PRCR_PRC0_Pos) |
        (SYSC_PRCR_PRC1_1 << SYSC_PRCR_PRC1_Pos) |
        (SYSC_PRCR_PRC3_1 << SYSC_PRCR_PRC3_Pos); // Unlock all clock-related registers.
    __DSB();

    R_SYSC->OPCCR = SYSC_OPCCR_OPCM_00; // High-speed mode.
    //R_SYSC->MEMWAIT = SYSC_MEMWAIT_MEMWAIT_1; // 1WS SRAM. Not required on 24MHz HSE.
    //R_FLCN->FLDWAITR = FLCN_FLDWAITR_FLDWAIT1_1; // 2WS Flash. Not required on 24MHz HSE.
    while (R_SYSC->OPCCR & SYSC_OPCCR_OPCMTSF_Msk); // Wait until high speed mode establishes.

    R_SYSC->MOMCR = 0;
    R_SYSC->MOSCCR = SYSC_MOSCCR_MOSTP_0; // Start HSE
    while (!(R_SYSC->OSCSF & SYSC_OSCSF_MOSCSF_Msk));
    R_SYSC->SCKDIVCR = (R_SYSC->SCKDIVCR & ~SYSC_SCKDIVCR_ICK_Msk) | (0 << SYSC_SCKDIVCR_ICK_Pos);
    R_SYSC->SCKSCR = SYSC_SCKSCR_CKSEL_011;
}

// LED on pin P201 (BOOT)

int main(void) {
    __DSB();
    R_PFS->PWPR = 0;
    __DSB();
    R_PFS->PWPR = PFS_PWPR_PFSWE_Msk;
    __DSB();

    R_PFS->P201PFS = PFS_P201PFS_PDR_Msk; // Output.
    systick_init();

    for (;;) {
        R_PFS->P201PFS ^= PFS_P201PFS_PODR_Msk;
        delay(500);
    }
}