# FONT clean deterministic round-trip report

Pipeline: clean encrypted XPR → destination-filename OuterCrypt decrypt → parse → topology rebuild with no semantic changes → destination-filename encrypt → decrypt again → compare.

Any mismatch is a failure; no canonicalization exception is used.

| selector | seed | original decrypted SHA256 | rebuilt decrypted SHA256 | rebuilt encrypted SHA256 | plaintext exact | encrypted exact | status |
|---|---:|---|---|---|---|---|---|
| 00c7c9f9.xpr | `0x3AF33BE1` | `31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b` | `31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b` | `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d` | PASS | PASS | **PASS** |
| 001cbbd1.xpr | `0xF2C6C89B` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | PASS | PASS | **PASS** |

## 00c7c9f9.xpr

| validation | result |
|---|---|
| XPR2 magic | PASS |
| resource count | PASS |
| USER content | PASS |
| charmap | PASS |
| GlyphRecords | PASS |
| TX2D descriptor | PASS |
| TX2D bitmap | PASS |
| all offsets | PASS |
| all sizes | PASS |
| alignment | PASS |
| decrypted plaintext byte-identical | PASS |
| encrypted bytes byte-identical | PASS |
| encrypt→decrypt plaintext byte-identical | PASS |
| OuterCrypt destination selector seed | PASS |

## 001cbbd1.xpr

| validation | result |
|---|---|
| XPR2 magic | PASS |
| resource count | PASS |
| USER content | PASS |
| charmap | PASS |
| GlyphRecords | PASS |
| TX2D descriptor | PASS |
| TX2D bitmap | PASS |
| all offsets | PASS |
| all sizes | PASS |
| alignment | PASS |
| decrypted plaintext byte-identical | PASS |
| encrypted bytes byte-identical | PASS |
| encrypt→decrypt plaintext byte-identical | PASS |
| OuterCrypt destination selector seed | PASS |

Overall: **PASS**
