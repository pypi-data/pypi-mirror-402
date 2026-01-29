from random import shuffle

from ...info import ADJACENT_ROOMS, ATTRIBUTES, ITEM_TICK, RECIPES, LOOT_TABLES, STORAGE, VALUES


def transport_item(output_kind, machine_inventory, output_inventory, item_tick, max_store):
    if output_kind in machine_inventory:
        output_number = min(machine_inventory[output_kind], item_tick, max_store - output_inventory.get(output_kind, 0))
        if output_kind not in output_inventory:
            output_inventory[output_kind] = output_number
        else:
            output_inventory[output_kind] += output_number
        machine_inventory[output_kind] -= output_number
        if machine_inventory[output_kind] == 0:
            del machine_inventory[output_kind]
    return machine_inventory, output_inventory

def output_transport(chunks, chunk, tile, current_tile, kind, output):
    if "inventory" not in current_tile:
        machine_inventory = {}
    else:
        machine_inventory = current_tile["inventory"]
    side_order = list(ADJACENT_ROOMS)
    shuffle(side_order)
    for location in side_order:
        adjacent_tile = ((tile[0] + location[0]) % 16, (tile[1] + location[1]) % 16)
        adjacent_chunk = (chunk[0] + (tile[0] + location[0]) // 16, chunk[1] + (tile[1] + location[1]) // 16)
        if location in current_tile and current_tile[location] == 1:
            if adjacent_tile in chunks[adjacent_chunk] and "kind" in chunks[adjacent_chunk][adjacent_tile]:
                adjacent = chunks[adjacent_chunk][adjacent_tile]
                if output & ATTRIBUTES.get(adjacent["kind"], set()):
                    if (-location[0], -location[1]) in adjacent and adjacent[-location[0], -location[1]] == 0:
                        if "inventory" not in adjacent:
                            adjacent["inventory"] = {}
                        if adjacent["kind"] in ITEM_TICK:
                            item_tick = ITEM_TICK[adjacent["kind"]]
                            max_store = item_tick * 2
                        else:
                            item_tick = ITEM_TICK[kind]
                            max_store = STORAGE.get(adjacent["kind"], (20, 64))[1]
                        if kind in RECIPES:
                            output_kind = RECIPES[kind][current_tile["recipe"]][0][0]
                            if output_kind not in LOOT_TABLES:
                                machine_inventory, adjacent["inventory"] = transport_item(output_kind, machine_inventory, adjacent["inventory"], item_tick, max_store)
                            else:
                                for item in LOOT_TABLES[output_kind][0]:
                                    if item[1] in machine_inventory:
                                        machine_inventory, adjacent["inventory"] = transport_item(item[1], machine_inventory, adjacent["inventory"], item_tick, max_store)
                        elif machine_inventory:
                            output_kind = list(machine_inventory)[0]
                            transportable = True
                            value_booster = 1
                            if adjacent["kind"] in RECIPES and "recipe" in adjacent:
                                for item in RECIPES[adjacent["kind"]][adjacent["recipe"]][1]:
                                    if item[0] == output_kind:
                                        break
                                    elif item[0] in VALUES and output_kind in VALUES[item[0]]:
                                        value_booster = VALUES[item[0]][output_kind]
                                        machine_inventory[item[0]] = value_booster * item_tick
                                        machine_inventory[output_kind] -= item_tick
                                        if machine_inventory[output_kind] == 0:
                                            del machine_inventory[output_kind]
                                        break
                                else:
                                    transportable = False
                            if transportable:
                                machine_inventory, adjacent["inventory"] = transport_item(output_kind, machine_inventory, adjacent["inventory"], item_tick * value_booster, max_store)
                        chunks[adjacent_chunk][adjacent_tile] = adjacent
    return machine_inventory, chunks