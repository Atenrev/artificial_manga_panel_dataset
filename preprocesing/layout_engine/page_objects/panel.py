from re import X
import numpy as np
import skimage

from PIL import Image, ImageDraw
from scipy import ndimage
from preprocesing.layout_engine.page_objects.panel_object import PanelObject
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

    def refresh_size(self):
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

    def get_random_coords(self):
        c, r = zip(*self.coords)
        rr, cc = skimage.draw.polygon(r, c)
        img = np.zeros((cfg.page_height, cfg.page_width), np.uint8)
        img[rr, cc] = 1
        r_structure = (max(int(self.height//5), 1), 1)
        c_structure = (1, max(int(self.width//5), 1))
        img = ndimage.binary_erosion(
            ndimage.binary_erosion(img, structure=np.ones(r_structure)),
            structure=np.ones(c_structure))
        rr, cc = np.where(img == 1)
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
        if self.circular:
            draw_mask.ellipse((*self.x3y3, *self.x1y1), fill=255)
        else:
            draw_mask.polygon(rect, fill=255)

        if np.random.random() < 0.9:
            # Draw outline
            line_rect = rect + (rect[0],)
            draw_img = ImageDraw.Draw(img)
            if self.circular:
                draw_img.ellipse((*self.x3y3, *self.x1y1),
                                 outline=boundary_color,
                                 width=boundary_width
                                 )
            else:
                draw_img.line(line_rect,
                              fill=boundary_color,
                              width=boundary_width,
                              joint="curve"
                              )

        return img, mask
