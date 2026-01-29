NOISE_STRUCTURES = {
    "forest": (((0, 0.01), "mushroom hut"),),
    "mountain": (((0, 0.01), "mineshaft"), ((0.11, 0.12), "amethyst geode")),
}
ROOM_COLORS = {
    "amethyst geode": {
        (95, 81, 114): {"kind": "amethyst brick", "floor": "amethyst brick floor"},
        (123, 104, 150): {"floor": "amethyst brick floor"},
        (160, 138, 193): {"floor": "amethyst mineable"},
        (136, 68, 31): {"kind": "skeleton", "inventory": {"copper ingot": 1}, "floor": "amethyst brick floor"},
    },
    "mineshaft": {
        (53, 53, 54): {"kind": "stone brick", "floor": "stone floor"},
        (138, 138, 140): {"floor": "stone brick floor"},
        (247, 247, 255): {"kind": "rock", "floor": "stone floor"},
        (73, 58, 37): {"kind": "log", "floor": "wood floor"},
        (92, 74, 49): {"kind": "wood", "floor": "wood floor"},
        (129, 107, 63): {"floor": "wood door"},
        (19, 17, 18): {"kind": "coal ore", "inventory": {"coal": 1}, "floor": "stone floor"},
        (123, 104, 150): {"kind": "small crate", "loot": "mine chest", "floor": "stone floor"},
        (60, 181, 71): {"kind": "slime", "inventory": {"slime ball": 1}, "floor": "stone floor"},
    },
    "mushroom hut": {
        (247, 247, 255): {"kind": "mushroom block", "floor": "mushroom floor"},
        (138, 138, 140): {"floor": "mushroom floor"},
        (53, 53, 54): {"floor": "mushroom door"},
        (106, 228, 138): {"kind": "mushroom shaper", "floor": "mushroom floor"},
        (92, 74, 49): {"kind": "small crate", "loot": "mushroom chest", "floor": "mushroom floor"},
    },
}
STRUCTURE_ENTRANCE = {
    "amethyst geode": {"kind": "amethyst", "floor": "amethyst mineable"},
    "mineshaft": {"floor": "stone floor"},
    "mushroom hut": {"floor": "mushroom door"},
}
STRUCTURE_ROOMS = {
    "amethyst geode": ("amethyst geode",),
    "mineshaft": ("hallway", "coal mine"),
    "mushroom hut": ("mushroom hut",),
}
ADJACENT_ROOMS = ((0, -1), (0, 1), (-1, 0), (1, 0))
