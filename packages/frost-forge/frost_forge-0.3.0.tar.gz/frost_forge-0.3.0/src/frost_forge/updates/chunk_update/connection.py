from ..right_click.inventory_move import move_inventory
from ...info import CONNECTIONS, GROW_FROM, CONTENTS, CONTENT_VALUES, REQUIREMENTS, ADJACENT_ROOMS, ATTRIBUTES


def connect_machine(chunks, chunk, tile, kind, attributes, connection, efficiency):
    x = 1
    y = 1
    connector_tile = ((tile[0] + x) % 16, tile[1])
    connector_chunk = (chunk[0] + (tile[0] + x) // 16, chunk[1])
    while chunks[connector_chunk].get(connector_tile, {}).get("kind", None) == CONNECTIONS[kind]:
        x += 1
        connector_tile = ((tile[0] + x) % 16, tile[1])
        connector_chunk = (chunk[0] + (tile[0] + x) // 16, chunk[1])
    connector_tile = (tile[0], (tile[1] + y) % 16)
    connector_chunk = (chunk[0], chunk[1] + (tile[1] + y) // 16)
    while chunks[connector_chunk].get(connector_tile, {}).get("kind", None) == CONNECTIONS[kind]:
        y += 1
        connector_tile = (tile[0], (tile[1] + y) % 16)
        connector_chunk = (chunk[0], chunk[1] + (tile[1] + y) // 16)
    for i in range(0, x + 1):
        for j in range(0, y + 1):
            connected_tile = ((tile[0] + i) % 16, (tile[1] + j) % 16)
            connected_chunk = (chunk[0] + (tile[0] + i) // 16, chunk[1] + (tile[1] + j) // 16)
            if i % x == 0 and j % y == 0:
                if chunks[connected_chunk].get(connected_tile, {}).get("kind", None) != kind:
                    connection = False
            elif i % x == 0 or j % y == 0:
                if chunks[connected_chunk].get(connected_tile, {}).get("kind", None) != CONNECTIONS[kind]:
                    connection = False
    if connection:
        if "harvester" in attributes:
            efficiency = 0
            for i in range(1, x):
                for j in range(1, y):
                    harvest_tile = ((tile[0] + i) % 16, (tile[1] + j) % 16)
                    harvest_chunk = (chunk[0] + (tile[0] + i) // 16, chunk[1] + (tile[1] + j) // 16)
                    if chunks[harvest_chunk].get(harvest_tile, {}).get("kind", None) in GROW_FROM:
                        harvestable = chunks[harvest_chunk][harvest_tile]
                        chunks[chunk][tile]["inventory"] = move_inventory(harvestable, chunks[chunk][tile].get("inventory", {}), (20, 64))[0]
                        if GROW_FROM[harvestable["kind"]] in chunks[chunk][tile]["inventory"]:
                            chunks[chunk][tile]["inventory"][GROW_FROM[harvestable["kind"]]] -= 1
                            chunks[harvest_chunk][harvest_tile]["kind"] = GROW_FROM[harvestable["kind"]]
                        else:
                            chunks[harvest_chunk][harvest_tile] = {"floor": chunks[harvest_chunk][harvest_tile]["floor"]}
        else:
            heat = 0
            efficiency -= 1
            for i in range(1, x):
                for j in range(1, y):
                    content_tile = ((tile[0] + i) % 16, (tile[1] + j) % 16)
                    content_chunk = (chunk[0] + (tile[0] + i) // 16, chunk[1] + (tile[1] + j) // 16)
                    if chunks[content_chunk].get(content_tile, {}).get("kind", None) in CONTENTS[kind]:
                        content = chunks[content_chunk][content_tile]
                        content_kind = content["kind"]
                        for requirement in REQUIREMENTS[content_kind]:
                            required = requirement[1]
                            for location in ADJACENT_ROOMS:
                                adjacent_tile = ((content_tile[0] + location[0]) % 16, (content_tile[1] + location[1]) % 16)
                                adjacent_chunk = ((content_chunk[0] + (content_tile[0] + location[0]) // 16), content_chunk[1] + (content_tile[1] + location[1]) // 16)
                                if chunks[adjacent_chunk].get(adjacent_tile, {}).get("kind", None) == requirement[0]:
                                    required -= 1
                            if required > 0:
                                heat = 999
                        efficiency += CONTENT_VALUES[content_kind][0]
                        heat += CONTENT_VALUES[content_kind][1]
                        if "drill" in attributes and "floor" in content and "drill" in ATTRIBUTES.get(content_kind, {}):
                            if content["floor"].split(" ")[-1] == "mineable":
                                if content["floor"] not in chunks[chunk][tile]["inventory"]:
                                    chunks[chunk][tile]["inventory"][content["floor"]] = 0
                                chunks[chunk][tile]["inventory"][content["floor"]] += CONTENT_VALUES[content_kind][0]
                    elif chunks[content_chunk].get(content_tile, {}).get("kind", None) == CONNECTIONS[kind]:
                        heat = 999
            if heat > 0:
                efficiency = 0
    return connection, efficiency, chunks