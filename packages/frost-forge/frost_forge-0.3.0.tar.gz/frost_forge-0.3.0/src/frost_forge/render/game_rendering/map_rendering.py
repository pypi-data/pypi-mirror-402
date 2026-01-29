from ...info import TILE_SIZE, CHUNK_SIZE, SCREEN_SIZE, ATTRIBUTES, HALF_SIZE


def renderable(tile, chunk, chunks, zoom, camera):
    rendering = False
    placement = ()
    if tile in chunks[chunk]:
        world_x = tile[0] * TILE_SIZE + chunk[0] * CHUNK_SIZE
        world_y = tile[1] * TILE_SIZE + chunk[1] * CHUNK_SIZE
        placement = [camera[0] + world_x * zoom, camera[1] + world_y * zoom]
        boundary = -4 * TILE_SIZE * zoom
        if boundary <= placement[0] <= SCREEN_SIZE[0] and boundary <= placement[1] <= SCREEN_SIZE[1]:
            rendering = True
    return rendering, placement

def render_map(location, chunks, camera, zoom, scaled_image, window, images):
    for chunk_y in range(-2, 3):
        for chunk_x in range(-2, 3):
            chunk = (chunk_x + location["tile"][0], chunk_y + location["tile"][1])
            if chunk in chunks:
                for y in range(0, 16):
                    for x in range(0, 16):
                        tile = (x, y)
                        rendering, placement = renderable(tile, chunk, chunks, zoom, camera)
                        if rendering:
                            current_tile = chunks[chunk][tile]
                            if "floor" in current_tile:
                                floor_image = scaled_image[current_tile["floor"]]
                                window.blit(floor_image, placement)
    for chunk_y in range(-2, 3):
        for chunk_x in range(-2, 3):
            chunk = (chunk_x + location["tile"][0], chunk_y + location["tile"][1])
            if chunk in chunks:
                for y in range(0, 16):
                    for x in range(0, 16):
                        tile = (x, y)
                        rendering, placement = renderable(tile, chunk, chunks, zoom, camera)
                        if rendering:
                            current_tile = chunks[chunk][tile]
                            if "kind" in current_tile:
                                attributes = ATTRIBUTES.get(current_tile["kind"], set())
                                placement[1] -= HALF_SIZE * zoom
                                if "point" not in attributes:
                                    tile_image = scaled_image[current_tile["kind"]]
                                    window.blit(tile_image, placement)
                                if "table" in attributes and "inventory" in current_tile and current_tile["inventory"]:
                                    content = list(current_tile["inventory"])[0]
                                    placement[1] -= (HALF_SIZE * zoom * (images[content].get_size()[1] // 8 - 2))
                                    content_image = scaled_image[content]
                                    window.blit(content_image, placement)
    return window
