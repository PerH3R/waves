import cv2 as cv
from os import listdir

# Load world png
def load_world_tileset(filename: str):
    tileset = cv.imread(filename)
    return tileset

# Load tile images
def load_tile_imgs(foldername: str) -> tuple[dict, int]:
    tiles = {file.split(".")[0]: cv.imread(foldername + "/" + file) for file in listdir(foldername)}
    tilesize = list(tiles.values())[0].shape[0]
    return tiles, tilesize