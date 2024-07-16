import os
import cv2 as cv
import json
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
        self.history = []  # Stack to track changes
        self.neighbour_rules = neighbour_rules
        self.tile_size = tile_size
        self.create_new_world(self.xSize, self.ySize)
    
    # Creates an empty world
    def create_new_world(self, xSize, ySize):
        self.world = [[Tile(x, y, list(self.neighbour_rules.keys())) for y in range(ySize)] for x in range(xSize)]
    
    # Finds the candidate tiles with the lowest entropy
    def find_candidate_tiles(self):
        lowest_entropy = len(self.neighbour_rules.keys())
        candidate_tiles = []
        for x in range(self.xSize):
            for y in range(self.ySize):
                tile = self.world[x][y]
                if tile.get_tile_id() == "-1":
                    tile.update_entropy()
                    if tile.get_entropy() < lowest_entropy:
                        candidate_tiles = [tile]
                        lowest_entropy = tile.get_entropy()
                    elif tile.get_entropy() == lowest_entropy:
                        candidate_tiles.append(tile)
        return candidate_tiles
    
    # Helper method to get neighbor positions
    def get_neighbor_positions(self, x, y):
        return {
            'up': (x, y-1),
            'right': (x+1, y),
            'down': (x, y+1),
            'left': (x-1, y)
        }
    
    # Helper method to revert the last change
    def revert_last_change(self):
        if self.history:
            x, y, previous_tile_id = self.history.pop()
            self.world[x][y].set_tile_id(previous_tile_id)

    # Reset the possibilities of all tiles
    def reset_possibilities(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1":
                    self.world[x][y].set_possibilities(set(self.neighbour_rules.keys()))
        
    def aggressive_collapse(self):
        self.reset_possibilities()

        for x in range(self.xSize):
            for y in range(self.ySize):
                tile = self.world[x][y]
                if tile.get_tile_id() != "-1":
                    tile.set_possibilities(set())
                    potential_tile_ids = [tile.get_tile_id()]
                else:
                    potential_tile_ids = tile.get_possibilities()

                for direction, (nx, ny) in self.get_neighbor_positions(x, y).items():
                    if 0 <= nx < self.xSize and 0 <= ny < self.ySize:
                        neighbor_tile = self.world[nx][ny]
                        neighbor_possibilities = set()
                        for tile_id in potential_tile_ids:
                            neighbor_possibilities.update(self.get_nb_possibilities(tile_id, direction))
                        neighbor_tile.set_possibilities(neighbor_tile.get_possibilities() & neighbor_possibilities)
                        
                        if len(neighbor_tile.get_possibilities()) == 0:
                            return False

        return True

    def create_image(self, tile_imgs):
        new_world_map = Image.new('RGB', (self.xSize * self.tile_size, self.ySize * self.tile_size))
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != '-1':
                    converted_img = cv.cvtColor(tile_imgs[self.world[x][y].get_tile_id()], cv.COLOR_BGR2RGB)
                    tile_img = Image.fromarray(converted_img)
                    new_world_map.paste(tile_img, (x * self.tile_size, y * self.tile_size))
        new_world_map.save('world.png')
        print("Saved image!")
    
    def show_image(self, tile_imgs):
        new_world_map = Image.new('RGB', (self.xSize * self.tile_size, self.ySize * self.tile_size))
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() != '-1':
                    converted_img = cv.cvtColor(tile_imgs[self.world[x][y].get_tile_id()], cv.COLOR_BGR2RGB)
                    tile_img = Image.fromarray(converted_img)
                    new_world_map.paste(tile_img, (x * self.tile_size, y * self.tile_size))
        open_cv_image = np.array(new_world_map)
        open_cv_image = open_cv_image[:, :, ::-1].copy()  # RGB to BGR
        cv.imshow('Current state', open_cv_image)
        cv.waitKey(10)

    def get_nb_possibilities(self, id, direction):
        return set(self.neighbour_rules[id][direction])
    
    def stuck_check(self):
        for x in range(self.xSize):
            for y in range(self.ySize):
                if self.world[x][y].get_tile_id() == "-1" and self.world[x][y].get_entropy() == 0:
                    return True
        return False
    
    def progress_calculator(self):
        n_tiles_left = sum(1 for x in range(self.xSize) for y in range(self.ySize) if self.world[x][y].get_tile_id() == "-1")
        n_tiles_done = self.world_size - n_tiles_left
        return round(100 * (n_tiles_done / self.world_size))
    
    def done_check(self):
        return all(self.world[x][y].get_tile_id() != "-1" and self.world[x][y].get_entropy() == 0 for x in range(self.xSize) for y in range(self.ySize))
    
    def debug_terminal_print(self):
        for y in range(self.ySize):
            for x in range(self.xSize):
                print(self.world[x][y].get_tile_id(), end='\t')
            print()

    def debug_terminal_print_entropy(self):
        for y in range(self.ySize):
            for x in range(self.xSize):
                print(self.world[x][y].get_entropy(), end='\t')
            print()

    def is_empty(self):
        return all(self.world[x][y].get_tile_id() == "-1" for x in range(self.xSize) for y in range(self.ySize))
    
    def get_tile(self, x, y):
        return self.world[x][y]
    
    def set_tile(self, x, y, id):
        self.history.append((x, y, self.world[x][y].get_tile_id()))
        self.world[x][y].set_tile_id(id)


class Tile:
    def __init__(self, x, y, all_tile_ids):
        self.x = x
        self.y = y
        self.entropy = len(all_tile_ids)
        self.possibilities = set(all_tile_ids)
        self.tile_id = "-1"

    def get_entropy(self):
        return self.entropy
    
    def update_entropy(self):
        self.entropy = len(self.possibilities)
    
    def get_possibilities(self):
        return self.possibilities
    
    def set_possibilities(self, new_possibilities):
        self.possibilities = new_possibilities
        self.update_entropy()
    
    def get_tile_id(self):
        return self.tile_id

    def set_tile_id(self, id):
        self.tile_id = id

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

    def update_config(self, tile_folder, neighbour_rules_file, xSize, ySize, show_generation):
        self.tile_folder = tile_folder
        self.neighbour_rules_file = neighbour_rules_file
        self.xSize = xSize
        self.ySize = ySize
        self.show_generation = show_generation

    def load_neighbours_json(self, filename):
        with open(filename, "r") as file:
            tile_neighbours = json.load(file)
            return tile_neighbours       

    def generate(self, world, tile_imgs, update_callback):
        self.progress = world.progress_calculator()
        update_callback(self.progress)
        
        while True:
            if world.stuck_check():
                print("We are stuck!")
                return None
            
            candidate_tiles = world.find_candidate_tiles()

            while True:
                if world is None:
                    print("Hard error bro")

                if world.done_check():
                    return world
                
                if len(candidate_tiles) == 0:
                    print("No more candidate tiles in this branch, going back")
                    return None

                chosen_tile = choice(list(candidate_tiles))
                candidate_tiles.remove(chosen_tile)
                candidate_tile_ids = chosen_tile.get_possibilities()

                print(candidate_tile_ids)

                while candidate_tile_ids:
                    chosen_tile_id = choice(list(candidate_tile_ids))
                    candidate_tile_ids.remove(chosen_tile_id)

                    world.set_tile(chosen_tile.x, chosen_tile.y, chosen_tile_id)
                    if not world.aggressive_collapse():
                        world.revert_last_change()
                        continue
                    
                    self.progress = world.progress_calculator()
                    update_callback(self.progress)

                    if self.show_generation:
                        world.show_image(tile_imgs)

                    break
                else:
                    world.revert_last_change()
                    continue

                break


def main(
        tiles_path: Annotated[str, typer.Option(prompt=False, help="Path to tiles")],
        neighbour_rules_path: Annotated[str, typer.Option(prompt=False, help="Path to neighbours.json")],
        xSize: Annotated[int, typer.Option(prompt=False, help="X size of world")],
        ySize: Annotated[int, typer.Option(prompt=False, help="Y size of world")],
        show_generation: Annotated[bool, typer.Option(prompt=False, help="Show the progress visually")]
    ):
    wave_collapser = WaveCollapser()
    wave_collapser.update_config(tiles_path, neighbour_rules_path, xSize, ySize, show_generation)

    tile_imgs, tile_size = load_tile_imgs(wave_collapser.tile_folder)
    neighbour_rules = wave_collapser.load_neighbours_json(wave_collapser.neighbour_rules_file)

    world = World(xSize, ySize, neighbour_rules, tile_size)
    
    def progress_callback(progress):
        print(f"Progress: {progress}%")

    result = wave_collapser.generate(world, tile_imgs, progress_callback)
    if result:
        result.create_image(tile_imgs)
        print("Generation completed successfully!")
    else:
        print("Generation failed or was interrupted.")


if __name__ == "__main__":
    typer.run(main)
