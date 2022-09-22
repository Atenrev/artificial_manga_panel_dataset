import numpy as np
import cjkwrap

from PIL import Image, ImageDraw, ImageFont, ImageOps
from ... import config_file as cfg


class SpeechBubble(object):
    """
    A class to represent the metadata to render a speech bubble

    :param texts: A list of texts from the text corpus to render in this
    bubble

    :type texts: lists

    :param text_indices: The indices of the text from the dataframe
    for easy retrival

    :type text_indices: lists

    :param font: The path to the font used in the bubble

    :type font: str

    :param speech_bubble: The path to the base speech bubble file
    used for this bubble

    :type speech_bubble: str

    :param writing_areas: The areas within the bubble where it is okay
    to render text

    :type writing_areas: list

    :param resize_to: The amount of area this text bubble should consist of
    which is a ratio of the panel's area

    :type resize_to: float

    :param location: The location of the top left corner of the speech bubble
    on the page

    :type location: list

    :param width: Width of the speech bubble

    :type width: float

    :param height: Height of the speech bubble

    :type height: float

    :param transforms: A list of transformations to change
    the shape of the speech bubble

    :type transforms: list, optional

    :param transform_metadata: Metadata associated with transformations,
    defaults to None

    :type transform_metadata: dict, optional

    :param text_orientation: Whether the text of this speech bubble
    is written left to right ot top to bottom

    :type text_orientation: str, optional
    """

    def __init__(self,
                 texts,
                 text_indices,
                 font,
                 speech_bubble,
                 writing_areas,
                 width,
                 height,
                 orientation,
                 parent_center_coords,
                 location=None,
                 resize_to=None,
                 transforms=None,
                 transform_metadata=None,
                 text_orientation=None):
        """
        Constructor method
        """

        self.texts = texts
        # Index of dataframe for the text
        self.text_indices = text_indices
        self.font = font
        self.speech_bubble = speech_bubble
        self.writing_areas = writing_areas

        # Location on panel
        if resize_to is not None:
            self.resize_to = resize_to
        self.width = width
        self.height = height
        self.orientation = orientation

        if location is not None:
            self.location = location

        if parent_center_coords is not None:
            self.parent_center_coords = parent_center_coords

        self.transform_metadata = {}
        if transform_metadata is not None:
            self.transform_metadata = transform_metadata

        if transforms is None:
            possible_transforms = [
                "rotate",
                "stretch x",
                "stretch y",
            ]

            # If it has no orientation
            if type(self.orientation) is float:
                possible_transforms += [
                    "flip horizontal",
                    "flip vertical"
                ]

            # 1 in 50 chance of no transformation
            if np.random.rand() < 0.98:
                self.transforms = list(np.random.choice(
                    possible_transforms,
                    2,
                    replace=False
                ))

                # 1 in 20 chance of inversion
                if np.random.rand() < 0.05:
                    self.transforms.append("invert")

                # TODO: Parametrize stretching
                if "stretch x" in self.transforms:
                    # Up to 30% stretching
                    factor = np.random.random()*0.3
                    self.transform_metadata["stretch_x_factor"] = factor
                if "stretch y" in self.transforms:
                    factor = np.random.random()*0.3
                    self.transform_metadata["stretch_y_factor"] = factor

                if "rotate" in self.transforms:
                    rotation = np.random.randint(5, 15)
                    self.transform_metadata["rotation_amount"] = rotation

            else:
                self.transforms = []
        else:
            self.transforms = transforms

        if text_orientation is None:
            # 1 in 100 chance
            if np.random.random() < 1.0:  # 0.01
                self.text_orientation = "ltr"
            else:
                self.text_orientation = "ttb"
        else:
            self.text_orientation = text_orientation

        min_font_size = cfg.min_font_size
        max_font_size = cfg.max_font_size
        # Change this, make it dynamic
        self.font_size = np.random.randint(min_font_size,
                                           max_font_size
                                           )

    def place_randomly(self, parent, min_ratio: float = 0.3, max_ratio: float = 1.0):
        """
        A method to place the SpeechBubble in a random location
        inside the parent.

        :param panel: The panel in which the SpeechBubble will
        be placed

        :type  panel: Panel
        """
        new_area = parent.get_area() * (np.random.random() * (max_ratio-min_ratio) + min_ratio )
        self.resize_to = new_area

        x_choice, y_choice = parent.get_random_coords()

        self.location = [
            x_choice,
            y_choice
        ]

    def overlaps(self, other):
        """
        A method to check if this SpeechBubble overlaps with
        another.

        :param other: The other SpeechBubble

        :type  other: SpeechBubbles

        :return: Whether the SpeechBubbles overlap.
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

    def dump_data(self):
        """
        A method to take all the SpeechBubble's relevant data
        and create a dictionary out of it so it can be
        exported to JSON via the Page(Panel) class's
        dump_data method

        :return: Data to be returned to Page(Panel) class's
        dump_data method
        :rtype: dict
        """
        data = dict(
            texts=self.texts,
            text_indices=self.text_indices,
            font=self.font,
            font_size=self.font_size,
            speech_bubble=self.speech_bubble,
            writing_areas=self.writing_areas,
            resize_to=self.resize_to,
            location=self.location,
            parent_center_coords=self.parent_center_coords,
            width=self.width,
            height=self.height,
            orientation=self.orientation,
            transforms=self.transforms,
            transform_metadata=self.transform_metadata,
            text_orientation=self.text_orientation
        )

        return data

    @classmethod
    def load_data(cls, data: dict):
        return cls(
            texts=data['texts'],
            text_indices=data['text_indices'],
            font=data['font'],
            speech_bubble=data['speech_bubble'],
            writing_areas=data['writing_areas'],
            resize_to=data['resize_to'],
            location=data['location'],
            parent_center_coords=data['parent_center_coords'],
            width=data['width'],
            height=data['height'],
            orientation=data['orientation'],
            transforms=data['transforms'],
            transform_metadata=data['transform_metadata'],
            text_orientation=data['text_orientation']
        )

    def apply_prerendering_transforms(self, bubble, mask):
        # Center of bubble
        w, h = bubble.size
        cx, cy = w/2, h/2

        # States is used to indicate whether this bubble is
        # inverted or not to the page render function
        states = []

        # Pre-rendering transforms
        for transform in self.transforms:
            if transform == "invert":
                states.append("inverted")
                bubble = ImageOps.invert(bubble)

            elif transform == "stretch x":

                stretch_factor = self.transform_metadata['stretch_x_factor']
                new_size = (round(w*(1+stretch_factor)), h)
                # Reassign for resizing later
                w, h = new_size
                bubble = bubble.resize(new_size)
                mask = mask.resize(new_size)

                new_writing_areas = []
                for area in self.writing_areas:
                    og_width = area['original_width']

                    # Convert from percentage to actual values
                    px_width = (area['width']/100)*og_width

                    area['original_width'] = og_width*(1+stretch_factor)

                    new_writing_areas.append(area)

                self.writing_areas = new_writing_areas
                states.append("xstretch")

            elif transform == "stretch y":
                stretch_factor = self.transform_metadata['stretch_y_factor']
                new_size = (w, round(h*(1+stretch_factor)))

                # Reassign for resizing later
                w, h = new_size
                bubble = bubble.resize(new_size)
                mask = mask.resize(new_size)

                new_writing_areas = []
                for area in self.writing_areas:
                    og_height = area['original_height']

                    # Convert from percentage to actual values
                    px_height = (area['height']/100)*og_height

                    area['original_height'] = og_height*(1+stretch_factor)

                    new_writing_areas.append(area)

                self.writing_areas = new_writing_areas
                states.append("ystretch")

            elif transform == "flip horizontal":
                bubble = ImageOps.flip(bubble)
                mask = ImageOps.flip(mask)
                # TODO: vertically flip box coordinates
                new_writing_areas = []
                for area in self.writing_areas:
                    og_height = area['original_height']

                    # Convert from percentage to actual values
                    px_height = (area['height']/100)*og_height

                    og_y = ((area['y']/100)*og_height)
                    cydist = abs(cy - og_y)
                    new_y = (2*cydist + og_y) - px_height
                    new_y = (new_y/og_height)*100
                    area['y'] = new_y
                    new_writing_areas.append(area)

                self.writing_areas = new_writing_areas
                states.append("vflip")

            elif transform == "flip vertical":
                bubble = ImageOps.mirror(bubble)
                mask = ImageOps.mirror(mask)
                new_writing_areas = []
                for area in self.writing_areas:
                    og_width = area['original_width']

                    # Convert from percentage to actual values
                    px_width = (area['width']/100)*og_width

                    og_x = ((area['x']/100)*og_width)
                    # og_y = ((area['y']/100)*og_height)
                    cxdist = abs(cx - og_x)
                    new_x = (2*cxdist + og_x) - px_width
                    new_x = (new_x/og_width)*100
                    area['x'] = new_x
                    new_writing_areas.append(area)

                self.writing_areas = new_writing_areas
                states.append("hflip")

        return bubble, mask, (w, h), states

    def write_text_to_bubble(self, bubble, states):
        # Set variable font size
        min_font_size = cfg.max_font_size
        max_font_size = cfg.max_font_size
        current_font_size = self.font_size
        font = ImageFont.truetype(self.font, current_font_size)

        # Write text into bubble
        write = ImageDraw.Draw(bubble)
        if "inverted" in states:
            fill_type = "white"
        else:
            fill_type = "black"

        for i, area in enumerate(self.writing_areas):
            og_width = area['original_width']
            og_height = area['original_height']

            # Convert from percentage to actual values
            px_width = (area['width']/100)*og_width
            px_height = (area['height']/100)*og_height

            og_x = ((area['x']/100)*og_width)
            og_y = ((area['y']/100)*og_height)

            # at = (og_x, og_y, og_x+px_width, og_y+px_height)
            # write.rectangle(at, outline="black")

            # Padded
            x = og_x + 20
            y = og_y + 20

            # More padding
            max_x = px_width - 20
            max_y = px_height - 20

            text = self.texts[i]['English']  # ['Japanese']
            text = text+text+text+text+text
            text_segments = [text]
            size = font.getsize(text)

            if self.text_orientation == "ttb":

                # Setup vertical wrapping
                avg_height = size[0]/len(text)

                # Maximum chars in line
                max_chars = int((px_height//avg_height))
                if size[0] > px_height:
                    # Using specialized wrapping library
                    if max_chars > 1:
                        text_segments = cjkwrap.wrap(text, width=max_chars)

                text_max_w = len(text_segments)*size[1]

                is_fit = False

                # Horizontal wrapping
                # Reduce font or remove words till text fits
                while not is_fit:
                    if text_max_w > px_width:
                        if current_font_size > min_font_size:
                            current_font_size -= 1
                            font = ImageFont.truetype(self.font,
                                                      current_font_size)
                            size = font.getsize(text)
                            avg_height = size[0]/len(text)
                            max_chars = int((max_y//avg_height))
                            if max_chars > 1:
                                text_segments = cjkwrap.wrap(text,
                                                             width=max_chars)

                            text_max_w = len(text_segments)*size[1]
                        else:
                            text_segments.pop()
                            text_max_w = len(text_segments)*size[1]
                    else:
                        is_fit = True

            # if text left to right
            else:
                pass
                # Setup horizontal wrapping
                avg_width = size[0]/len(text)
                max_chars = int((px_width//avg_width))
                if size[0] > px_width:
                    # Using specialized wrapping library
                    if max_chars > 1:
                        text_segments = cjkwrap.wrap(text, width=max_chars)

                # Setup vertical wrapping
                text_max_h = len(text_segments)*size[1]
                is_fit = False
                while not is_fit:
                    if text_max_h > px_height:
                        if current_font_size > min_font_size:
                            current_font_size -= 1
                            font = ImageFont.truetype(self.font,
                                                      current_font_size)
                            size = font.getsize(text)
                            avg_width = size[0]/len(text)
                            max_chars = int((px_width//avg_width))
                            if max_chars > 1:
                                text_segments = cjkwrap.wrap(text,
                                                             width=max_chars)
                            text_max_h = len(text_segments)*size[1]
                        else:
                            text_segments.pop()
                            text_max_h = len(text_segments)*size[1]
                    else:
                        is_fit = True

            # Center bubble x axis
            cbx = og_x + (px_width/2)
            cby = og_y + (px_height/2)

            # Render text
            for i, text in enumerate(text_segments):
                if self.text_orientation == 'ttb':
                    rx = ((cbx + text_max_w/2) -
                          ((len(text_segments) - i)*size[1]))

                    ry = y
                else:
                    seg_size = font.getsize(text)
                    rx = cbx - seg_size[0]/2
                    ry = ((cby + (len(text_segments)*size[1])/2) -
                          ((len(text_segments) - i)*size[1]))

                write.text((rx, ry),
                           text,
                           font=font,
                           #    font=ImageFont.truetype(
                           #        "/usr/share/fonts/truetype/freefont/FreeMono.ttf", current_font_size),
                           fill=fill_type,
                           direction=self.text_orientation
                           )

    def render(self):
        """
        A function to render this speech bubble

        :return: A list of states of the speech bubble,
        the speech bubble itself, it's mask and it's location
        on the page
        :rtype: tuple
        """

        bubble = Image.open(self.speech_bubble).convert("L")
        mask = bubble.copy()
        bubble, mask, new_size, states = self.apply_prerendering_transforms(bubble, mask)
        self.write_text_to_bubble(bubble, states)        

        # reisize bubble
        w, h = new_size
        aspect_ratio = w/h
        new_height = max(1, round(np.sqrt(self.resize_to/aspect_ratio)))
        new_width = max(1, round(new_height * aspect_ratio))
        bubble = bubble.resize((new_width, new_height))
        mask = mask.resize((new_width, new_height))

        # perform rotation if it was in transforms
        if "rotate" in self.transforms:
            rotation = self.transform_metadata['rotation_amount']
            bubble = bubble.rotate(rotation, expand=True)
            mask = mask.rotate(rotation, expand=True)
            new_width, new_height = bubble.size

        # Make sure bubble doesn't bleed the page
        xcenter, ycenter = self.location
        # center bubble in coordinates
        x1 = xcenter - new_width // 2
        y1 = ycenter - new_height // 2
        x2 = x1 + new_width
        y2 = y1 + new_height

        # If it has no orientation, otherwise, the character
        # manages this.
        if type(self.orientation) is float:
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

        self.location = (x1, y1)

        dx = self.parent_center_coords[0] - xcenter
        dy = self.parent_center_coords[1] - ycenter

        if type(self.orientation) is str and (dy > 0 and self.orientation[0] == 't'
                                              or dy < 0 and self.orientation[0] == 'b'):
            bubble = ImageOps.flip(bubble)
            mask = ImageOps.flip(mask)

        if type(self.orientation) is str and (dx > 0 and self.orientation[1] == 'l'
                                              or dx < 0 and self.orientation[1] == 'r'):
            bubble = ImageOps.mirror(bubble)
            mask = ImageOps.mirror(mask)

        return bubble, mask, self.location
