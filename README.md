# ra2e1-hello

A bare-metal demo for the Renesas RA2E1 (Cortex-M23), built **without
e² studio and without the Flexible Software Package (FSP)**. Just a Makefile,
the GNU Arm toolchain, CMSIS 6 and the device headers generated from the
Renesas SVD.

The firmware starts the 24 MHz HSE crystal, programs SysTick for a 1 ms
timebase and blinks the LED on P201 every 500 ms.

This is my first project on a Renesas MCU, and my first Cortex-M23 project
that produced blinkenlights.

## Hardware

The board is in [hardware/](hardware) as a KiCad 8 project (schematic, PCB
and project settings), and the same design is published as
[doc/ra2e1-evk.pdf](doc/ra2e1-evk.pdf). It is built around an
R7FA2E1AxxxFJ (LQFP-32), a 24 MHz crystal, a USB-C connector, one LED on P201
and one button.

The physical board carries an **R7FA2E1A5** (32 KB flash). The A5, A7 and A9
parts differ only in flash size (32, 64 and 128 KB, all with the same 16 KB
of RAM and the same peripherals), so one device header and one SVD cover the
family: the build links the 32 KB memory map from
`contrib/platform/lib/R7FA2E1A5.ld`, while the debug configuration and the
SVD name the A9. The mismatch is intentional, not a copy-paste slip.

Renesas documentation lives in [doc/vendor/](doc/vendor).

## Repository layout

| Path | Contents |
|---|---|
| `src/` | Application: `main.c`, `systick.c`, `config.c` (option bytes) |
| `include/` | Project headers, e.g. `systick.h` |
| `lib/ra2e1-hello.ld` | Project linker script (vector table, `.config`, layout) |
| `contrib/platform/` | Device support: startup code, system file, RA2E1 memory maps, SVD/SFR/SFD sources |
| `contrib/platform/include/` | Device headers, generated from the SVD by `make headers` |
| `contrib/cmsis/` | CMSIS 6 submodule |
| `hardware/` | KiCad project for the board |
| `doc/` | Board schematics; `doc/vendor/` holds the Renesas datasheet and manuals |
| `.vscode/` | Build task and Cortex-Debug (J-Link) configuration |

## Building

Requirements:

- `arm-none-eabi-gcc` with Cortex-M23 support (built here with Arm GNU Toolchain 13.2 and 15.3)
- GNU make, plus a Unix-like shell for `mkdir -p` and `rm -rf` (Git Bash or MSYS2)
- `python3` (generates the interrupt handler table with `contrib/platform/share/irqn.py`)
- Optionally Keil's `SVDConv.exe` in `C:\Keil_v5\UV4` (or edit `SVDCONV_PATH` in the
  Makefile) to regenerate the device headers from the SVD

```sh
make            # build ra2e1-hello.elf
make hex        # Intel HEX
make bin        # raw binary
make size       # Berkeley totals and a per-section breakdown
make clean      # remove build products
make distclean  # also remove generated device headers
```

The header generation step is prefixed with `-` in the Makefile, so a missing
`SVDConv.exe` does not break the build; the checked-in headers are used
instead.

## Debugging

`.vscode/launch.json` runs Cortex-Debug against a J-Link over SWD, erases the
flash before programming, and loads `contrib/platform/share/R7FA2E1A9.svd` so
the peripheral registers show up by name.

## Notes on the RA2E1

**Write protection is scattered.** Almost every peripheral has its own
write-protect register somewhere in its register block, and you only find out
you forgot one when the write silently does nothing. The centralised
enable/reset scheme used by STM32 and friends is simply easier to understand.

**TrustZone is optional here, thankfully.** Renesas did not go all in on
TrustZone for this part, so there is no security state to get past before the
first instruction runs. My first Cortex-M23 project, on an ATSAML11, crashed
and burned for exactly that reason: the code never managed to run past the
TrustZone level.

**Option bytes in the middle of flash are a trap.** The option-setting memory
sits at `0x00000400`, so the first kilobyte of flash is dead space on small
parts and the linker script has to work around it. Pinning the `.config`
section there took a bit of linker-script wizardry: a bare `. = 0x00000400`
does not move a section that is assigned to a memory region, so the address
has to be attached to the section itself (see `lib/ra2e1-hello.ld`). It is a
common stumbling block for newcomers, and one that fails silently.

## Licence

BSD 3-Clause, see [LICENSE.md](LICENSE.md).
Copyright &copy; 2018-2026 HIKARU Infotech Shanghai Ltd.

Third-party material keeps its own terms:

- Everything under `doc/vendor/` is copyright Renesas Electronics.
- `contrib/platform/share/R7FA2E1A9.sfd`, `R7FA2E1A9.SFR` and
  `R7FA2E1A9.svd` are copyright Renesas, with my own edits.
