"""Master Collection filename-seeded symmetric outer transform.

Callers must restart the stream at each format-defined allocation boundary.
"""

from __future__ import annotations

from pathlib import Path


MASK32 = 0xFFFFFFFF


def _u32(value: int) -> int:
    return value & MASK32


def filename_seed(filename: str | Path) -> int:
    name = Path(filename).name.split(".", 1)[0]
    encoded = name.encode("ascii")
    value = 0
    for byte in encoded:
        value = _u32(value * 0x2356F + byte * 0x1D35)
    return value


class PcStream:
    def __init__(self, seed: int) -> None:
        self.state: list[int] = []
        for _ in range(624):
            high = seed & 0xFFFF0000
            seed = _u32(seed * 0x10DCD + 1)
            self.state.append(high | (seed >> 16))
            seed = _u32(seed * 0x10DCD + 1)
        self.output: list[int] = []
        self.index = 0
        self._twist()

    def _twist(self) -> None:
        for index in range(227):
            value = (self.state[index] & 0x80000000) | (
                self.state[index + 1] & 0x7FFFFFFF
            )
            self.state[index] = _u32(
                self.state[index + 397]
                ^ (value >> 1)
                ^ (0x9908B0DF if value & 1 else 0)
            )
        for index in range(227, 623):
            value = (self.state[index] & 0x80000000) | (
                self.state[index + 1] & 0x7FFFFFFF
            )
            self.state[index] = _u32(
                self.state[index - 227]
                ^ (value >> 1)
                ^ (0x9908B0DF if value & 1 else 0)
            )
        value = (self.state[623] & 0x80000000) | (self.state[0] & 0x7FFFFFFF)
        self.state[623] = _u32(
            self.state[396]
            ^ (value >> 1)
            ^ (0x9908B0DF if value & 1 else 0)
        )
        self.output = []
        for value in self.state:
            value ^= value >> 11
            value ^= (value << 7) & 0x9D2C5680
            value ^= (value << 15) & 0xEFC60000
            value ^= value >> 18
            self.output.append(_u32(value))

    def next(self) -> int:
        if self.index >= 624:
            self._twist()
            self.index = 0
        result = self.output[self.index]
        self.index += 1
        return result


def outer_transform(data: bytes, seed: int) -> bytes:
    """Encrypt or decrypt one independently seeded physical byte span."""

    stream = PcStream(seed)
    for _ in range(5):
        stream.next()
    output = bytearray(data)
    for offset in range(0, len(output), 4):
        count = min(4, len(output) - offset)
        value = int.from_bytes(output[offset : offset + count], "little")
        value ^= stream.next() ^ 0xB9D3018F
        output[offset : offset + count] = value.to_bytes(4, "little")[:count]
    return bytes(output)
