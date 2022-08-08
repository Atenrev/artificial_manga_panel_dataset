import numpy as np
import skimage

from PIL import Image, ImageDraw

from preprocesing.layout_engine.page_objects.panel_object import PanelObject
from ... import config_file as cfg
from ..helpers import (add_noise, blank_image,
                      crop_image_only_outside, get_leaf_panels)
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

    def __init__(self,
                 coords,
                 name,
                 parent,
                 orientation,
                 children=[],
                 non_rect=False):
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

        self.width = float((self.x2y2[0] - self.x1y1[0]))
        self.height = float((self.x3y3[1] - self.x2y2[1]))

        self.area = float(self.width*self.height)

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
        self.speech_bubbles = []

        self.panel_objects = []

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

    def get_random_coords(self):
        r, c = zip(*self.coords)
        x, y = skimage.draw.polygon(r, c)
        random_index = np.random.choice(list(range(len(x))))
        random_point = (x[random_index], y[random_index])
        return int(random_point[0]), int(random_point[1])

    def get_center(self):
        r, c = zip(*self.coords)
        x, y = skimage.draw.polygon(r, c)
        return int(np.mean(x)), int(np.mean(y))

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

    def get_child(self, idx):
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
        panel_objects = [panel_object.dump_data() for panel_object in self.panel_objects]
        data = dict(
            name=self.name,
            coordinates=self.coords,
            orientation=self.orientation,
            children=children_rec,
            non_rect=self.non_rect,
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

        if len(data['speech_bubbles']) > 0:
            for speech_bubble in data['speech_bubbles']:

                transform_metadata = speech_bubble['transform_metadata']
                bubble = SpeechBubble(
                    texts=speech_bubble['texts'],
                    text_indices=speech_bubble['text_indices'],
                    font=speech_bubble['font'],
                    speech_bubble=speech_bubble['speech_bubble'],
                    writing_areas=speech_bubble['writing_areas'],
                    resize_to=speech_bubble['resize_to'],
                    location=speech_bubble['location'],
                    panel_center_coords=speech_bubble['panel_center_coords'],
                    width=speech_bubble['width'],
                    height=speech_bubble['height'],
                    orientation=speech_bubble['orientation'],
                    transforms=speech_bubble['transforms'],
                    transform_metadata=transform_metadata,
                    text_orientation=speech_bubble['text_orientation']
                )

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
                    non_rect=child['non_rect']
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
            # img_array = np.asarray(img)
            # crop_array = crop_image_only_outside(img_array)
            # img = Image.fromarray(crop_array)
        else:
            img = Image.new("RGB", cfg.page_size, 255)

        # Resize it to the page's size as a simple
        # way to crop differnt parts of it

        # TODO: Figure out how to do different types of
        # image crops for smaller panels
        w_rev_ratio = cfg.page_width/img.size[0]
        h_rev_ratio = cfg.page_height/img.size[1]

        img = img.resize(
            (round(img.size[0]*w_rev_ratio),
                round(img.size[1]*h_rev_ratio))
        )

        # Create a mask for the panel illustration
        mask = Image.new("L", cfg.page_size, 0)
        draw_mask = ImageDraw.Draw(mask)

        # On the mask draw and therefore cut out the panel's
        # area so that the illustration can be fit into
        # the page itself
        draw_mask.polygon(rect, fill=255)

        if np.random.random() < 0.9:
            # Draw outline
            line_rect = rect + (rect[0],)
            draw_img = ImageDraw.Draw(img)
            draw_img.line(line_rect,
                            fill=boundary_color,
                            width=boundary_width,
                            joint="curve"
                            )

        return img, mask
