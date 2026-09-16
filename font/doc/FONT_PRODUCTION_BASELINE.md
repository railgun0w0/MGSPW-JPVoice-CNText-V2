# MGSPW FONT Production Baseline

归档日期：2026-09-16
用途：只记录当前已知能工作的 Golden Baseline；逆向证据链见 [`FONT_TECHNICAL_ARCHIVE.md`](FONT_TECHNICAL_ARCHIVE.md)。

状态只使用：`PROVEN`、`NOT YET PRODUCTIONIZED`、`UNKNOWN`。

## 1. JPN EXE identity

| item | value | status |
|---|---|---|
| executable | `METAL GEAR SOLID PEACE WALKER.exe` | `PROVEN` |
| file/product version | `1.3.1.0` | `PROVEN` |
| size | `18,408,520` bytes | `PROVEN` |
| SHA256 | `82838bbeb357ab4560b727f487121d0baa419a687b6a26b6e29a4c540b12b559` | `PROVEN` |
| supported runtime patch build | the exact identity above only | `PROVEN` |

Evidence provenance: on 2026-09-16 the existing local file `D:\GAME\test\JPN\MGS_PW\mgspw\METAL GEAR SOLID PEACE WALKER.exe` was re-read without modification. Its Windows VERSIONINFO reports both `FileVersion=1.3.1.0` and `ProductVersion=1.3.1.0`; the same file reports size `18,408,520` and SHA256 `82838b...b559`. The executable itself is not in this Git repository, so this VERSIONINFO source is explicitly `LOCAL-ONLY`. The adjacent Experimental report `JPN001C_TEXTURE_CAPACITY_ROOT_CAUSE.md` independently records the same size and full SHA256, but does not by itself prove the version string. `PROVEN` here therefore means the exact locally verified binary identity only, not every executable labeled 1.3.1.0.

Another local EXE hash, `8dd0eaa5cc8d35e121612a52087399399578aeb62df1a5faff64388e7ec7a429`, appears in an older installer check. It was not the binary used by the current dump/RVA investigation and must not receive this runtime patch without a separate version, unpacked-byte, and RVA validation. Its support status is `UNKNOWN`.

## 2. Large font Golden Baseline

| item | value | status |
|---|---|---|
| JPN production selector | `00c7c9f9.xpr` | `PROVEN` |
| clean authoritative input for future owned build | `font/JPN/00c7c9f9.xpr` | `PROVEN` |
| clean encrypted SHA256 | `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d` | `PROVEN` |
| clean atlas | `4096×4096`, pitch `4096`, format `2`, linear 8-bit | `PROVEN` |
| current proven compatibility output | patched MLG large `0007ccd8.xpr` plaintext, pure-rekeyed to the `00c7c9f9.xpr` filename seed | `PROVEN` |
| runtime dimension patch required | no | `PROVEN` |
| patched MLG_CN0007-derived/rekeyed 00c7 append/count/new-atlas technique | TEST2B/TEST3B/`厥` PoCs pass from `3209 records / 3208 mapped` to count `3210` | `PROVEN` |
| clean JPN00c7 full self-owned rebuild runtime compatibility | Phase 2A fixture from clean JPN00c7: `3078 records / 3077 mapped`; real-machine Chinese display confirmed | `PROVEN` |
| full-corpus self-owned large builder/output | Phase 2A technical fixture is runtime-proven; final release asset/profile is not selected | `NOT YET PRODUCTIONIZED` |

The proven legacy compatibility output is an operational Golden, not the future release dependency. The future production large font must be rebuilt from clean JPN00c7 with owned charset/raster inputs.

Phase 2A runtime-proof scope (2026-09-16): this proves only clean JPN00c7 self-owned full-rebuild runtime compatibility. It does not prove clean JPN001c self-owned 4096×4096 runtime output, the final font choice, the final punctuation policy, or the final large/small raster profile.

## 3. Small font Golden Baseline

| item | value | status |
|---|---|---|
| JPN selector | `001cbbd1.xpr` | `PROVEN` |
| clean authoritative input | `font/JPN/001cbbd1.xpr` | `PROVEN` |
| clean encrypted SHA256 | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | `PROVEN` |
| clean atlas | `2048×1024`, pitch `2048`, format `2`, linear 8-bit | `PROVEN` |
| Loading texture path | `001cbbd1.xpr` own TX2D | `PROVEN` |
| proven expanded atlas | `4096×4096`, `data_size=0x1000000` | `PROVEN` |
| runtime patch required for 4096×4096 | yes; Width and Height both must become `0x1000` | `PROVEN` |
| patched MLG000e pure-rekey compatibility | game starts; Chinese glyphs render; old overflow and missing-glyph fallback disappear | `PROVEN` |
| reusable production runtime patch component | PoC exists; release integration/QA not complete | `NOT YET PRODUCTIONIZED` |
| full-corpus self-owned small XPR | not built in this archive pass | `NOT YET PRODUCTIONIZED` |

### Runtime patch points for EXE 1.3.1.0

All addresses are module-relative RVAs and must be resolved as `ASLR module base + RVA`.

| purpose | RVA | original instruction bytes | patched 4096 instruction bytes |
|---|---:|---|---|
| Height | `0x436AB` | `41 B9 00 04 00 00` (`mov r9d,0x400`) | `41 B9 00 10 00 00` (`mov r9d,0x1000`) |
| Width | `0x436B5` | `41 B8 00 08 00 00` (`mov r8d,0x800`) | `41 B8 00 10 00 00` (`mov r8d,0x1000`) |

The proven `2048×1025` diagnostic patch changes only Height:

```text
41 B9 00 04 00 00 -> 41 B9 01 04 00 00
```

It is diagnostic evidence, not the 4096×4096 production setting.

## 4. Runtime patch safety requirements

A productionized patcher must satisfy every item below; any mismatch fails closed without writing.

1. Verify the on-disk EXE identity before launch or attachment: version `1.3.1.0`, size `18,408,520`, exact SHA256 above.
2. Discover the target process and main module; derive patch VAs from the current ASLR module base. Never use a fixed absolute address.
3. Wait until runtime unpack/decode has completed. The on-disk protected bytes are not the executed decoded `.text`; patch only after both complete six-byte runtime instructions match exactly.
4. Verify the full Height instruction and full Width instruction, not only the immediate byte or a short signature.
5. Confirm both instructions are wholly within a committed executable page and that the operation can be performed atomically enough to avoid a half-patched state.
6. Use `VirtualProtectEx` to apply temporary writable executable protection only to the containing page.
7. Re-read both complete instructions after changing protection and before writing. A change or mismatch means no write.
8. Use `WriteProcessMemory`; if either write fails, perform best-effort rollback of any first write.
9. Call `FlushInstructionCache` for the complete patched range.
10. Restore the original page protection with `VirtualProtectEx`.
11. Read back both complete instructions and compare against the exact expected patched byte sequences.
12. Any hash, version, module, page, byte, write, flush, protection-restore, or readback mismatch must report failure and stop. Do not continue with an assumed partial patch.

The existing `LOCAL-ONLY` Experimental source `mgspw_001c_height_poc.cpp` implements the core ASLR lookup, polling, exact byte verification, protection change, write, cache flush, protection restoration, rollback attempt, and readback pattern. It remains a PoC until integrated with release packaging, version gating, logging, recovery behavior, and full QA.

## 5. Real-machine validation status

| validation | status |
|---|---|
| JPN large selector accepts the historical 0007→00c7 pure-rekey output | `PROVEN` |
| Patched MLG_CN0007-derived/rekeyed 00c7 append/count/new-atlas/real-glyph path | `PROVEN` |
| Clean JPN00c7 `2309/2308` full append/rebuild semantics | `UNKNOWN` |
| JPN001c `2048×1025`, Height `0x400→0x401` | `PROVEN` |
| JPN001c patched MLG000e `4096×4096`, Width/Height `0x1000×0x1000` | `PROVEN` |
| Game startup after 4096 patch | `PROVEN` |
| Old `main+0x1DE60` overflow removed | `PROVEN` |
| Small UI / Loading Chinese missing glyphs removed | `PROVEN` |
| Production-ready runtime patch distribution/integration | `NOT YET PRODUCTIONIZED` |
| Self-owned large and small full-corpus XPR pair | `NOT YET PRODUCTIONIZED` |
| Final public-release source font choice | `UNKNOWN` |

## 6. Dependency policy

The third-party patched MLG fonts are currently retained only as:

- compatibility proof;
- reverse-engineering reference;
- runtime-capacity proof.

They must not be defined as the future production dependency. The target production baseline is a completely self-owned pair generated from clean JPN `00c7c9f9.xpr` and `001cbbd1.xpr`, using the project's own charset and an approved source font.
