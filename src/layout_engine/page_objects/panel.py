from re import X
from typing import List, Tuple
import numpy as np
import skimage

from PIL import Image, ImageDraw
from scipy import ndimage
from src.layout_engine.page_objects.panel_object import PanelObject
from src.layout_engine.helpers import crop_image_only_outside
from ... import config_file as cfg
from .speech_bubble import SpeechBubble


class Panel(object):
    """
    A class to encapsulate a panel of the manga page.
    Since the script works in a parent-child relationship
    where each panel child is an area subset of some parent panel,
    some panels aren't leaf nodes and thus not rendered.

    :param coords: Coordinates of the boundary of the panel

    :type coords: list

    :param name: Unique name for the panel

    :type name: str

    :param parent: The panel which this panel is a child of

    :type parent: Panel

    :param orientation: Whether the panel consists of lines that are vertically
    or horizotnally oriented in reference to the page

    :type orientation: str

    :children: Children panels of this panel

    :type children: list

    :non_rect: Whether the panel was transformed to be non rectangular
    and thus has less or more than 4 coords

    :type non_rect: bool, optional
    """

    next_panel_id: int = 0

    def __init__(self,
                 coords,
                 name,
                 parent,
                 orientation,
                 children=[],
                 non_rect=False,
                 circular=None):
        """
        Constructor methods
        """

        coords = [tuple(c) for c in coords]

        self.x1y1 = coords[0]
        self.x2y2 = coords[1]
        self.x3y3 = coords[2]
        self.x4y4 = coords[3]

        self.lines = [
            (self.x1y1, self.x2y2),
            (self.x2y2, self.x3y3),
            (self.x3y3, self.x4y4),
            (self.x4y4, self.x1y1)
        ]

        self.name = name
        self.parent = parent

        self.coords = coords
        self.non_rect = non_rect

        if circular is not None:
            self.circular = circular
        else:
            self.circular = False

        self.refresh_size()

        area_proportion = round(self.area/(cfg.page_height*cfg.page_width), 2)
        self.area_proportion = area_proportion

        if len(children) > 0:
            self.children = children
        else:
            self.children = []

        self.orientation = orientation

        # Whether or not this panel has been transformed by slicing into two
        self.sliced = False

        # Whether or not to render this panel
        self.no_render = False

        # Image from the illustration dataset which is
        # the background of this panel
        self.image = None

        # A list of speech bubble objects to render around this panel
        self.speech_bubbles : List[SpeechBubble] = []

        self.panel_objects : List[PanelObject] = []

    def get_polygon(self):
        """
        Return the coords in a format that can be used to render a polygon
        via Pillow

        :return: A tuple of coordinate tuples of the polygon's vertices
        :rtype: tuple
        """
        if self.non_rect:
            return tuple(self.coords)
        else:

            return (
                self.x1y1,
                self.x2y2,
                self.x3y3,
                self.x4y4,
                self.x1y1
            )

    def get_bounding_box(self) -> List[int]:
        xmin = np.inf
        xmax = 0
        ymin = np.inf
        ymax = 0

        for coord in self.coords:
            x, y = coord

            if x < xmin:
                xmin = x
            elif x > xmax:
                xmax = x

            if y < ymin:
                ymin = y
            elif y > ymax:
                ymax = y

        return [int(xmin), int(ymin), int(xmax), int(ymax)]

    def refresh_size(self):
        xmin, ymin, xmax, ymax = self.get_bounding_box()
        self.width = float(xmax - xmin)
        self.height = float(ymax - ymin)
        self.area = float(self.width*self.height)

    def refresh_coords(self):
        """
        When changes are made to the xy coordinates variables directly
        this function allows you to refresh the coords variable with
        the changes
        """
        self.coords = [
            self.x1y1,
            self.x2y2,
            self.x3y3,
            self.x4y4,
            self.x1y1
        ]
        self.refresh_size()

    def refresh_drawable_area(self):
        c, r = zip(*self.coords)
        c = [e-1 for e in c]; r = [e-1 for e in r]
        rr, cc = skimage.draw.polygon(r, c)
        img = np.zeros((cfg.page_height, cfg.page_width), np.uint8)
        img[rr, cc] = 1
        r_structure = (max(int(self.height//5), 1), 1)
        c_structure = (1, max(int(self.width//5), 1))
        img = ndimage.binary_erosion(
            ndimage.binary_erosion(img, structure=np.ones(r_structure)),
            structure=np.ones(c_structure))
        self.drawable_area = np.where(img == 1)

    def get_random_coords(self):
        rr, cc = self.drawable_area
        random_index = np.random.choice(list(range(len(rr))))
        random_point = (rr[random_index], cc[random_index])
        return int(random_point[1]), int(random_point[0])

    def get_center(self):
        r, c = zip(*self.coords)
        x, y = skimage.draw.polygon(r, c)
        return int(np.mean(x)), int(np.mean(y))

    def get_area(self):
        return self.area

    def refresh_vars(self):
        """
        When changes are made to the xy coordinates directly
        this function allows you to refresh the x1y1... variable with
        the changes
        """

        self.x1y1 = self.coords[0]
        self.x2y2 = self.coords[1]
        self.x3y3 = self.coords[2]
        self.x4y4 = self.coords[3]

    def add_child(self, panel):
        """
        Add child panels

        :param panel: A child panel to the current panel

        :type panel: Panel
        """
        self.children.append(panel)

    def add_children(self, panels):
        """
        Method to add multiple children at once

        :param panels: A list of Panel objects

        :type panels: list
        """

        for panel in panels:
            self.add_child(panel)

    def get_child(self, idx) -> 'Panel':
        """
        Get a child panel by index

        :param idx: Index of a child panel

        :type idx: int

        :return: The child at the idx
        :rtype: Panel
        """
        return self.children[idx]

    def dump_data(self):
        """
        A method to take all the Panel's relevant data
        and create a dictionary out of it so it can be
        exported to JSON via the Page(Panel) class's
        dump_data method

        :return: A dictionary of the Panel's data
        :rtype: dict
        """

        # Recursively dump children
        if len(self.children) > 0:
            children_rec = [child.dump_data() for child in self.children]
        else:
            children_rec = []

        speech_bubbles = [bubble.dump_data() for bubble in self.speech_bubbles]
        panel_objects = [panel_object.dump_data()
                         for panel_object in self.panel_objects]
        data = dict(
            name=self.name,
            coordinates=self.coords,
            orientation=self.orientation,
            children=children_rec,
            non_rect=self.non_rect,
            circular=self.circular,
            sliced=self.sliced,
            no_render=self.no_render,
            image=self.image,
            speech_bubbles=speech_bubbles,
            panel_objects=panel_objects,
        )

        return data

    def load_data(self, data):
        """
        This method reverses the dump_data function and
        load's the metadata of the panel from the subsection
        of the JSON file that has been loaded

        :param data: A dictionary of this panel's data

        :type data: dict
        """

        self.sliced = data['sliced']
        self.no_render = data['no_render']
        self.image = data['image']
        self.circular = data['circular']

        if len(data['speech_bubbles']) > 0:
            for speech_bubble_data in data['speech_bubbles']:
                bubble = SpeechBubble.load_data(speech_bubble_data)
                self.speech_bubbles.append(bubble)

        if len(data['panel_objects']) > 0:
            for panel_object_data in data['panel_objects']:
                panel_object = PanelObject.load_data(panel_object_data)
                self.panel_objects.append(panel_object)

        # Recursively load children
        children = []
        if len(data['children']) > 0:
            for child in data['children']:
                panel = Panel(
                    coords=child['coordinates'],
                    name=child['name'],
                    parent=self,
                    orientation=child['orientation'],
                    non_rect=child['non_rect'],
                    circular=child['circular']
                )

                panel.load_data(child)
                children.append(panel)

        self.children = children

    def render(self, boundary_width, boundary_color):
        # Panel coords
        rect = self.get_polygon()

        # Open the illustration to put within panel
        if self.image is not None:
            img = Image.open(self.image).convert("RGB")
            # Clean it up by cropping the black areas
            crop_array = crop_image_only_outside(img)
            img = Image.fromarray(crop_array)
        else:
            img = Image.new("RGBA", cfg.page_size, (0,0,0,0))

        bounding_box = self.get_bounding_box()
        composite_img = Image.new("RGBA", cfg.page_size, (0, 0, 0, 0))

        image_h = int(self.height)
        # height_offset = int(self.height // 5)

        # if not self.non_rect:
        #     gap = max(height_offset-np.random.randint(4, 48), 0)
        #     draw_img = ImageDraw.Draw(composite_img)
        #     draw_img.rectangle(
        #         (bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[1] + gap),
        #         fill='white', outline=boundary_color)
        #     image_h -= height_offset
        #     bounding_box[1] += height_offset

        # reisize panel
        w, h = img.size
        aspect_ratio = w/h
        poly_aspect_ratio = self.width/image_h
        crop_width = crop_heigth = 0

        if poly_aspect_ratio < aspect_ratio:
            new_height = image_h
            new_width = round(new_height * aspect_ratio)

            if new_width > self.width:
                crop_width = np.random.randint(0, new_width - int(self.width))
        else:
            new_width = int(self.width)
            new_height = round(new_width / aspect_ratio)

            if new_height > image_h:
                crop_heigth = np.random.randint(0, new_height - image_h)

        img = img.resize((new_width, new_height))
        img = img.crop((
            crop_width,
            crop_heigth,
            int(self.width) + crop_width,
            image_h + crop_heigth
        ))

        composite_img.paste(img, tuple(bounding_box))

        # Create a mask for the panel illustration
        mask = Image.new("L", cfg.page_size, 0)
        draw_mask = ImageDraw.Draw(mask)

        # On the mask draw and therefore cut out the panel's
        # area so that the illustration can be fit into
        # the page itself
        if self.circular:
            draw_mask.ellipse((*self.x3y3, *self.x1y1), fill=255)
        else:
            draw_mask.polygon(rect, fill=255)

        if np.random.random() < 0.9:
            # Draw outline
            line_rect = list(rect) + [rect[0]]
            draw_img = ImageDraw.Draw(composite_img)

            if self.circular:
                draw_img.ellipse((*self.x3y3, *self.x1y1),
                                 outline=boundary_color,
                                 width=boundary_width
                                 )
                draw_mask.ellipse((*self.x3y3, *self.x1y1),
                                  outline=255,
                                  width=boundary_width
                                  )
            else:
                # if not self.non_rect:
                #     line_rect = (
                #         self.x1y1,
                #         self.x2y2,
                #         (self.x3y3[0], self.x3y3[1] + height_offset),
                #         (self.x4y4[0], self.x4y4[1] + height_offset),
                #         self.x1y1,
                #         self.x1y1,
                #     )

                draw_img.line(line_rect,
                              fill=boundary_color,
                              width=boundary_width,
                              joint="curve"
                              )
                draw_mask.line(line_rect,
                               fill=255,
                               width=boundary_width,
                               joint="curve"
                               )

        final_mask = Image.new("RGBA", cfg.page_size, (0, 0, 0, 0))
        final_mask.paste(composite_img, mask=mask)
        return composite_img, final_mask
