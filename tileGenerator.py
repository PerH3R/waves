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
        x = x.split
        if (x.split('=')[0] == argflag):
            return int(x[1])
    return -1
    
    

def load_tileset(filename):
    print(filename)
    tileset = cv.imread(filename)
    return tileset


def guess_gridsize():
    pass
    # return tileSizePx, gridSizePx


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
    # Detect grid color
    gridcolor = tileset[0,0]

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

    tiles_list = [] # set()
    tiles_hash = set()

    # For all contours, cut out tile
    imgname = 0
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
        if hash(str(box_image)) not in tiles_hash:
            tiles_hash.add(hash(str(box_image)))
            tiles_list.append(box_image)     

    # Create folder for tiles
    os.makedirs("./{f}_tiles".format(f=filename), exist_ok=True)
    
    # Write all (unique) tiles
    imgname = 0
    for tile in tiles_list:
        try:
            cv.imwrite("./{f}_tiles/{i}.png".format(f=filename, i=imgname), tile)
            imgname += 1

        except:
            raise BufferError("Error: Tried to save an empty image.")


def main():
    #load tileset
    filename_path = sys.argv[1]
    tileset = load_tileset(filename_path)
    filename = os.path.basename(filename_path).split(".")[0]
    print("Filename:" , filename)

    separate_grid(filename, tileset)

    #if grid, detect distance between tiles
    # if read_args("-g") != 
    tileSizePx = read_args("-t") #-1 if not specified
    gridSizePx = read_args("-g")

if __name__=="__main__": 
    main() 