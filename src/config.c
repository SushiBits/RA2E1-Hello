/**
 * @file config.c
 */

#include "R7FA2E1A9.h"

__attribute__((used, section(".config"))) const R_OPTIONS_Type options = {
    .OFS0 = 0xFFFFFFFF,
    .OFS1 =
        (OPTIONS_OFS1_LVDAS_DISABLED << OPTIONS_OFS1_LVDAS_Pos) |
        (OPTIONS_OFS1_VDSEL_1V7 << OPTIONS_OFS1_VDSEL_Pos) |
        (OPTIONS_OFS1_HOCOEN_ENABLED << OPTIONS_OFS1_HOCOEN_Pos) | 
        (OPTIONS_OFS1_HOCOFRQ1_64MHZ << OPTIONS_OFS1_HOCOFRQ1_Pos) |
        (OPTIONS_OFS1_ICSATS_TYPEA << OPTIONS_OFS1_ICSATS_Pos),
    .SECMPUAC = 0xFFFFFFFF
};