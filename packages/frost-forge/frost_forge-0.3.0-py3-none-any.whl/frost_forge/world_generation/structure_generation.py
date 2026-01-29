from noise import pnoise2
from random import choice

from ..info import NOISE_STRUCTURES, STRUCTURE_ENTRANCE, STRUCTURE_ROOMS
from .room_generation import generate_room
from .biome_determination import determine_biome


def generate_structure(world_type, noise_offset, chunk_x, chunk_y, chunks, save_chunks):
    if (chunk_x, chunk_y) not in chunks and max(abs(chunk_x), abs(chunk_y)) >= 2:
        structure_value = pnoise2(
            chunk_x + noise_offset[0], chunk_y + noise_offset[1], 3, 0.5, 2
        )
        structure = False
        biome = determine_biome(
            world_type,
            16 * chunk_x + noise_offset[0],
            16 * chunk_y + noise_offset[1],
            noise_offset,
        )
        for noise_structure in NOISE_STRUCTURES.get(biome, ()):
            if noise_structure[0][0] < structure_value < noise_structure[0][1]:
                structure_type = noise_structure[1]
                structure = True
                break
        if structure:
            save_chunks.add((chunk_x, chunk_y))
            dungeon_room = choice(STRUCTURE_ROOMS[structure_type])
            chunks[chunk_x, chunk_y] = generate_room(
                structure_type,
                dungeon_room,
                (chunk_x, chunk_y),
            )
            chunks[chunk_x, chunk_y][7, 0] = STRUCTURE_ENTRANCE[structure_type]
    return chunks, save_chunks
