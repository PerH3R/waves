import cv2 as cv
import numpy as np
import os
import sys
np.zeroes = np.zeros

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
tile_possibilities = [None]*num_tiles # Tile
for i in tile_possibilities:
    i = [set(),set(),set(),set()] #urdl

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
def split_sections(world):
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
        world_sections.append(box_image)
    
    return world_sections


# TODO
#gets a contour and returns a representation as an 2d-array
def build_section_ids(world_section, gray_tileset, size):
    if (world_section.shape[0] % size != 0 and world_section.shape[0] <= size*2) or (world_section.shape[1] % size != 0 and world_section.shape[1] <= size*2):
        return
    world_section_gray = cv.cvtColor(world_section, cv.COLOR_BGR2GRAY)
    # For each tile, we match in the world (section).
    for id, tile in gray_tileset.items():
        # print(id)
        res = cv.matchTemplate(world_section_gray, tile, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        # print(res)
        loc = np.where(res >= threshold)
        # print(loc)
        for m in zip(*loc[::-1]):
            # print(m)
            pass

    pass



        
def analyze_old_world_area(area_list):
    if tileXsize == 0 or tileYsize == 0:
        raise ValueError("tilesize inccorect x={} y={}".format(tileXsize, tileYsize))

    for area in area_list:
        for row in range(0,area.size[0], tileXsize):
            for col in range(0,area.shape[1], tileXsize):
                # what is self
                selfTile = tile_data[area[row][col]]

                if row-1 > 0:
                    # add area[row-1][col] (up)
                    # possibilities[selfTile][0].add(area[row-1][col])
                    pass
                if col+1 < area.size[1]:
                    # add area[row][col-1] (right)
                    # possibilities[selfTile][0].add(area[row][col+1])
                    pass
                if row+1 < area.size[0]:
                    # add area[row-1][col] (down)
                    # possibilities[selfTile][0].add(area[row+1][col])
                    pass
                if col-1 > 0:
                    # add area[row][col-1] (left)
                    # possibilities[selfTile][0].add(area[row][col-1])
                    pass
                
                

def main():
    #load tileset. The user gives the name of the world (LADX, AlttP)
    # and the tiles and world are automatically loaded according to the
    # standard naming convention. TODO: is this the nice way to do it?
    worldname = sys.argv[1]
    tileset, size = load_tiles(worldname + "_tiles/")
    world = load_world("worlds/" + worldname + "_world.png")

    gray_tileset = {k: cv.cvtColor(t, cv.COLOR_BGR2GRAY) for k, t in tileset.items()}

    # filename = os.path.basename(filename_path).split(".")[0]
    # print("Filename:" , filename)

    world_sections = split_sections(world)    
    for section in world_sections:
        build_section_ids(section, gray_tileset, size)

    

if __name__=="__main__": 
    main() 

# result = cv.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
# (yCoords, xCoords) = np.where(result >= args["threshold"])