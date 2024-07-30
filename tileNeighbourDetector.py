import cv2 as cv
import numpy as np
import os
from copy import deepcopy
from tqdm import tqdm
import json
import climage

import typer
from typing_extensions import Annotated
app = typer.Typer(pretty_exceptions_enable=False)

from utils import load_world_tileset, load_tile_imgs

np.zeroes = np.zeros # Important


class TileRulesDetector:
    def __init__(self):
        self.progress = 0
        self.is_running = False

        self.tile_folder = None
        self.world_name = None
        self.sections_folder = None
        self.output_file = None

    def update_config(self, tile_folder: str, world_name: str, sections_folder: str, output_file: str) -> None:
        self.tile_folder = tile_folder
        self.world_name = world_name
        self.sections_folder = sections_folder
        self.output_file = output_file

    # uses contours to extract the different areas of an overworld file
    # returns seperate sections of the world
    def split_sections(self, world, size):
        # Detect grid color using top-left pixel
        gridcolor = world[0,0]

        # Create the mask
        mask = np.all(world == gridcolor, axis=-1)
        mask = ~mask
        color_mask = mask.astype(np.uint8)
        color_mask *= 255
        
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

            # Check if world section is divisible by tile size and if
            # world section contains at least 16 tiles (4 by 4).
            if (box_image.shape[0] % size == 0 and box_image.shape[0] >= size*4) and (box_image.shape[1] % size == 0 and box_image.shape[1] >= size*4):
                world_sections.append(box_image)
        
        return world_sections

    # Check if given tile exists and if it has the correct size
    def validate_supplied_tile(self, tile_nr: int, tile_folder: str, tile_size: int) -> bool:
        full_path = os.path.join("./", tile_folder, str(tile_nr) + ".png")
        if not os.path.exists(full_path):
            print("Path of the file is invalid")
            return False
        try:
            imgfile = cv.imread(full_path)
            if not (imgfile.shape[0] == tile_size and imgfile.shape[1] == tile_size):
                print("Size of the image is invalid")
                return False
            return True
        except:
            print("not a valid img")
            return False

    # Add new tile specified during manual rule addition   
    def add_new_tile(self, raw_img_data: str, tile_folder: str) -> int:
        imgname = ""
        # The current highest tile ID, + 1 for the new tile
        new_tile_nr = sorted([int(n.split('.')[0]) for n in os.listdir(tile_folder)])[-1] + 1
        imgname = str(new_tile_nr)
        cv.imwrite("{f}/{i}.png".format(f=tile_folder, i=imgname), raw_img_data)
        return new_tile_nr

    # Gets (a subsection of) the world and returns the representation of the tiles as ids as an 2d-array
    def build_section_ids(self, world_section: np.array, tileset: dict, tile_size: int, specified_tiles: list, tile_folder: str) -> np.array:
        # Create an array for the tile ids we find. Initialize on -1 for tiles we did not find.
        section_numbered = np.full((int(world_section.shape[0]/tile_size), int(world_section.shape[1]/tile_size)), -1)

        # For each tile, we match it in the world (section).
        for id, tile in tileset.items():
            # Create a copy to draw the match on
            res = cv.matchTemplate(world_section, tile, cv.TM_SQDIFF_NORMED)
            threshold = 0.01
            loc = np.where(res <= threshold)
            for m in zip(*loc[::-1]):
                # only take into account matches coinciding with stride length
                if m[0] % tile_size == 0 and m[1] % tile_size == 0:
                    section_numbered[int(m[1]/tile_size)][int(m[0]/tile_size)] = id

        unknown_imgs = [] 
        skip_section = False

        for y in range(section_numbered.shape[0]):
            for x in range(section_numbered.shape[1]):
                if section_numbered[y][x] == -1:
                    current_subsection = world_section[(y*tile_size):(y+1)*tile_size, (x*tile_size):(x+1)*tile_size]
                    specified_tiles_idx = -1
                    specified_earlier = False

                    # check if file has been manually specified before
                    for image_idx in range(len(specified_tiles[0])):
                        
                        if specified_tiles[0][image_idx] == hash(str(current_subsection)): #compare image with current subsection
                            print("match: ", image_idx)
                            specified_tiles_idx = specified_tiles[1][image_idx] # get matching manually set tile number
                            print(climage.convert_array(cv.cvtColor(current_subsection, cv.COLOR_BGR2RGB), is_unicode=True) )
                            specified_earlier = True                    

                    if specified_earlier:
                        print("specified earlier")
                        print(specified_tiles_idx)
                        section_numbered[y][x] = specified_tiles_idx
                    elif not skip_section:
                        print("new tile")
                        
                        unknown_imgs.append(current_subsection)
                        output = climage.convert_array(cv.cvtColor(world_section, cv.COLOR_BGR2RGB), is_unicode=True) 
                        print(output)
                        output = climage.convert_array(cv.cvtColor(current_subsection, cv.COLOR_BGR2RGB), is_unicode=True) 
                        print(output)
                        print("(you might need to scroll up)")
                        tile_nr = input("\nPlease type number of the tile to use here (without file extension e.g. type '1' if you want '1.png').\n" +
                                        "Leave empty if you want to ignore this tile. Type 'skip' (or 's') to ignore all unknown tiles in this section \n" +
                                        "Type 'new' (or 'n') to add the currently shown tile as a new image to the tileset: ").lower()
                        print(tile_nr)
                        # ask to link unknown tile to existing tile
                        while not (tile_nr == "" or tile_nr.isdigit() or tile_nr=="skip" or tile_nr=="s" or tile_nr=="new" or tile_nr=="n"):
                            tile_nr = input("Wrong tilename. \n Please try again:")
                        
                        # tile linked to existing image
                        if not ((tile_nr == "" or tile_nr == "-1") or (tile_nr=="skip" or tile_nr=="s") or (tile_nr=="new" or tile_nr=="n")):
                            if self.validate_supplied_tile(tile_nr, tile_folder, tile_size):
                                section_numbered[y][x] = int(tile_nr)
                                specified_tiles[0].append(hash(str(current_subsection)))
                                specified_tiles[1].append(int(tile_nr))
                            else:
                                print("Weird input!")
                        else: # other valid inputs
                            if (tile_nr == "" or tile_nr == "-1"):
                                print("Ignored current tile")
                                section_numbered[y][x] = -1
                                specified_tiles[0].append(hash(str(current_subsection)))
                                specified_tiles[1].append(-1)
                            elif (tile_nr=="skip" or tile_nr=="s"):
                                print("Skipping all unknown tiles in section")
                                section_numbered[y][x] = -1
                                specified_tiles[0].append(hash(str(current_subsection)))
                                specified_tiles[1].append(-1)
                                skip_section = True
                            elif (tile_nr=="new" or tile_nr=="n"):
                                print("Adding extra tile missing from original tileset...")                            
                                specified_tiles[0].append(hash(str(current_subsection)))
                                specified_tiles[1].append(self.add_new_tile(current_subsection, tile_folder))

                    elif skip_section==True:
                        already_in_st = False
                        for image_idx in range(len(specified_tiles[0])):
                            if specified_tiles[0][image_idx] == hash(str(current_subsection)):
                                specified_tiles_idx = specified_tiles[1][image_idx]
                                already_in_st = True
                        if not already_in_st:
                            specified_tiles[0].append(hash(str(current_subsection)))
                            specified_tiles[1].append(-1)
                        if already_in_st:
                            section_numbered[y][x] = specified_tiles_idx

        return section_numbered


    def add_sect_to_dict(self, section_numbered: np.array, neighbourdict: dict) -> None:
        for row in range(section_numbered.shape[0]):
            for col in range(section_numbered.shape[1]):
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
                    # add area[row+1][col] (down)
                    neighbourdict[selfTile]["down"].add(str(section_numbered[row+1][col]))
                if col-1 > 0 and section_numbered[row][col-1] != -1:
                    # add area[row][col-1] (left)
                    neighbourdict[selfTile]["left"].add(str(section_numbered[row][col-1]))


    def run(self, update_callback: callable) -> None:
        self.is_running = True
        
        typer.echo(f"Separate tiles tileset folder: {self.tile_folder}")
        typer.echo(f"World file: {self.world_name}")
        typer.echo(f"World sections folder: {self.sections_folder}")
        typer.echo(f"Output JSON file: {self.output_file}")

        tileset, tile_size = load_tile_imgs(self.tile_folder)
        world = load_world_tileset(self.world_name)

        neighbourdict = {}

        world_sections = self.split_sections(world, tile_size)
        sec = 0
        
        os.makedirs(self.sections_folder, exist_ok=True)
        for s in world_sections:
            cv.imwrite("{w}/section_{sec}.png".format(w=self.sections_folder, sec=sec), s)
            sec += 1

        neighbourdict = {}
        specified_tiles = [
            [], #image data to match future occurences
            []  #tile_nr
        ]

        print("Matching tiles in each world section...")
        n_sections_done = 0
        for section in tqdm(world_sections):
            # Progress report
            n_sections_done += 1
            self.progress = round(100 * (n_sections_done / len(world_sections)))
            update_callback(self.progress)

            section_numbered = self.build_section_ids(section, tileset, tile_size, specified_tiles, self.tile_folder)
            self.add_sect_to_dict(section_numbered, neighbourdict)
            
        #convert sets to lists for json dumping
        for tile in neighbourdict.keys():
            for direction in neighbourdict[tile].keys():
                neighbourdict[tile][direction] = list(neighbourdict[tile][direction])
        if not self.output_file.lower().endswith(".json"):
            self.output_file += ".json"
        with open(self.output_file, "w") as f:
            json.dump(neighbourdict, f, indent=4)

        self.is_running = False


# This part is to make sure the script can still be called separately without the UI.
@app.command()
def main(
        tile_folder: Annotated[str, typer.Argument(help="The folder containing all separate tile images.")],
        world_name: Annotated[str, typer.Argument(help="The image file containing the original world from which neighbor rules should be inferred.")],
        sections_folder: Annotated[str, typer.Argument(help="The folder in which all separate world sections extracted from the world image file should be saved.")],
        output_file: Annotated[str, typer.Argument(help="The output JSON file containing the rules of what tiles can have which neighbors.")]
) -> None:
    tileRulesDetector = TileRulesDetector()
    tileRulesDetector.update_config(tile_folder, world_name, sections_folder, output_file)
    def update_callback(progress):
        pass
        # This is an empty function to make sure the gui can properly connect and pass its own callback function
        # print(f"Tile extraction progress: {progress}%") # Optional (extra) report if you don't like tqdm
    tileRulesDetector.run(update_callback)

if __name__=="__main__":
    # typer.run(main)
    app()
