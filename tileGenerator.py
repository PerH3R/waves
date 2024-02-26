# TODO funtionality
# import a picture; either tileset (seperated tiles and blank space) or existing map (no seperation)
# detect tile size and spacing
# save tiles as individual png's

import cv2 as cv
import numpy as np
import sys
import matplotlib.pyplot as plt
import os
import copy


def read_args(argflag):
    for i in sys.argv[2:]:
        x = i.split('=')
        if (x[0] == argflag):
            return int(x[1])
    return -1
    
    

def load_tileset(filename):
    print(filename)
    tileset = cv.imread(filename)
    return tileset


def guess_gridsize():
    pass
    # return tileSizePx, gridSizePx

# adds a tile to a list. If an accompanying hashset is passed it doesn't add duplicates
def add_tile(tile, tilelist, hashset=None):
    if hashset is None:
        tilelist.append(tile)
    else:
        if hash(str(tile)) not in hashset:
            hashset.add(hash(str(tile)))
            tilelist.append(tile)
    
def write_tiles(file_dir, tilelist):
    os.makedirs("./{f}_tiles".format(f=file_dir), exist_ok=True)
    imgname = 0
    for tile in tilelist:
        try:
            cv.imwrite("./{f}_tiles/{i}.png".format(f=file_dir, i=imgname), tile)
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
def separate_grid(filename, tileset):
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

    # Save mask to file to inspect
    os.makedirs("./masks", exist_ok=True)
    cv.imwrite("./masks/{f}_mask.png".format(f=filename), color_mask)

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
    
    
    write_tiles(filename, tiles_list)


# "Hardcoded" tile extraction, for tilesets that contain no grid lines.
# tilesize denotes the standard size of the tiles (16 means 16x16).
# Offset is for the cases where there is a border around the entire tileset,
# but no grid.
def fixed_offset_extraction(filename, tileset, tilesize, offset):
    x = 0
    y = 0
    tilesetX_size = tileset.shape[:2][1]
    tilesetY_size = tileset.shape[:2][0]
    tiles_list = []
    tiles_hash = set()
    print(tilesetX_size, tilesetY_size)
    for x in range(offset, tilesetX_size, tilesize):
        for y in range(offset, tilesetY_size, tilesize):
            box_image = tileset[y : y+tilesize, x : x+tilesize]
            add_tile(box_image, tiles_list, tiles_hash)

    write_tiles(filename, tiles_list)
    


def main():
    #load tileset
    filename_path = sys.argv[1]
    tileset = load_tileset(filename_path)
    filename = os.path.basename(filename_path).split(".")[0]
    print("Filename:" , filename)

    

    #if grid, detect distance between tiles
    # if read_args("-g") != 
    tileSizePx = read_args("-t") #-1 if not specified
    gridSizePx = read_args("-g")
    borderSizePx = read_args("-b")

    if borderSizePx == -1 and tileSizePx == -1:
        separate_grid(filename, tileset)
    else:
        print("manual mode")
        fixed_offset_extraction(filename, tileset, tileSizePx, borderSizePx)

    

if __name__=="__main__": 
    main() 