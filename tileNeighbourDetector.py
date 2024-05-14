import cv2 as cv
import numpy as np
import os
import sys
from copy import deepcopy
from tqdm import tqdm
import json
import ntpath

import climage

import typer
from typing_extensions import Annotated

from utils import load_world_tileset, load_tile_imgs

np.zeroes = np.zeros # We like being British

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


def validate_supplied_tile(tile_nr, tile_folder, tile_size):
    if not os.path.exists(tile_nr):
        print("Path of the file is invalid")
        return False
    imgfile
    try:
        imgfile = cv.imread(os.path.join(tile_folder, str(tile_nr)+".png"))
    except:
        print("not a valid img")
        return False
    if not (imgfile.shape[0] == tile_size and imgfile.shape[1] == tile_size):
        print("Size of the image is invalid")
        return False
    return True

#gets a (subsection of) the world and returns the representation of the tiles as ids as an 2d-array
def build_section_ids(world_section, tileset, tile_size, specified_tiles):
    # Create an array for the tile ids we find. Initialize on -1 for tiles we did not find.
    section_numbered = np.full((int(world_section.shape[0]/tile_size), int(world_section.shape[1]/tile_size)), -1)

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
            if m[0] % tile_size == 0 and m[1] % tile_size == 0:
                # print(id)
                # print(m)
                # print(m[0]/tile_size, m[1]/tile_size)
                # cv.rectangle(world_section_copy, m, (m[0]+w, m[1]+h), (0,0,255), 1)
                # cv.imwrite("matches/{id}/{id}-match.png".format(id=id), world_section_copy)
                section_numbered[int(m[1]/tile_size)][int(m[0]/tile_size)] = id

    unknown_imgs = [] 
    for y in range(section_numbered.shape[0]):
        for x in range(section_numbered.shape[0]):
            if section_numbered[y][x] == -1:
                current_subsection = world_section[(y*tileSizeY):(y+1)*tileSizeY, (x*tileSizeX):(x+1)*tileSizeX]
                specified_tiles_idx = -1
                
                specified_tiles_idx = -1
                for i in range(len(specified_tiles[0])):
                    if np.array_equal(specified_tiles[0][i], current_subsection):
                        specified_tiles_idx = i


                print("idx", specified_tiles_idx)
                if specified_tiles_idx != -1:                    
                    section_numbered[y][x] = specified_tiles[1][specified_tiles_idx]
                else:
                    unknown_imgs.append(current_subsection)
                    # print(unknown_imgs[-1])
                    print(unknown_imgs[-1].shape)
                    output = climage.convert_array(cv.cvtColor(world_section, cv.COLOR_BGR2RGB), is_unicode=True) 
                    print(output)
                    output = climage.convert_array(cv.cvtColor(unknown_imgs[-1], cv.COLOR_BGR2RGB), is_unicode=True) 
                    # prints output on console. 
                    print(output)
                    tile_nr = input("Please type number of the tile to use here (without file extension e.g. type '1' if you want '1.png'), leave empty if you want to ignore:")
                    print(tile_nr)
                    while not (tile_nr == "") and not tile_nr.isdigit():
                        tile_nr = input("Wrong tilename. \n Please type number of the tile to use here (without file extension e.g. type '1' if you want '1.png'), leave empty ot ype '-1' if you want to ignore:")
                    
                    if not tile_nr == "" and not tile_nr == "-1": 
                        if validate_supplied_tile(tile_nr, tile_folder):
                            section_numbered[y][x] = int(tile_nr)
                            specified_tiles[0].append(current_subsection)
                            specified_tiles[1].append(int(tile_nr))
                    else:
                        print("Ignored")
                        section_numbered[y][x] = -1
                        specified_tiles[0].append(current_subsection)
                        specified_tiles[1].append(-1)

    print(unknown_imgs)
    i = 0
    same_img_idx = []
        
        
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


def tileNBdetect(tile_folder: Annotated[str, typer.Argument(help="The folder containing all separate tile images.")],
                 world_name: Annotated[str, typer.Argument(help="The image file containing the original world from which neighbor rules should be inferred.")],
                 sections_folder: Annotated[str, typer.Argument(help="The folder in which all separate world sections extracted from the world image file should be saved.")],
                 output_file: Annotated[str, typer.Argument(help="The output JSON file containing the rules of what tiles can have which neighbors.")]
                 ):
    
    typer.echo(f"Separate tiles tileset folder: {tile_folder}")
    typer.echo(f"World file: {world_name}")
    typer.echo(f"World sections folder: {sections_folder}")
    typer.echo(f"Output JSON file: {output_file}")

    tileset, tile_size = load_tile_imgs(tile_folder)
    world = load_world_tileset(world_name)

    neighbourdict = {} # Tile

    world_sections = split_sections(world, tile_size)
    sec = 0
    
    os.makedirs(sections_folder, exist_ok=True)
    for s in world_sections:
        cv.imwrite("{w}/section_{sec}.png".format(w=sections_folder, sec=sec),s)
        sec += 1

    neighbourdict = {}
    specified_tiles = [[], #image data
                        []] #tile_nr

    print("Matching tiles in each world section...")
    for section in tqdm(world_sections):
        section_numbered = build_section_ids(section, tileset, tile_size)
        add_sect_to_dict(section_numbered, neighbourdict)
    #convert sets to lists for json dumping
    for tile in neighbourdict.keys():
        for direction in neighbourdict[tile].keys():
            neighbourdict[tile][direction] = list(neighbourdict[tile][direction])
    if not output_file.lower().endswith(".json"):
        output_file += ".json"
    with open(output_file, "w") as f:
        json.dump(neighbourdict, f, indent=4)



    

if __name__=="__main__":
    typer.run(tileNBdetect)


# TODO: can this be removed?
# result = cv.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
# (yCoords, xCoords) = np.where(result >= args["threshold"])

# TODO: 1. Add neighbor weights support?
#       2. We have hardcoded 16x16 tile sizes here, this should be fixed.