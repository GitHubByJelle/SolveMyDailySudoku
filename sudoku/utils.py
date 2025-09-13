from typing import Iterable

def bit_of(num: int) -> int:
    return 1 << (num - 1) if num > 0 else 0

def val_of(mask: int) -> int:
    if mask == 0:
        return 0
    if mask <= 0 or (mask & (mask - 1)) != 0:
        raise ValueError("Mask must have exactly one bit set")
    return mask.bit_length()

def bits_iter(mask: int) -> Iterable[int]:
    """Yield concrete values encoded in mask (1..n)."""
    i = 0
    while mask:
        if mask & 1:
            yield i + 1
        mask >>= 1
        i += 1

def num_ones(mask: int) -> int:
    count = 0
    while mask:
        mask &= mask - 1
        count += 1
    return count

def print_mask(mask: int) -> None:
    print(f"{mask:09b}")