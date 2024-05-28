import cv2 as cv
import numpy as np
from os import makedirs

from tqdm import tqdm

from typing import Optional
import typer
from typing_extensions import Annotated

from utils import load_world_tileset


class TileExtractor:
    def __init__(self):
        self.progress = 0
        self.is_running = False

        self.filename_path = None
        self.output_path = None
        self.tile_size = None
        self.grid_offset_x = None
        self.grid_offset_y = None
        self.grid_size = None

    def update_config(self, filename_path, output_path, tile_size, grid_offset_x, grid_offset_y, grid_size):
        self.filename_path = filename_path
        self.output_path = output_path
        self.tile_size = tile_size
        self.grid_offset_x = grid_offset_x
        self.grid_offset_y = grid_offset_y
        self.grid_size = grid_size

    # adds a tile to a list. If an accompanying hashset is passed it doesn't add duplicates
    def add_tile(self, tile, tilelist, hashset=None):
        if hashset is None:
            tilelist.append(tile)
        else:
            if hash(str(tile)) not in hashset:
                hashset.add(hash(str(tile)))
                tilelist.append(tile)
        
        
    def write_tiles(self, file_dir, tilelist):
        makedirs(file_dir, exist_ok=True)
        imgname = 0
        for tile in tilelist:
            try:
                cv.imwrite("{f}/{i}.png".format(f=file_dir, i=imgname), tile)
                imgname += 1

            except:
                raise BufferError("Error: Tried to save an empty image.")
        

    # This function creates a black and white mask for the tileset.
    # The color of the grid is auto-detected, after a mask, removing
    # the grid, is created. Then, we detect all contours of the mask.
    # Using these contours, we cut out each tile and save it as a
    # separate image. Note that this only works if the tileset does
    # not contain the color of the mask itself, although we think
    # this is safe to assume.
    # The grid also needs to go around the border of the whole image.
    # We use the top left pixel to detect the color of the mask.
    def separate_grid(self, tileset, output_path, update_callback):
        # Detect grid color. Legacy: use the pixel at (0,0) to determine the grid color.
        gridcolor = tileset[0,0]

        # # Detect grid color. Modern: use the most-occurring color to determine the grid color.
        # flattened_tileset = tileset.reshape(-1, 3)

        # unique_color, counts = np.unique(flattened_tileset, axis=0, return_counts=True)
        # max_count_index = np.argmax(counts)

        # gridcolor = unique_color[max_count_index]

        # Create the mask.
        mask = np.all(tileset == gridcolor, axis=-1)
        mask = ~mask
        color_mask = mask.astype(np.uint8)
        color_mask *= 255

        # Save mask to file to inspect TODO: doesn't work now anymore with new filename conventions
        # makedirs("./masks", exist_ok=True)
        # cv.imwrite("./masks/{f}_mask.png".format(f=output_path), color_mask)

        # Detect contours
        contours, hierarchy = cv.findContours(image=color_mask, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_SIMPLE)

        # First pass: check most common area
        area_dict = {}
        for c in contours:
            area = cv.contourArea(c)
            if area not in area_dict:
                area_dict[area] = 1
            else:
                area_dict[area] += 1

        # Determine the standard area: the most-occurring area of tiles.
        # We discard tiles with other dimensions, as they will not fit.
        standard_area = max(zip(area_dict.values(), area_dict.keys()))[1]

        tiles_list = []
        tiles_hash = set()

        n_contours_done = 0

        # For all contours, cut out tile
        for c in tqdm(contours):
            n_contours_done += 1
            self.progress = round(100 * (n_contours_done / len(contours)))
            print("Progress of worker:", self.progress)
            update_callback(self.progress)

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

            # Check if tile is a square. If not, we skip the tile.
            if maxX - minX != maxY - minY:
                continue

            # If area of contour does not match standard area, we skip this tile.
            # We may lose some tiles, bat that's a sacrifice we're willing to make. Tey would probably not fit with the
            # other tiles anyway.
            if cv.contourArea(c) != standard_area:
                continue

            box_image = tileset[minY : maxY+1, minX: maxX+1]

            # Hash the tile to ensure we only save unique tiles
            self.add_tile(box_image, tiles_list, tiles_hash)
        
        
        self.write_tiles(output_path, tiles_list)


    # "Hardcoded" tile extraction, for tilesets that contain no grid lines.
    # tile_size denotes the standard size of the tiles (16 means 16x16).
    # Offset is for the cases where there is a border around the entire tileset,
    # but no grid.
    def fixed_offset_extraction(self, tileset, output_path, tile_size, grid_offset_x, grid_offset_y, grid_size):
        x = 0
        y = 0
        tilesetX_size = tileset.shape[:2][1]
        tilesetY_size = tileset.shape[:2][0]
        tiles_list = []
        tiles_hash = set()
        print(tilesetX_size, tilesetY_size)
        for x in range(grid_offset_x, tilesetX_size, tile_size+grid_size):
            for y in range(grid_offset_y, tilesetY_size, tile_size+grid_size):
                box_image = tileset[y : y+tile_size, x : x+tile_size]
                self.add_tile(box_image, tiles_list, tiles_hash)

        self.write_tiles(output_path, tiles_list)
        


    def run(self, update_callback):
        self.is_running = True
        #load tileset
        tileset = load_world_tileset(self.filename_path)

        typer.echo(f"Filename path: {self.filename_path}")
        typer.echo(f"Output path: {self.output_path}")
        typer.echo(f"Tile size: {self.tile_size}")
        typer.echo(f"Grid offset X: {self.grid_offset_x}")
        typer.echo(f"Grid offset Y: {self.grid_offset_y}")
        typer.echo(f"Grid size: {self.grid_size}")

        if self.grid_offset_x is None and self.grid_offset_y is None and self.tile_size is None:
            self.separate_grid(tileset, self.output_path, update_callback)
        else:
            self.fixed_offset_extraction(tileset, self.output_path, self.tile_size, self.grid_offset_x, self.grid_offset_y, self.grid_size)
        self.is_running = False

def main(
        filename_path: Annotated[str, typer.Argument(help="The filename of the tileset as a .png (or other image file).")],
        output_path: Annotated[str, typer.Argument(help="The folder name in which the tileset should be extracted as separate image files.")],
        tile_size: Annotated[Optional[int], typer.Option(help="The tile size dimension in pixels. Both horizontal and vertical.")] = None,
        grid_offset_x: Annotated[Optional[int], typer.Option(help="The offset at which the leftmost column of tiles starts, in pixels.")] = None,
        grid_offset_y: Annotated[Optional[int], typer.Option(help="The offset at which the topmost row of tiles starts, in pixels.")] = None,
        grid_size: Annotated[Optional[int], typer.Option(help="The size of the grid; the width of the lines separating tiles, in pixels.")] = None
):
    tileExtractor = TileExtractor()
    tileExtractor.update_config(filename_path, output_path, tile_size, grid_offset_x, grid_offset_y, grid_size)
    def update_callback(progress):
        pass
        # This is an empty function to make sure the gui can properly connect and pass its own callback function
        # print(f"Tile extraction progress: {progress}%") # Optional extra report if you don't like tqdm
    tileExtractor.run(update_callback)

if __name__=="__main__":
    typer.run(main)
