import os
import cv2 as cv
import json
import copy
import numpy as np
from random import choice
from PIL import Image

import typer
from typing_extensions import Annotated

from utils import load_tile_imgs


class World:
    def __init__(self, xSize, ySize, neighbour_rules, tile_size):
        self.xSize = int(xSize)
        self.ySize = int(ySize)
        self.world_size = xSize * ySize
        self.history = [] # Stack
        self.neighbour_rules = neighbour_rules
        self.tile_size = tile_size
        self.create_new_world(self.xSize, self.ySize)
    
    # Creates an empty world
    def create_new_world(self, xSize, ySize):
        world = []
        for x in range(xSize):
            world.append([])
            for y in range(ySize):
                world[x].append(Tile(x, y, list(self.neighbour_rules.keys())))
                
        self.world = world
    
    # Finds the candidate tiles with the lowest entropy
    def find_candidate_tiles(self):
        lowest_entropy = len(self.neighbour_rules.keys())
        candidate_tiles = []
        for x in range(self.xSize):
            for y in range (self.ySize):
                tile = self.world[x][y]
                if tile.get_tile_id() == "-1":
                    tile.update_entropy()
                    # Entropy is lower. Remove candidate tiles and continue with
                    # new lowest entropy
                    if tile.get_entropy() < lowest_entropy:
                        candidate_tiles = [tile]
                        lowest_entropy = tile.get_entropy()
                    # Entropy is equal. Add tile to list of possible candidates.
                    elif tile.get_entropy() == lowest_entropy:
                        candidate_tiles.append(tile)

        return candidate_tiles
        
    #checks if given a certain tile id on a position, no neighbour gets no viable possibilities
    def check_nb_viable(self, x, y, id):
        if (y-1 >= 0): # if above is in bounds
            # up
            if (len(self.world[x][y-1].get_possibilities() & self.get_nb_possibilities(id, "up")) <= 0) and self.world[x][y-1].get_tile_id() == "-1":
                return False
        if (x+1 < self.xSize):
            # right
            if (len(self.world[x+1][y].get_possibilities() & self.get_nb_possibilities(id, "right")) <= 0) and self.world[x+1][y].get_tile_id() == "-1":
                return False
        if (y+1 < self.ySize):
            # down
            if (len(self.world[x][y+1].get_possibilities() & self.get_nb_possibilities(id, "down")) <= 0) and self.world[x][y+1].get_tile_id() == "-1":
                return False
        if (x-1 >= 0):
            # left
            if (len(self.world[x-1][y].get_possibilities() & self.get_nb_possibilities(id, "left")) <= 0) and self.world[x-1][y].get_tile_id() == "-1":
                return False
        return True
        
    
    # Decrease possibilities for all tiles. This is done by checking
    # the possibilities of the neighbours and intersecting them with
    # the possibilities of the other adjacent neighbours, as well
    # as looking in the dictionary of possibilities.
    def collapse(self):
        #reset entropy values, needed in case of undo's
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1":
                    self.world[x][y].set_possibilities(list(self.neighbour_rules.keys()))
                    

        #calculate new entropy values
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != "-1":
                    self.world[x][y].set_possibilities(set())
                    if y-1 >= 0 : # if above is in bounds
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
                    if x-1 >= 0:
                        # left
                        self.world[x-1][y].set_possibilities(self.world[x-1][y].get_possibilities() & 
                                                                self.get_nb_possibilities(self.world[x][y].get_tile_id(), "left"))
                        

    def create_image(self, tile_imgs):
        new_world_map = Image.new('RGB', (self.xSize*self.tile_size, self.ySize*self.tile_size))
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != '-1':
                    converted_img = cv.cvtColor(tile_imgs[self.world[x][y].get_tile_id()], cv.COLOR_BGR2RGB)
                    tile_img = Image.fromarray(converted_img)
                    new_world_map.paste(tile_img, (x*self.tile_size, y*self.tile_size))
        new_world_map.save('world.png')
        print("Saved image!")
        # new_world_map.show()

    def show_image(self, tile_imgs):
        new_world_map = Image.new('RGB', (self.xSize*self.tile_size, self.ySize*self.tile_size))
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != '-1':
                    converted_img = cv.cvtColor(tile_imgs[self.world[x][y].get_tile_id()], cv.COLOR_BGR2RGB)
                    tile_img = Image.fromarray(converted_img)
                    new_world_map.paste(tile_img, (x*self.tile_size, y*self.tile_size))
        # new_world_map.save('world.png')
        # print("Saved image!")
        open_cv_image = np.array(new_world_map)
        open_cv_image = open_cv_image[:, :, ::-1].copy() #RGB to BGR
        cv.imshow('Current state', open_cv_image)
        cv.waitKey(10)
                
            
                      
    # Reset the possibilities for all tiles, so all tiles
    # are possible again as neighbours for each tile.
    def reset_possibilities(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                # if self.world[x][y].get_tile_id() != "-1":
                self.world[x][y].set_possibilities(list(self.neighbour_rules.keys()))
                # self.world[x][y].update_entropy()
                    
                
    # Get the possibilities of the neighbour in a certain direction.
    def get_nb_possibilities(self, id, direction):
        return(set(self.neighbour_rules[id][direction]))
    

    # Walk through all tiles and check whether we are stuck.
    # We are stuck when a tile has an id of -1 (empty tile),
    # but the entropy (no. of possible tiles) is equal to 0.
    def stuck_check(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1" and self.world[x][y].get_entropy() == 0:
                    return True
                
        return False
    
    # Calculates how far we are currently in generating the world
    def progress_calculator(self):
        n_tiles_left = 0
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1" or self.world[x][y].get_entropy() != 0:
                    n_tiles_left += 1

        n_tiles_done = self.world_size - n_tiles_left
        progress = round(100 * (n_tiles_done / self.world_size))
        return progress
    
    # Walk through all tiles and check whether we are done.
    # We are done when all tiles have an id that is not -1
    # and the entropy is 0.
    def done_check(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1" or self.world[x][y].get_entropy() != 0:
                    return False
                
        return True
    
    # Print all ids in the world in terminal.
    def debug_terminal_print(self):
        for y in range(self.ySize):
            for x in range(self.xSize):
                print(self.world[x][y].get_tile_id(), end="" + '\t')
            print("\n", end="")


    def debug_terminal_print_entropy(self):
        for y in range(self.ySize):
            for x in range(self.xSize):
                print(self.world[x][y].get_entropy(), end="" + '\t')
            print("\n", end="")

    #checks if all tiles in world are "-1" and thus not set
    def is_empty(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != "-1":
                    return False
        return True
    
    #returns the tile object at x,y
    def get_tile(self, x, y):     
        return self.world[x][y]
    
    #sets the tile at x,y to id. don't forget to collapse
    def set_tile(self, x, y, id):
        self.world[x][y].set_tile_id(id)


class Tile:
    def __init__(self, x, y, all_tile_ids):
        self.x = x
        self.y = y
        self.entropy = len(all_tile_ids)

        self.possibilities = set(copy.deepcopy(all_tile_ids))
        self.tile_id = "-1" #positive numbers represent a tile ID

    # Returns the entropy of the tile.
    def get_entropy(self):
        return self.entropy
    
    # Changes the entropy to the number of possible tiles.
    def update_entropy(self):
        self.entropy = len(self.possibilities)
    
    # Returns the ids of the tiles that could be placed here.
    def get_possibilities(self):
        return self.possibilities
    
    # Set the possibilities of the tile.
    def set_possibilities(self, new_possibilities):
        self.possibilities = set(copy.deepcopy(new_possibilities))
        self.update_entropy()
    
    # Returns the type id of the tile.
    def get_tile_id(self):
        return self.tile_id

    # Set the type id of the tile.
    def set_tile_id(self, id):
        self.tile_id = id

    # Returns the position of the tile in the world.
    def get_position(self):
        return self.x, self.y
    

class WaveCollapser:
    def __init__(self):
        self.progress = 0
        self.is_running = False

        self.tile_folder = None
        self.neighbour_rules_file = None
        self.xSize = None
        self.ySize = None
        self.show_generation = None
        pass

    def update_config(self, tile_folder, neighbour_rules_file, xSize, ySize, show_generation):
        self.tile_folder = tile_folder
        self.neighbour_rules_file = neighbour_rules_file
        self.xSize = xSize
        self.ySize = ySize
        self.show_generation = show_generation

    # Load tile rules
    def load_neighbours_json(self, filename):
        with open(filename, "r") as file:
            tile_neighbours = json.load(file)
            return tile_neighbours       

    def generate(self, world, tile_imgs, update_callback):
        self.progress = world.progress_calculator()
        update_callback(self.progress)
        # Main generating loop
        while(True):
            # If stuck, return and try another config
            if world.stuck_check():
                print("We are stuck!")
                return None
            # List of tiles we can choose from with lowest entropy
            candidate_tiles = world.find_candidate_tiles()
        
            while(True):
                if world == None:
                    print("Hard error bro")
                # When done, propagate world upwards out of recursion
                if world.done_check():
                    return world
                # If there are no candidate tiles left, we are stuck
                if (len(candidate_tiles) == 0):
                    print("No more candidate tiles in this branch, going back")
                    return None
                # Keep trying tiles and removing them, so if it doesn't work out,
                # we try another
                chosen_tile = choice(list(candidate_tiles))
                candidate_tiles.remove(chosen_tile)

                # Get all possible tile IDs that can be placed on selected tile
                candidate_tile_ids = chosen_tile.get_possibilities()

                if len(candidate_tile_ids) > 0:
                    # Once again, chose a tile ID and remove it so we do not try
                    # it again if it doesn't work out
                    chosen_tile_id = choice(list(candidate_tile_ids))
                    candidate_tile_ids.remove(chosen_tile_id)

                    # Set tile ID
                    chosen_tile.set_tile_id(chosen_tile_id)
                    world.collapse()
                    
                    if self.show_generation:
                        print("Current world")
                        world.show_image(tile_imgs)
                        world.debug_terminal_print()
                        print("Current entropy")
                        world.debug_terminal_print_entropy()
                        print()

                    # Recursion: try to generate further with the current world
                    done_world = self.generate(copy.deepcopy(world), tile_imgs, update_callback)
                    # Propagate world out of recursion if we are done
                    if done_world != None and done_world.done_check():
                        print("We are done")
                        world = done_world
                    
                    # Undo tile
                    chosen_tile.set_tile_id("-1")
                    world.collapse()
                else:
                    print("No more ids available for candidate tile, choosing another")

    def run(self, update_callback):
        self.is_running = True

        tile_imgs, tile_size = load_tile_imgs(self.tile_folder)
        neighbour_rules = self.load_neighbours_json(self.neighbour_rules_file)
        world = World(self.xSize, self.ySize, neighbour_rules, tile_size)
        world = self.generate(world, tile_imgs, update_callback)
        world.create_image(tile_imgs)

        self.is_running = False
                    
    

# This part is to make sure the script can still be called separately without the UI.
def main(
    tile_folder: Annotated[str, typer.Argument(help="The folder containing all separate tile images")],
    neighbour_rules_file: Annotated[str, typer.Argument(help="The JSON file containing the rules of what tiles can have which neighbours.")],
    x_size: Annotated[int, typer.Argument(help="The horizontal dimension of the generated world in number of tiles.")],
    y_size: Annotated[int, typer.Argument(help="The vertical dimension of the generated world in number of tiles.")],
    show_generation: Annotated[bool, typer.Argument(help="Show the world being generated. Note: this may result in slower generation, especially when the generator gets 'stuck' in a local problem.")]
):
    waveCollapser = WaveCollapser()
    waveCollapser.update_config(tile_folder, neighbour_rules_file, x_size, y_size, show_generation)
    def update_callback(progress):
        pass
        # This is an empty function to make sure the gui can properly connect and pass its own callback function
        # print(f"Tile extraction progress: {progress}%") # Optional (extra) report if you don't like tqdm
    waveCollapser.run(update_callback)


if __name__=="__main__":
    typer.run(main)

"""
TODO:
Soms duurt genereren heel erg lang, misschien door moeilijke tegels.
Misschien een soort stop-moment inbouwen?

Water fixen: tegels die niet in de wereld voorkomen wel alloceren zodat die gevonden kunnen
worden, waaronder water.

Gewichten zodat we niet 3 telefoonhuisjes krijgen

Animatie van genereren, met live entropie updates. Partially. done

Misschien ook nog als extensie: kijken tussen world-sections, maar niet altijd.
Alleen als het in dezelfde type "biome" is?
"""