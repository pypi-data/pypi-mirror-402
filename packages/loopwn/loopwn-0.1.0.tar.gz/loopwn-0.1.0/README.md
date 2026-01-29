# loopwn

A Python library designed to assist with CTF Pwn challenges, specifically focusing on Libc address calculation and leak exploitation.

## Installation

```bash
pip install loopwn
```

## Usage

```python
from loopwn import Looplibc

# Example 1: Initialize with a known base address
libc = Looplibc('./libc.so.6', 0x7ffff7a0d000)

# Example 2: Initialize with a leaked symbol address
# This will automatically calculate the base address
libc = Looplibc('./libc.so.6', 'puts', 0x7ffff7a8c5a0)

# Access addresses
print(hex(libc.system))
print(hex(libc.bin_sh))
```

## Features

- **Automatic Base Calculation**: Easily calculate libc base address from a leaked symbol.
- **Quick Access**: Get `system` and `/bin/sh` addresses via properties.
- **Pwntools Integration**: Inherits from `pwntools`'s `ELF` class.
