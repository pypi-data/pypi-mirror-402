import pygame as pg

from ...info import (
    ATTRIBUTES,
    SCREEN_SIZE,
    UI_SCALE,
    SLOT_SIZE,
    TILE_UI_SIZE,
    HALF_SCREEN_SIZE,
    STORAGE,
    RECIPES,
    ADJACENT_ROOMS,
)
from .craft_rendering import render_craft
from .store_rendering import render_store
from .machine_rendering import render_machine


def render_open(machine_ui, window, images, recipe_tile, machine_inventory):
    attributes = ATTRIBUTES.get(machine_ui, set())
    if "open" in attributes and "connected" not in attributes:
        window.blit(
            pg.transform.scale(
                images["big_inventory_slot"], (320 * UI_SCALE, 128 * UI_SCALE)
            ),
            (HALF_SCREEN_SIZE - 160 * UI_SCALE, SCREEN_SIZE[1] - 160 * UI_SCALE),
        )
        window.blit(
            pg.transform.scale(images["inventory_slot_3"], SLOT_SIZE),
            (HALF_SCREEN_SIZE + 88 * UI_SCALE, SCREEN_SIZE[1] - 80 * UI_SCALE),
        )
        window.blit(
            pg.transform.scale(images[machine_ui], TILE_UI_SIZE),
            (HALF_SCREEN_SIZE + 96 * UI_SCALE, SCREEN_SIZE[1] - 76 * UI_SCALE),
        )
        if "craft" in attributes:
            window = render_craft(window, RECIPES[machine_ui], images, recipe_tile.get("recipe", 0))
        elif "machine" in attributes:
            window = render_machine(
                window, RECIPES.get(machine_ui, ()), images, machine_inventory, recipe_tile, machine_ui,
            )
        elif "store" in attributes:
            window = render_store(window, STORAGE[machine_ui][0], images, machine_inventory)
    if {"machine", "store", "connected"} & attributes:
        window.blit(
            pg.transform.scale(
                images["medium_inventory_slot"], (128 * UI_SCALE, 128 * UI_SCALE)
            ),
            (HALF_SCREEN_SIZE + 160 * UI_SCALE, SCREEN_SIZE[1] - 160 * UI_SCALE),
        )
        for location in ADJACENT_ROOMS:
            sprite_location = (HALF_SCREEN_SIZE + (208 + 32 * location[0]) * UI_SCALE, SCREEN_SIZE[1] - (112 - 32 * location[1]) * UI_SCALE)
            if location not in recipe_tile:
                slot_image = images["inventory_slot_5"]
            elif recipe_tile[location] == 0:
                slot_image = images["inventory_slot"]
            else:
                slot_image = images["inventory_slot_2"]
            window.blit(pg.transform.scale(slot_image, (32 * UI_SCALE, 32 * UI_SCALE)), sprite_location)
    return window
