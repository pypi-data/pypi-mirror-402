from ..left_click import recipe
from .connection import connect_machine
from .mana import mana_level
from .transport import output_transport
from ...info import RUNES_USER, CONNECTIONS, PROCESSING_TIME


def machine(tick, current_tile, kind, attributes, tile, chunk, chunks):
    if "inventory" not in current_tile:
        machine_inventory = {}
    else:
        machine_inventory = current_tile["inventory"]
    if "harvester" in attributes:
        chunks[chunk][tile]["recipe"] = 0
    if "process" not in current_tile:
        current_tile["process"] = 0
    if current_tile.get("recipe", -1) >= 0 and current_tile["process"] == 0:
        delete_item = []
        for item in machine_inventory:
            if item.split(" ")[-1] == "mineable":
                delete_item.append(item)
        for item in delete_item:
            del machine_inventory[item]
        efficiency = 1
        connection = True
        if kind in RUNES_USER:
            machine_inventory, efficiency = mana_level(chunks, chunk, tile, kind, current_tile, machine_inventory, efficiency)
        if kind in CONNECTIONS:
            connection, efficiency, chunks = connect_machine(chunks, chunk, tile, kind, attributes, connection, efficiency)
        if connection and efficiency:
            machine_inventory = recipe(kind, current_tile["recipe"], machine_inventory, (20, 64))
            current_tile["process"] = PROCESSING_TIME[current_tile["kind"]] // efficiency
    machine_inventory, chunks = output_transport(chunks, chunk, tile, current_tile, kind, {"connected", "transport"})
    if current_tile["process"] > 0:
        current_tile["process"] -= 1
    return machine_inventory