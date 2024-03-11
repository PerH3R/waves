import os
import cv2 as cv
import json
import copy
import numpy as np
from random import choice

# TODO for increasing the scope of the project:
# 1. Add tile weighs, maybe even based on occurrence in the "real world".
# 2. Prevent tiles that cannot have neighbors in a certain direction to be placed
#    on a spot where neighbors need to be filled in in that direction.


# tilesize
tileXsize = 0
tileYsize = 0

# Directions
NORTH = 0
EAST  = 1
SOUTH = 2
WEST  = 3

# World Size in tiles
xSize = 25
ySize = 25


all_tiles = []
all_tiles_gray = []

class World:
    def __init__(self, xSize, ySize, neighbor_rules):
        self.xSize = int(xSize)
        self.ySize = int(ySize)
        self.neighbor_rules = neighbor_rules
        self.create_new_world(self.xSize, self.ySize)
    
    # Creates an empty world
    def create_new_world(self, xSize, ySize):
        world = []
        for x in range(self.xSize):
            world.append([])
            for y in range(ySize):
                world[x].append(Tile(x, y, list(self.neighbor_rules.keys())))
                
        self.world = world

    # # Returns a tile at position x, y
    # def get_tile(self, x, y):
    #     return self.world[x][y]
    
    # Selects the tile with the lowest entropy
    def select_tile(self):
        lowest_entropy = len(self.neighbor_rules.keys())
        candidate_tiles = []
        for x in range(self.xSize):
            for y in range (self.ySize):
                tile = self.world[x][y]
                if tile.get_tile_id() == "-1":
                    self.world[x][y].update_entropy()
                    # Entropy is lower. Remove candidate tiles and continue with
                    # new lowest entropy
                    if tile.get_entropy() < lowest_entropy:
                        candidate_tiles = [tile]
                        lowest_entropy = tile.get_entropy()
                    # Entropy is equal. Add tile to list of possible candidates.
                    elif tile.get_entropy() == lowest_entropy:
                        candidate_tiles.append(tile)

        if len(candidate_tiles) != 0:
            return choice(candidate_tiles)
        else:
            return None
    
    def collapse(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != "-1":
                    if y-1 > 0 : # if above is in bounds
                        # up
                        self.world[x][y-1].set_possibilities(self.world[x][y-1].get_possibilities() & 
                        self.get_nb_possibilities(self.world[x][y].get_tile_id(), "up")) 
                    if x+1 < self.xSize :
                        # right
                        self.world[x+1][y].set_possibilities(self.world[x+1][y].get_possibilities() & 
                                                                self.get_nb_possibilities(self.world[x][y].get_tile_id(), "right"))
                    if y+1 < self.ySize:
                        # down
                        self.world[x][y+1].set_possibilities(self.world[x][y+1].get_possibilities() & 
                                                                self.get_nb_possibilities(self.world[x][y].get_tile_id(), "down"))
                    if x-1 > 0:
                        # left
                        self.world[x-1][y].set_possibilities(self.world[x-1][y].get_possibilities() & 
                                                                self.get_nb_possibilities(self.world[x][y].get_tile_id(), "left"))
                    
                

    def get_nb_possibilities(self, id, direction):
        return(set(self.neighbor_rules[id][direction]))
    
    def debug_terminal_print(self):
        for y in range(self.ySize):
            for x in range(self.xSize):
                print(self.world[x][y].get_tile_id(), end="" + '\t')
            print("\n", end="")



class Tile:
    def __init__(self, x, y, all_tile_ids):
        self.x = x
        self.y = y
        self.entropy = len(all_tile_ids)

        self.possibilities = set(copy.deepcopy(all_tile_ids))
        self.tile_id = "-1" #positive numbers represent a tile ID
        # self.neighbors = dict()

    # Returns the entropy of the tile
    def get_entropy(self):
        return self.entropy
    
    def update_entropy(self):
        self.entropy = len(self.possibilities)
        pass
    
    def get_possibilities(self):
        return self.possibilities
    
    def set_possibilities(self, new_possibilities):
        self.possibilities = new_possibilities
    
    def get_tile_id(self):
        return self.tile_id

    def set_tile_id(self, id):
        self.tile_id = id
        




# Load tile images
def load_tile_imgs(foldername):
    tilefolder = foldername+"_tiles/"
    tiles = {file.split(".")[0]: cv.imread(tilefolder + file) for file in os.listdir(tilefolder)}
    return tiles

# Load tile rules
def load_neighbors_json(filename):
    with open("{f}_neighbors.json".format(f=filename), "r") as file:
        tile_neighbors = json.load(file)
        return tile_neighbors

            

def main():
    tilesname = input("What tileset to use for world generation? ")
    tile_imgs = load_tile_imgs(tilesname)
    tile_neighbors = load_neighbors_json(tilesname)
    xSize = input("What world size? X-coodinate: ")
    ySize = input("What world size? Y-coordinate: ")

    all_tile_ids = list(tile_imgs.keys())
    world = World(xSize, ySize, tile_neighbors)

    # Main generating loop
    while(True):
        world.collapse()
        new_tile = world.select_tile()
        if new_tile == None:
            print("Finished!")
            break
        else:
            # place_id = choice(list(new_tile.get_possibilities()))
            # print(place_id)
            new_tile.set_tile_id(choice(list(new_tile.get_possibilities())))

        world.debug_terminal_print()
        print()

if __name__=="__main__": 
    main()