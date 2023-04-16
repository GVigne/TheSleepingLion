import cairo
from math import sqrt
from collections import UserDict
from .errors import InvalidAoEFile
from pathlib import Path

class HexagonDict(UserDict):
    """
    A wrapper around an dictionnary holding the hexagons needed to describe an AOE. It is indexed by tuples,
    which are the coordinates of hexagons, and hold the colors as dictionnaries
    (ie {(0,0): {"red": 0, "green": 0, "blue": 0}})

    Can be serialised and deserialised. When serialised, it will remove unnecessary hexagons (ie blank hexagons)
    to provide the minimum required to describe an AOE: this means the serialized object won't have the same indexes
    as the object.
    """
    @staticmethod
    def CreateFromFile(path_to_aoe: Path):
        """
        Load aoe from file. Will raise uncaught error if the file couldn't be read.
        """
        try:
            hex_from_file = HexagonDict()
            with open(path_to_aoe, "r") as aoe_file:
                for hexagon in aoe_file.readlines():
                    splitted = hexagon.strip().split(" ")
                    rgb = splitted[2].split(",")
                    hex_from_file[(int(splitted[0]), int(splitted[1]))] = {"red": int(rgb[0]), "green": int(rgb[1]), "blue":int(rgb[2])}
            return hex_from_file
        except Exception:
            raise InvalidAoEFile

    def serialize_aoe(self, save_path: Path):
        """
        Save path to target location. Override everything there.
        Also crops the aoe down to a bare minimum (remove unnecessary hexagons).
        """
        with open(save_path, "w") as aoe_file:
            for _, ((x,y), color) in enumerate(self.crop_aoe().items()):
                aoe_file.write(f'{x} {y} {color["red"]},{color["green"]},{color["blue"]} ')
                aoe_file.write("\n")

    def crop_aoe(self):
        """
        Return a HexagonDict equivalent to this one but with
            - no blank hexagons
            - reindexed hexagons to remove additional lines or columns around the aoe.
        """
        stripped_hex = HexagonDict()
        all_y = []
        for _, (coordinate, color) in enumerate(self.data.items()):
            if color["red"] != 255 or color["green"] != 255 or color["blue"] != 255:
                stripped_hex[coordinate] = color
                all_y.append(coordinate[1])

        if len(all_y) == 0:
            # Empty aoe
            return HexagonDict()

        y_offset = min(all_y)
        # y-parity musn't change: if it does, a correction will be required (either on hexagons with odd y, or with even y)
        # Here, we will be removing 1 to the x-coordinate of the hexagons with an odd y. This means shifting to the left
        # every odd line: this is because the odd lines will be reindexed to become even lines.
        parity_offset = 0
        if y_offset%2 == 1:
            parity_offset = 1
        y_shifted = HexagonDict()
        for _, ((x,y), color) in enumerate(stripped_hex.items()):
            if y%2 == 1:
                y_shifted[(x-parity_offset, y-y_offset)] = color
            else:
                y_shifted[(x, y-y_offset)] = color

        # We then remove additional columns because the x coordinates might have changed when removing lines
        x_offset = min([x for (x,_) in y_shifted.keys()])
        result = HexagonDict()
        for _, ((x,y), color) in enumerate(y_shifted.items()):
            result[x-x_offset, y] = color
        return result

class HexagonalGrid:
    """
    A wrapper around a cairo context that draws a hexagonal grid with some hexes colored.

    The convention is even-r horizontal layout (shove even rows right), ie:
    top left edge _> / \/ \/ \/ \
                     | || || || |
                     \ /\ /\ /\ /
    Indexing starts at (0,0).
    See also https://www.redblobgames.com/grids/hexagons/.

    Functions for this class often take a list of points. Each item in the list should be a dictionnary with 5 elements:
        - key "x": x coordinate for the hexagon
        - key "y": y coordinate for the hexagon
        - RGB value with keys "red", "green", "blue". Values should be between 0 and 255.
    This list may be empty.
    """
    def __init__(self, edge_size):
        self.edge_size = edge_size
        self.hexagon_width = 2*self.edge_size*sqrt(3)/2 # sqrt(3)/2 = sin(60)
        self.small_height = self.edge_size*0.5 # 0.5 = cos(60)
        # length of the right-triangle with sides 0.5*hexagon_width and self.edge_size

        self.inner_edge = 0.8*self.edge_size
        self.inner_hexagon_width = 2*self.inner_edge*sqrt(3)/2
        self.inner_small_height = self.inner_edge*0.5

    def get_width(self, hexagons: HexagonDict):
        """
        If I were to draw hexagons, how wide would it be?
        """
        x_coordinates = []
        for _, ((hex_x, hex_y), color) in enumerate(hexagons.items()):
            x_pos, _ = self.coord_to_pos(hex_x, hex_y)
            x_coordinates.append(x_pos)

        min_coord, max_coord = min(x_coordinates), max(x_coordinates)
        return max_coord - min_coord + self.hexagon_width # Coordinates are those of the top left edge

    def get_height(self, hexagons: HexagonDict):
        """
        If I were to draw hexagons, how tall would it be?
        """
        y_coordinates = []
        for _, ((hex_x, hex_y), color) in enumerate(hexagons.items()):
            _, y_pos = self.coord_to_pos(hex_x, hex_y)
            y_coordinates.append(y_pos)

        min_coord, max_coord = min(y_coordinates), max(y_coordinates)
        return max_coord - min_coord + 2*self.small_height + self.edge_size # Coordinates are those of the top left edge

    def coord_to_pos(self, x_coord: int, y_coord: int):
        """
        Given the x and y coordinates for a hexagon, return the position of its top left edge.
        """
        x_pos = x_coord*self.hexagon_width
        if y_coord%2 == 1:
            x_pos = x_pos - self.hexagon_width/2
        y_pos = y_coord*(self.edge_size+ self.small_height)

        return x_pos, y_pos

    def pos_to_coord(self, x_pos: int, y_pos: int, hexagons_to_draw: HexagonDict):
        """
        See technical docs for the documentation.
        It's dark magic.
        """
        # Translation to bring (0,0) to the top left vertex of the hexagon at hexagonal coordinates (0,0)
        internal_x, internal_y, = self.get_origin_pixel_coordinates(hexagons_to_draw)
        x_pos -= internal_x
        y_pos -= internal_y

        q_x = x_pos //round(sqrt(3) * self.edge_size)
        r_x = x_pos - q_x*round(sqrt(3) * self.edge_size)
        q_y = y_pos // round(1.5*self.edge_size)
        r_y = y_pos - q_y*round(1.5*self.edge_size)

        x_res = q_x
        if r_x  > round(sqrt(3) * self.edge_size)/2:
            if q_y % 2 == 0:
                if r_y > self.edge_size and (r_y - self.edge_size) >= -(1/sqrt(3)) * (r_x - self.hexagon_width):
                    x_res += 1
            else:
                if r_y < self.edge_size or (r_y - self.edge_size) <= (1/sqrt(3))*(r_x - self.hexagon_width/2):
                    x_res += 1

        y_res = q_y
        if r_y > self.edge_size:
            if q_y % 2 ==0:
                if r_x <= self.hexagon_width/2:
                    if (r_y - self.edge_size) >= (1/(sqrt(3))) * r_x:
                        y_res +=1
                else:
                    if (r_y - self.edge_size) >= -(1/(sqrt(3)))*(r_x - self.hexagon_width):
                        y_res +=1
            else:
                if r_x <= self.hexagon_width/2:
                    if (r_y - self.edge_size) >= -(1/(sqrt(3)))*(r_x - self.hexagon_width/2):
                        y_res +=1

                else:
                    if (r_y - self.edge_size) >= (1/(sqrt(3)))*(r_x - self.hexagon_width/2):
                        y_res +=1

        return x_res, y_res

    def color_hexagon(self, cr: cairo.Context, rgb:dict = {"red": 0, "green": 0, "blue": 0}):
        """
        Draw the current hexagon with the given color, which must be RGB code between 0 and 255.
        Assumes that the cursor is at the top left corner of the hexagon.

        In Gloomhaven, a hexagon always has a small black border of width 2 pixels, followed by some
        whitish space (RGB = 245,245,245). After those two borders, the hexagon is drawn in a given color.
        """
        cr.move_to(0,0)
        cr.line_to(self.hexagon_width/2, -self.small_height)
        cr.line_to(self.hexagon_width, 0)
        cr.line_to(self.hexagon_width, self.edge_size)
        cr.line_to(self.hexagon_width/2, self.edge_size + self.small_height)
        cr.line_to(0, self.edge_size)
        cr.close_path() # Move back to (0,0)

        cr.set_source_rgb(245/255,245/255,245/255)
        cr.fill_preserve()
        cr.set_source_rgb(0,0,0)
        cr.set_line_width(2)
        cr.stroke()
        # We now have a whitish hexagon with a black border. Now draw the inner hexagon in the given color.

        cr.save()
        diagonal_diff = (1-self.inner_edge/self.edge_size)*self.edge_size # Difference between diagonals of te big white hexagon and the small colored one
        cr.translate(sqrt(3)/2 * diagonal_diff,
                        0.5*diagonal_diff)
        cr.move_to(0,0)
        # Now draw the small hexagon
        cr.line_to(self.inner_hexagon_width/2, -self.inner_small_height)
        cr.line_to(self.inner_hexagon_width, 0)
        cr.line_to(self.inner_hexagon_width, self.inner_edge)
        cr.line_to(self.inner_hexagon_width/2, self.inner_edge + self.inner_small_height)
        cr.line_to(0, self.inner_edge)
        cr.close_path() # Move back to (0,0)

        cr.set_source_rgb(rgb["red"]/255, rgb["green"]/255, rgb["blue"]/255)
        cr.fill()
        cr.restore()

    def get_origin_pixel_coordinates(self, hexagons_to_draw):
        """
        When the Hexagonal Grid draws something at pixel coordinates (0,0), it actually draws a box around the hexagons,
        such that the top left corner of the box fits the pixel coordinate (0,0), ie where the cairo cursor currently is.
        However, due to the even-r convention, a translation may be first made, so that the origin actually fits the
        top left vertex of the hexagon at hexagonal coordinates (0,0).
        This function returns the translation going FROM the reference where the origin has pixel coordinates (0,0) ie cairo's
        cursor position TO the reference where the origin is the top left vertex of the hexagon at hexagonal coordinates (0,0).
        """
        trans_y = self.small_height
        trans_x = 0
        has_odd_hex_first_col = False
        for (x,y), _ in hexagons_to_draw.items():
            if x == 0 and y % 2 == 1:
                has_odd_hex_first_col = True
                break
        if has_odd_hex_first_col:
            trans_x = 0.5*self.hexagon_width
        return trans_x, trans_y

    def draw(self, cr: cairo.Context, hexagons_to_draw: HexagonDict):
        """
        Draw the given hexagons at coordinates (0,0).
        Note: a translation is first made as the origin for the HexagonalGrid is the top left vertex but the hexagons
        at positions (0, 2n+1) (example: hexagon (0,1)) are a bit to the left.
        - On x: translate if a hexagon (0, 2n+1) has to be drawn. If there are no such hexagons, don't translate on the x component
        - On y: translate (always) since hexagons on the first line have a pointy top

        This translation enables the following:
        - W = Hexagonalgrid.get_width(hexagons), H = Hexagonalgrid.get_height(hexagons)
        - Draw a rectangle of size W x H with top left vertex at (0,0)
        - Hexagonalgrid.draw()
        => The hexagons fit in the box and don't overflow.
        """
        cr.save()
        trans_x, trans_y = self.get_origin_pixel_coordinates(hexagons_to_draw)
        cr.translate(trans_x, trans_y)
        cr.move_to(0,0)
        for _, ((hex_x, hex_y), color) in enumerate(hexagons_to_draw.items()):
            cr.save()
            x_pos, y_pos = self.coord_to_pos(hex_x, hex_y)
            cr.translate(x_pos, y_pos)
            cr.move_to(0,0)
            self.color_hexagon(cr, color)
            cr.restore()
        cr.restore()
