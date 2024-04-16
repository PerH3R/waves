import cv2 as cv
import numpy as np
import os
import sys
np.zeroes = np.zeros # We like being British
from copy import deepcopy
from tqdm import tqdm
import json


# todo -> contouring worldmap af, area bij area kopies maken met nummers gematched aan tiles om vervolgens burenlijsten van te kunnen maken


# class Tile:
#     def __init__(self):
#         for i in self.possibilities:
#             i = np.zeroes[4] #urdl
#         pass

#     value = -1 #positive numbers represent a tile ID
    # format: [ [[u][r][d][l]], ... , [[1,4,5][2,3][4,9][1,4]]
    #             \> tile nrs of tiles that are allowed to be at this position respective of current tile
    # possibilities = np.zeroes(num_tiles)

num_tiles = 1


#loads world png
def load_world(filename):
    print(filename)
    world = cv.imread(filename)
    return world


def load_tiles(foldername):
    tiles = {file.split(".")[0]: cv.imread(foldername+file) for file in os.listdir(foldername)}
    tilesize = list(tiles.values())[0].shape[0]
    return tiles, tilesize
    
# uses contours to extract the different areas of an overworld file
# returns seperate sections of the world
def split_sections(world, size):
    # Detect grid color. Legacy: use the pixel at (0,0) to determine the grid color.
    gridcolor = world[0,0]

    # # Detect grid color. Modern: use the most-occurring color to determine the grid color.
    # flattened_world = world.reshape(-1, 3)

    # unique_color, counts = np.unique(flattened_world, axis=0, return_counts=True)
    # max_count_index = np.argmax(counts)

    # gridcolor = unique_color[max_count_index]

    # new_list = []
    # for x, y in zip(counts, unique_color):
    #     new_list.append((x, y))

    # new_list = sorted(new_list, key=lambda element: element[0])

    # print(new_list)

    # Create the mask.
    mask = np.all(world == gridcolor, axis=-1)
    mask = ~mask
    color_mask = mask.astype(np.uint8)
    color_mask *= 255

    # Save mask to file to inspect
    os.makedirs("./worldmasks", exist_ok=True)
    cv.imwrite("./worldmasks/{f}_worldmask.png".format(f="lalal"), color_mask)
    
    # Detect contours
    contours, hierarchy = cv.findContours(image=color_mask, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_SIMPLE)

    world_sections = []

    # For all contours, cut out tile
    for c in contours:
        maxX, maxY = -1, -1
        minX = world.shape[:2][1]
        minY = world.shape[:2][0]
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

        box_image = world[minY : maxY+1, minX: maxX+1]

        if (box_image.shape[0] % size == 0 and box_image.shape[0] >= size*4) and (box_image.shape[1] % size == 0 and box_image.shape[1] >= size*4):
            world_sections.append(box_image)
    
    return world_sections


#gets a (subsection of) the world and returns the representation of the tiles as ids as an 2d-array
def build_section_ids(world_section, tileset, size):
    # Create an array for the tile ids we find. Initialize on -1 for tiles we did not find.
    section_numbered = np.full((int(world_section.shape[0]/size), int(world_section.shape[1]/size)), -1)

    # For each tile, we match it in the world (section).
    for id, tile in tileset.items():
        # os.makedirs("matches/{id}/".format(id=id), exist_ok=True)
        # Create a copy to draw the match on
        # world_section_copy = deepcopy(world_section)
        res = cv.matchTemplate(world_section, tile, cv.TM_SQDIFF_NORMED)
        threshold = 0.01
        w, h = tile.shape[:2]
        loc = np.where(res <= threshold)
        for m in zip(*loc[::-1]):
            # only take into account matches coinciding with stride length
            if m[0] % size == 0 and m[1] % size == 0:
                # print(id)
                # print(m)
                # print(m[0]/size, m[1]/size)
                # cv.rectangle(world_section_copy, m, (m[0]+w, m[1]+h), (0,0,255), 1)
                # cv.imwrite("matches/{id}/{id}-match.png".format(id=id), world_section_copy)
                section_numbered[int(m[1]/size)][int(m[0]/size)] = id

    unknown_imgs = []
    for y in range(section_numbered.shape[0]):
        for x in range(section_numbered.shape[0]):
            if section_numbered[y][x] == -1:
                unknown_imgs.append(world_section[y:y+16, x:x+16])
    # print(unknown_imgs)
    i = 0
    same_img_idx = []
    # while i < len(unknown_imgs)-1:        
    #     for j in range(len(unknown_imgs[i+1:])):
    #         if unknown_imgs[i] == unknown_imgs[j]:
    #             same_img_idx.append(j)
    #             pass
    # for idx in same_img_idx.reverse():
    #     unknown_imgs[i]
    for img in unknown_imgs:
        cv.imshow('Missing image', img)
        cv.waitKey(1)
    return section_numbered

def add_sect_to_dict(section_numbered, neighbourdict):

    for row in range(section_numbered.shape[0]):
        for col in range(section_numbered.shape[1]):
            # For now, skip tiles with ID -1. TODO: ask user to fill in an ID while
            # showing the tile and/or word Section in order, so the user can manually
            # add missing tile IDs, for example for flowing water, etc.
            if section_numbered[row][col] == -1:
                continue
            selfTile = str(section_numbered[row][col])
            if selfTile not in neighbourdict.keys():
                neighbourdict[selfTile] = {}
                neighbourdict[selfTile]["up"], neighbourdict[selfTile]["down"], neighbourdict[selfTile]["left"], neighbourdict[selfTile]["right"] = set(), set(), set(), set()
            if row-1 > 0 and section_numbered[row-1][col] != -1: # if above is in bounds
                # add area[row-1][col] (up)
                neighbourdict[selfTile]["up"].add(str(section_numbered[row-1][col]))
            if col+1 < section_numbered.shape[1] and section_numbered[row][col+1] != -1:
                # add area[row][col-1] (right)
                neighbourdict[selfTile]["right"].add(str(section_numbered[row][col+1]))
            if row+1 < section_numbered.shape[0] and section_numbered[row+1][col] != -1:
                # add area[row-1][col] (down)
                neighbourdict[selfTile]["down"].add(str(section_numbered[row+1][col]))
            if col-1 > 0 and section_numbered[row][col-1] != -1:
                # add area[row][col-1] (left)
                neighbourdict[selfTile]["left"].add(str(section_numbered[row][col-1]))


def main():
    #load tileset. The user gives the name of the world (LADX, AlttP)
    # and the tiles and world are automatically loaded according to the
    # standard naming convention. TODO: is this the nice way to do it?
    worldname = sys.argv[1]
    tileset, size = load_tiles(worldname + "_tiles/")
    world = load_world("worlds/" + worldname + "_world.png")

    neighbourdict = {} # Tile

    world_sections = split_sections(world, size)
    sec = 0
    os.makedirs("world_sections_{w}/".format(w=worldname), exist_ok=True)
    for s in world_sections:
        cv.imwrite("world_sections_{w}/section_{sec}.png".format(w=worldname, sec=sec),s)
        sec += 1

    neighbourdict = {}

    print("Matching tiles in each world section...")
    for section in tqdm(world_sections):
        section_numbered = build_section_ids(section, tileset, size)
        add_sect_to_dict(section_numbered, neighbourdict)
    #convert sets to lists for json dumping
    for tile in neighbourdict.keys():
        for direction in neighbourdict[tile].keys():
            neighbourdict[tile][direction] = list(neighbourdict[tile][direction])
    with open("{w}_neighbors.json".format(w=worldname), "w") as f:
        json.dump(neighbourdict, f, indent=4)



    

if __name__=="__main__": 
    main()

# result = cv.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
# (yCoords, xCoords) = np.where(result >= args["threshold"])