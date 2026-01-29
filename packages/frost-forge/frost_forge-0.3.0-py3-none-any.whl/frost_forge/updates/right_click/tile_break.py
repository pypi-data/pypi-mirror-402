from ...info import HEALTH
from .damage_calculation import calculate_damage
from .inventory_move import move_inventory


def break_tile(inventory, chunks, mining_tile, inventory_number, inventory_size):
    delete_mining_tile = False
    if "health" not in mining_tile:
        mining_tile["health"] = HEALTH[mining_tile["kind"]]
    mining_tile["health"] -= calculate_damage(
        mining_tile["kind"], inventory, inventory_number
    )
    if mining_tile["health"] <= 0:
        mining_floor_exist = "floor" in mining_tile
        if mining_floor_exist:
            mining_floor = mining_tile["floor"]
        inventory, junk_inventory = move_inventory(mining_tile, inventory, inventory_size)
        if mining_floor_exist:
            mining_tile = {}
        else:
            delete_mining_tile = True
        if len(junk_inventory) > 0:
            mining_tile = {"kind": "junk", "inventory": junk_inventory}
        if mining_floor_exist:
            mining_tile["floor"] = mining_floor
    return chunks, delete_mining_tile, mining_tile
