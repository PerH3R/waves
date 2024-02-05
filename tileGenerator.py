# TODO funtionality
# import a picture; either tileset (seperated tiles and blank space) or existing map (no seperation)
# detect tile size and spacing
# save tiles as individual png's

import cv2 as cv
import numpy as np
import sys
import matplotlib.pyplot as plt
import os


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
# separate image.

# TODO: make sure only the largest area of the detected grid color is
# put in the mask. See: https://z-uo.medium.com/opencv-automatic-select-big-contour-areas-and-remove-8d79464a06e7
# Also, remove the background of tiles that have transparency. Now, they take over the background color.
# Do some research into the alpha in openCV.
def separate_grid(filename, tileset):
    # Detect grid color
    gridcolor = tileset[0,0]

    # Create mask
    mask = np.all(tileset == gridcolor, axis=-1)
    mask = ~mask
    color_mask = mask.astype(np.uint8)
    color_mask *= 255

    # Save mask to file to inspect
    os.makedirs("./masks", exist_ok=True)
    cv.imwrite("./masks/{f}_mask.png".format(f=filename), color_mask)

    # Detect contours
    contours, hierarchy = cv.findContours(image=color_mask, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_NONE)

    # For all contours, cut out tile
    imgname = 0
    for c in contours:
        # Detect contour corners
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

        box_image = tileset[minY : maxY+1, minX: maxX+1]

        os.makedirs("./{f}_tiles".format(f=filename), exist_ok=True)
        
        try:
            cv.imwrite("./{f}_tiles/{i}.png".format(f=filename, i=imgname), box_image)
            imgname += 1

        except:
            raise BufferError("Error: Tried to save an empty image.")

    # return seperate_tiles_list

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

    #seperate tiles
    
    


    pass

if __name__=="__main__": 
    main() 