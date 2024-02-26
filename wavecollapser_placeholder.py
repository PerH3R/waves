import os
import cv2 as cv
import json
import copy

# Directions
NORTH = 0
EAST  = 1
SOUTH = 2
WEST  = 3

# World Size in tiles
Xsize = 25
Ysize = 25

world = []
all_tiles = []

class Tile:
    def __init__(self, x, y):
        pass

    value = -1 #positive numbers represent a tile ID
    possibilities = copy.deepcopy(all_tiles)
    entropy = len(possibilities)


# creates framework for collapsing
def create_world(X=Xsize, Y=Ysize):
    for row in range(Y):
        world.append([])
        for column in range(X):
            world[0].append(Tile())
            
    pass


def load_tile_imgs(foldername):
    tiles = {file.split(".")[0]: cv.imread(file) for file in os.listdir(foldername)}
    return tiles

def load_world_json(filename):
    with open("tile_rules{f}".format(filename), "r") as file:
        tile_data = json.load(file)

    return tile_data

def select_tile():
    pass

def collapse():
    pass

def main():
    pass