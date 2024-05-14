# TODO funtionality
# import a picture; either tileset (seperated tiles and blank space) or existing map (no seperation)
# detect tile size and spacing
# save tiles as individual png's

import cv2 as cv
import numpy as np
import sys
import os

from typing import Optional
import typer
from typing_extensions import Annotated

from PyQt5.QtCore import QObject, QThread, pyqtSignal


def load_tileset(filename):
    print(filename)
    tileset = cv.imread(filename)
    return tileset


def guess_grid_size():
    pass
    # return tile_sizePx, grid_sizePx

# adds a tile to a list. If an accompanying hashset is passed it doesn't add duplicates
def add_tile(tile, tilelist, hashset=None):
    if hashset is None:
        tilelist.append(tile)
    else:
        if hash(str(tile)) not in hashset:
            hashset.add(hash(str(tile)))
            tilelist.append(tile)
    
def write_tiles(file_dir, tilelist):

    os.makedirs(file_dir, exist_ok=True)
    imgname = 0
    for tile in tilelist:
        try:
            cv.imwrite("{f}/{i}.png".format(f=file_dir, i=imgname), tile)
            imgname += 1

        except:
            raise BufferError("Error: Tried to save an empty image.")
    

# This function creates a black and white mask for the tileset.
# The color of the grid is auto-detected, after a mask, removing
# the grid, is created. Then, we detect all contours of the mask.
# Using these contours, we cut out each tile and save it as a
# separate image. Note that this only works if the tileset does
# not contain the color of the mask itself, although we think
# this is safe to assume.
# The grid also needs to go around the border of the whole image.
# We use the top left pixel to detect the color of the mask.
def separate_grid(tileset, output_path):
    progressChanged = pyqtSignal(int)
    finished = pyqtSignal()

    # Detect grid color. Legacy: use the pixel at (0,0) to determine the grid color.
    gridcolor = tileset[0,0]

    # # Detect grid color. Modern: use the most-occurring color to determine the grid color.
    # flattened_tileset = tileset.reshape(-1, 3)

    # unique_color, counts = np.unique(flattened_tileset, axis=0, return_counts=True)
    # max_count_index = np.argmax(counts)

    # gridcolor = unique_color[max_count_index]

    # Create the mask.
    mask = np.all(tileset == gridcolor, axis=-1)
    mask = ~mask
    color_mask = mask.astype(np.uint8)
    color_mask *= 255

    # Save mask to file to inspect TODO: doesn't work now anymore with new filename conventions
    # os.makedirs("./masks", exist_ok=True)
    # cv.imwrite("./masks/{f}_mask.png".format(f=output_path), color_mask)

    # Detect contours
    contours, hierarchy = cv.findContours(image=color_mask, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_SIMPLE)

    # First pass: check most common area
    area_dict = {}
    for c in contours:
        area = cv.contourArea(c)
        if area not in area_dict:
            area_dict[area] = 1
        else:
            area_dict[area] += 1

    # Determine the standard area: the most-occurring area of tiles.
    # We discard tiles with other dimensions, as they will not fit.
    standard_area = max(zip(area_dict.values(), area_dict.keys()))[1]

    tiles_list = []
    tiles_hash = set()

    contour_n = 0

    # For all contours, cut out tile
    for c in contours:
        maxX, maxY = -1, -1
        minX = tileset.shape[:2][1]
        minY = tileset.shape[:2][0]
        for coord in c:
            coord = coord[0]
            if coord[0] > maxX: #x coord
                maxX = coord[0]
            if coord[0] < minX: #x coord
                minX = coord[0]
            if coord[1] > maxY: #y coord
                maxY = coord[1]
            if coord[1] < minY: #y coord
                minY = coord[1]

        # Check if tile is a square. If not, we skip the tile.
        if maxX - minX != maxY - minY:
            continue

        # If area of contour does not match standard area, we skip this tile.
        # We may lose some tiles, bat that's a sacrifice we're willing to make. Tey would probably not fit with the
        # other tiles anyway.
        if cv.contourArea(c) != standard_area:
            continue

        box_image = tileset[minY : maxY+1, minX: maxX+1]

        # Hash the tile to ensure we only save unique tiles
        add_tile(box_image, tiles_list, tiles_hash)

        progress = int((contour_n / len(contours)) * 100)
    
    
    write_tiles(output_path, tiles_list)


# "Hardcoded" tile extraction, for tilesets that contain no grid lines.
# tile_size denotes the standard size of the tiles (16 means 16x16).
# Offset is for the cases where there is a border around the entire tileset,
# but no grid.
def fixed_offset_extraction(tileset, output_path, tile_size, grid_offset_x, grid_offset_y, grid_size):
    x = 0
    y = 0
    tilesetX_size = tileset.shape[:2][1]
    tilesetY_size = tileset.shape[:2][0]
    tiles_list = []
    tiles_hash = set()
    print(tilesetX_size, tilesetY_size)
    for x in range(grid_offset_x, tilesetX_size, tile_size+grid_size):
        for y in range(grid_offset_y, tilesetY_size, tile_size+grid_size):
            box_image = tileset[y : y+tile_size, x : x+tile_size]
            add_tile(box_image, tiles_list, tiles_hash)

    write_tiles(output_path, tiles_list)
    


def tileGen(
        filename_path: Annotated[str, typer.Argument(help="The filename of the tileset as a .png (or other image file).")],
        output_path: Annotated[str, typer.Argument(help="The folder name in which the tileset should be extracted as separate image files.")],
        tile_size: Annotated[Optional[int], typer.Option(help="The tile size dimension in pixels. Both horizontal and vertical.")] = None,
        grid_offset_x: Annotated[Optional[int], typer.Option(help="The offset at which the leftmost column of tiles starts, in pixels.")] = None,
        grid_offset_y: Annotated[Optional[int], typer.Option(help="The offset at which the topmost row of tiles starts, in pixels.")] = None,
        grid_size: Annotated[Optional[int], typer.Option(help="The size of the grid; the width of the lines separating tiles, in pixels.")] = None
        ):
    #load tileset
    tileset = load_tileset(filename_path)
    # filename = os.path.basename(filename_path).split(".")[0]  

    typer.echo(f"Filename path: {filename_path}")
    typer.echo(f"Output path: {output_path}")
    typer.echo(f"Tile size: {tile_size}")
    typer.echo(f"Grid offset X: {grid_offset_x}")
    typer.echo(f"Grid offset Y: {grid_offset_y}")
    typer.echo(f"Grid size: {grid_size}")

    if grid_offset_x is None and grid_offset_y is None and tile_size is None:
        separate_grid(tileset, output_path)
    else:
        fixed_offset_extraction(tileset, output_path, tile_size, grid_offset_x, grid_offset_y, grid_size)

    

if __name__=="__main__":
    typer.run(tileGen)
