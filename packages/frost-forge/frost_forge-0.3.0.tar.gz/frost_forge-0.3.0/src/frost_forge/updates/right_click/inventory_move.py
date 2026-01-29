from ...info import VALUES, UNOBTAINABLE


def move_inventory(mining_tile, inventory, inventory_size):
    junk_inventory = {}
    if "inventory" not in mining_tile:
        mining_tile["inventory"] = {}
    if mining_tile["kind"] not in UNOBTAINABLE:
        if mining_tile["kind"].split()[-1].isdigit():
            mining_tile["kind"] = mining_tile["kind"][:-1]
            mining_tile["kind"] += "0"
        mining_tile["inventory"][mining_tile["kind"]] = (
            mining_tile["inventory"].get(mining_tile["kind"], 0) + 1
        )
    for item, amount in mining_tile["inventory"].items():
        if item != "mana_level" and item not in VALUES and item.split()[-1] != "mineable":
            if item in inventory:
                inventory[item] += amount
                if inventory[item] > inventory_size[1]:
                    junk_inventory[item] = inventory[item] - inventory_size[1]
                    inventory[item] = inventory_size[1]
            else:
                if len(inventory) < inventory_size[0]:
                    inventory[item] = amount
                else:
                    junk_inventory[item] = amount
    return inventory, junk_inventory