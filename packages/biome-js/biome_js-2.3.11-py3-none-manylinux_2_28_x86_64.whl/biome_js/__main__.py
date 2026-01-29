import os
import sys


def find_biome_bin() -> str:
    """Return the biome binary path."""

    return "biome"


if __name__ == "__main__":
    biome = find_biome_bin()
    os.execvp(biome, [biome, *sys.argv[1:]])
