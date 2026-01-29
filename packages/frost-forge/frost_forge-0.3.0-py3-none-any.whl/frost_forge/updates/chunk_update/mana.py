from math import sqrt, log2

from ...info import RUNES_USER, RUNES, RECIPES


def mana_level(chunks, chunk, tile, kind, current_tile, machine_inventory, efficiency):
    mana = 0
    for x in range(-RUNES_USER[kind], RUNES_USER[kind] + 1):
        for y in range(-RUNES_USER[kind], RUNES_USER[kind] + 1):
            if sqrt(x ** 2 + y ** 2) <= RUNES_USER[kind]:
                rune_tile = ((tile[0] + x) % 16, (tile[1] + y) % 16)
                rune_chunk = (chunk[0] + (tile[0] + x) // 16, chunk[1] + (tile[1] + y) // 16)
                if rune_tile in chunks[rune_chunk] and "floor" in chunks[rune_chunk][rune_tile]:
                    rune = chunks[rune_chunk][rune_tile]["floor"]
                    if rune in RUNES:
                        if RUNES[rune][0] == 0:
                            mana += RUNES[rune][1]
                        elif RUNES[rune][0] == 1:
                            mana *= RUNES[rune][1]
                            mana += RUNES[rune][2]
    if int(log2(max(mana, 0) ** 1.2 + 2)) != RECIPES[kind][current_tile["recipe"]][2]:
        efficiency = 0
    machine_inventory["mana_level"] = int(log2(mana ** 1.2 + 2))
    return machine_inventory, efficiency