from typing import Tuple
import numpy as np

from PIL import Image, ImageOps

from src.layout_engine.page_objects.speech_bubble import SpeechBubble
from src import config_file as cfg


class Character(object):
    """
    A class to represent the metadata to render a character

    :param texts: A list of texts from the text corpus to render in this
    bubble

    :type texts: lists

    :param text_indices: The indices of the text from the dataframe
    for easy retrival

    :type text_indices: lists

    :param font: The path to the font used in the bubble

    :type font: str

    :param speech_bubble: The path to the base character file
    used for this bubble

    :type speech_bubble: str

    :param resize_to: The amount of area this text bubble should consist of
    which is a ratio of the panel's area

    :type resize_to: float

    :param location: The location of the top left corner of the character
    on the page

    :type location: list

    :param width: Width of the character

    :type width: float

    :param height: Height of the character

    :type height: float

    :param transforms: A list of transformations to change
    the shape of the character

    :type transforms: list, optional

    :param transform_metadata: Metadata associated with transformations,
    defaults to None

    :type transform_metadata: dict, optional

    :param text_orientation: Whether the text of this character
    is written left to right ot top to bottom

    :type text_orientation: str, optional
    """

    def __init__(self,
                 object_image,
                 width,
                 height,
                 panel_center_coords,
                 location=None,
                 composite_location=None,
                 resize_to=None,
                 transforms=None,
                 transform_metadata=None,
                 ):
        """
        Constructor method
        """
        self.object_image = object_image

        # Location on panel
        if resize_to is not None:
            self.resize_to = resize_to

        self.width = width
        self.height = height

        if location is not None:
            self.location = location

        if composite_location is not None:
            self.composite_location = composite_location
        else:
            self.composite_location = [0, 0]

        if panel_center_coords is not None:
            self.panel_center_coords = panel_center_coords

        self.transform_metadata = {}
        if transform_metadata is not None:
            self.transform_metadata = transform_metadata

        if transforms is None:
            possible_transforms = [
                # "flip horizontal",
                "flip vertical",
                "rotate",
            ]
            # 1 in 50 chance of no transformation
            if np.random.rand() < 0.98:
                self.transforms = list(np.random.choice(
                    possible_transforms,
                    2,
                    replace=False
                ))

                if "rotate" in self.transforms:
                    rotation = np.random.randint(5, 15)
                    self.transform_metadata["rotation_amount"] = rotation

            else:
                self.transforms = []
        else:
            self.transforms = transforms

        self.speech_bubbles = []

    def place_randomly(self, panel):
        """
        A method to place the character in a random location
        inside the panel.

        :param panel: The panel in which the character will
        be placed

        :type  panel: Panel
        """
        # resize to < 40% of panel area
        max_area = panel.area*cfg.object_to_panel_area_max_ratio
        new_area = np.random.random()*(max_area*0.75)  # TODO: Parametrize
        new_area = max_area - new_area
        self.resize_to = new_area

        x_choice, y_choice = panel.get_random_coords()

        self.location = [
            x_choice,
            y_choice
        ]

    def overlaps(self, other):
        """
        A method to check if this Character overlaps with
        another.

        :param other: The other Character

        :type  other: Character

        :return: Whether the Character overlaps.
        :rtype: bool
        """
        self_x1, self_y1 = self.location
        self_x1 /= 2
        self_y1 /= 2
        other_x1, other_y1 = other.location
        other_x1 /= 2
        other_y1 /= 2

        self_height, self_width = self.get_resized()
        other_height, other_width = other.get_resized()

        self_x2 = self_x1 + self_width
        self_y2 = self_y1 + self_height
        other_x2 = other_x1 + other_width
        other_y2 = other_y1 + other_height

        x_inter = max(0, min(self_x2, other_x2) - max(self_x1, other_x1))
        y_inter = max(0, min(self_y2, other_y2) - max(self_y1, other_y1))

        return x_inter > cfg.overlap_offset and y_inter > cfg.overlap_offset

    def get_resized(self):
        if "stretch_x_factor" in self.transform_metadata:
            stretch_x_factor = self.transform_metadata['stretch_x_factor']
        else:
            stretch_x_factor = 0
        if "stretch_y_factor" in self.transform_metadata:
            stretch_y_factor = self.transform_metadata['stretch_y_factor']
        else:
            stretch_y_factor = 0

        w = round(self.width*(1+stretch_x_factor))
        h = round(self.height*(1+stretch_y_factor))
        aspect_ratio = w/h
        new_height = round(np.sqrt(self.resize_to/aspect_ratio))
        new_width = round(new_height * aspect_ratio)
        return new_height, new_width

    def get_random_coords(self):
        # x1, y1 = self.location
        x1, y1 = 0, 0
        x2, y2 = x1 + self.width, y1 + self.height
        if np.random.random() < 0.5:
            x = np.random.randint(x1, x2 // 5)
        else:
            x = np.random.randint(x2 * 4 // 5, x2)
        y = np.random.randint(y1, y2)
        return int(x), int(y)

    def get_center(self):
        x1, y1 = 0, 0
        x2, y2 = x1 + self.width, y1 + self.height
        return x2 // 2, y2 // 2

    def get_area(self):
        return self.width * self.height

    def add_speech_bubble(self, speech_bubble: SpeechBubble):
        # TODO: It only takes into account one bubble
        h, w = speech_bubble.get_resized()
        diameter = int(np.ceil(np.sqrt(np.square(h) + np.square(w))))
        x, y = speech_bubble.location
        cx, cy = speech_bubble.parent_center_coords
        new_x, new_y = x, y
        xmin = x - diameter // 2
        xmax = x + diameter // 2
        ymin = y - diameter // 2
        ymax = y + diameter // 2

        if xmin < 0:
            self.width += -xmin
            self.composite_location[0] += -xmin
            cx += -xmin
            new_x = -xmin

        if xmax > self.width:
            self.width += xmax - self.width

        if ymin < 0:
            self.height += -ymin
            self.composite_location[1] += -ymin
            cy += -ymin
            new_y = -ymin

        if ymax > self.height:
            self.height += ymax - self.height

        speech_bubble.location = new_x, new_y
        speech_bubble.parent_center_coords = (cx, cy)
        self.speech_bubbles.append(speech_bubble)

    def transform_stretch(self, size: Tuple[int, int], factor: float, vertically: bool) -> Tuple[int, int]:
        if vertically:
            new_size = (size[0], round(size[1]*(1+factor)))
        else:
            new_size = (round(size[0]*(1+factor)), size[1])

        return new_size

    def dump_data(self):
        """
        A method to take all the character's relevant data
        and create a dictionary out of it so it can be
        exported to JSON via the Page(Panel) class's
        dump_data method

        :return: Data to be returned to Page(Panel) class's
        dump_data method
        :rtype: dict
        """
        speech_bubbles = [bubble.dump_data() for bubble in self.speech_bubbles]

        data = dict(
            object_image=self.object_image,
            resize_to=self.resize_to,
            location=self.location,
            composite_location=self.composite_location,
            panel_center_coords=self.panel_center_coords,
            width=self.width,
            height=self.height,
            transforms=self.transforms,
            transform_metadata=self.transform_metadata,
            speech_bubbles=speech_bubbles,
        )

        return data

    @classmethod
    def load_data(cls, data: dict):
        character = cls(
            object_image=data['object_image'],
            resize_to=data['resize_to'],
            location=data['location'],
            composite_location=data['composite_location'],
            width=data['width'],
            height=data['height'],
            panel_center_coords=data['panel_center_coords'],
            transforms=data['transforms'],
            transform_metadata=data['transform_metadata'],
        )

        if len(data['speech_bubbles']) > 0:
            for speech_bubble_data in data['speech_bubbles']:
                bubble = SpeechBubble.load_data(speech_bubble_data)
                character.speech_bubbles.append(bubble)

        return character

    def apply_prerendering_transforms(self, composite_image, object_image):
        # Center of object
        w, h = object_image.size
        composite_w, composite_h = composite_image.size
        stretch_x_factor = stretch_y_factor = 1.0
        cx, cy = w/2, h/2
        new_size = new_composite_size = None

        for transform in self.transforms:
            if transform == "stretch x":
                stretch_factor = self.transform_metadata['stretch_x_factor']
                new_size = self.transform_stretch(
                    (w, h), stretch_factor, False)
                new_composite_size = (
                    composite_w + new_size[0] - w, composite_h)
                stretch_x_factor += stretch_factor

            elif transform == "stretch y":
                stretch_factor = self.transform_metadata['stretch_y_factor']
                new_size = self.transform_stretch((w, h), stretch_factor, True)
                new_composite_size = (
                    composite_w, composite_h + new_size[1] - h)
                stretch_y_factor += stretch_factor

            elif transform == "flip horizontal":
                object_image = ImageOps.flip(object_image)

            elif transform == "flip vertical":
                object_image = ImageOps.mirror(object_image)

            if new_size is not None and new_composite_size is not None:
                w, h = new_size
                composite_w, composite_h = new_composite_size

        if new_size is not None and new_composite_size is not None:
            object_image = object_image.resize(new_size)
            composite_image = composite_image.resize(new_composite_size)

        return composite_image, object_image, stretch_x_factor, stretch_y_factor

    def apply_rotation(self, composite_image):
        rotation = self.transform_metadata['rotation_amount']
        composite_image = composite_image.rotate(rotation, expand=True)
        return composite_image

    def apply_resizing(self, composite_image):
        composite_w, composite_h = composite_image.size
        aspect_ratio = composite_w/composite_h
        new_height = max(1, round(np.sqrt(self.resize_to/aspect_ratio)))
        new_width = max(1, round(new_height * aspect_ratio))
        composite_image = composite_image.resize((new_width, new_height))
        return composite_image

    def prevent_bleeding(self, composite_image):
        new_width, new_height = composite_image.size
        xcenter, ycenter = self.location
        # center object in coordinates
        x1 = xcenter - new_width // 2
        y1 = ycenter - new_height // 2
        x2 = x1 + new_width
        y2 = y1 + new_height

        if x2 > cfg.page_width:
            x1 = x1 - (x2-cfg.page_width)
        elif x1 < 0:
            xcenter -= x1
            x1 = 0
        if y2 > cfg.page_height:
            y1 = y1 - (y2-cfg.page_height)
        elif y1 < 0:
            ycenter -= y1
            y1 = 0

        return x1, y1

    def render(self, get_segmentations=False):
        """
        A function to render this character

        :return: The character itself, its mask and its location
        on the page
        :rtype: tuple
        """

        composite_image = Image.new("RGBA", (self.width, self.height))
        object_image = Image.open(self.object_image).convert("RGBA")
        composite_image, object_image, _, _ = self.apply_prerendering_transforms(
            composite_image, object_image)
        composite_images = [composite_image]

        if get_segmentations:
            composite_images += [composite_image.copy()
                                 for _ in range(len(self.speech_bubbles))]

        composite_images[0].paste(
            object_image, self.composite_location, object_image)

        for i, speech_bubble in enumerate(self.speech_bubbles):
            speech_bubble_image, speech_bubble_mask, location = speech_bubble.render()
            # TODO: There's a bug that cuts panels above the caracter, solve it
            # This is a temporal fix
            x, y = location
            x = max(0, x); y = max(0, y)

            if not get_segmentations:
                composite_images[0].paste(speech_bubble_image,
                                    (x, y), speech_bubble_mask)
            else:
                composite_images[i+1].paste(speech_bubble_image,
                                    (x, y), speech_bubble_mask)

        composite_images = [
            self.apply_resizing(ci) for ci in composite_images
        ]

        if "rotate" in self.transforms:
            composite_images = [
            self.apply_rotation(ci) for ci in composite_images
        ]

        x1, y1 = self.prevent_bleeding(composite_images[0])
        self.location = (x1, y1)

        if not get_segmentations:
            return composite_images[0], composite_images[0], self.location
        else:
            return composite_images, composite_images, self.location

