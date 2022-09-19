import random
import numpy as np
import json
import uuid

from PIL import Image, ImageDraw, ImageEnhance
from src.layout_engine.helpers import (add_noise, blank_image,
                      crop_image_only_outside, get_leaf_panels, get_segmentation)
from src import config_file as cfg
from .panel import Panel
from .speech_bubble import SpeechBubble


class Page(Panel):
    """
    A class that represents a full page consiting of multiple child panels

    :param coords: A list of the boundary coordinates of a page

    :type coords: list

    :param page_type: Signifies whether a page consists of vertical
    or horizontal panels or both

    :type page_type: str

    :param num_panels: Number of panels in this page

    :type num_panels: int

    :param children: List of direct child panels of this page

    :type children: list, optional:
    """

    def __init__(self,
                 coords=[],
                 page_type="",
                 num_panels=1,
                 children=[],
                 name=None,
                 transform_noise=None,
                 transform_rotation=None,
                 ):
        """
        Constructor method
        """

        if len(coords) < 1:
            topleft = (0.0, 0.0)
            topright = (cfg.page_width, 0.0)
            bottomleft = (0.0, cfg.page_height)
            bottomright = cfg.page_size
            coords = [
                topleft,
                topright,
                bottomright,
                bottomleft
            ]

        if name is None:
            self.name = str(uuid.uuid1())
        else:
            self.name = name

        if transform_noise is None:
            self.transform_noise = np.random.randint(2, 25)
        else:
            self.transform_noise = transform_noise

        if transform_rotation is None:
            if np.random.random() < 0.5:
                self.transform_rotation = np.random.randint(-15, 15)
            else:
                self.transform_rotation = 0
        else:
            self.transform_rotation = transform_rotation

        # Initalize the panel super class
        super().__init__(coords=coords,
                         name=self.name,
                         parent=None,
                         orientation=None,
                         children=[]
                         )

        self.num_panels = num_panels
        self.page_type = page_type

        # Whether this page needs to be rendered with a background
        self.background = None

        # The leaf children of tree of panels
        # These are the panels that are actually rendered
        self.leaf_children = []

        # Size of the page
        self.page_size = cfg.page_size

    def dump_data(self, dataset_path, dry=True):
        """
        A method to take all the Page's relevant data
        and create a dictionary out of it so it can be
        exported to JSON so that it can then be loaded
        and rendered to images in parallel

        :param dataset_path: Where to dump the JSON file

        :type dataset_path: str

        :param dry: Whether to just return or write the JSON file

        :type dry: bool, optional

        :return: Optional return when running dry of a json data dump
        :rtype: str
        """

        # Recursively dump children
        if len(self.children) > 0:
            children_rec = [child.dump_data() for child in self.children]
        else:
            children_rec = []

        speech_bubbles = [bubble.dump_data() for bubble in self.speech_bubbles]
        data = dict(
            name=self.name,
            num_panels=int(self.num_panels),
            page_type=self.page_type,
            page_size=self.page_size,
            background=self.background,
            children=children_rec,
            speech_bubbles=speech_bubbles,
            transform_noise=self.transform_noise,
            transform_rotation=self.transform_rotation,
        )

        if not dry:
            with open(dataset_path+self.name+".json", "w+") as json_file:
                json.dump(data, json_file)
        else:
            return json.dumps(data)

    def load_data(self, filename):
        """
        This method reverses the dump_data function and
        load's the metadata of the page from the JSON
        file that has been loaded.

        :param filename: JSON filename to load

        :type filename: str
        """
        with open(filename, "rb") as json_file:

            data = json.load(json_file)

            self.name = data['name']
            self.num_panels = int(data['num_panels'])
            self.page_type = data['page_type']
            self.background = data['background']
            self.transform_noise = data['transform_noise']
            self.transform_rotation = data['transform_rotation']

            if len(data['speech_bubbles']) > 0:
                for speech_bubble_data in data['speech_bubbles']:
                    bubble = SpeechBubble.load_data(speech_bubble_data)
                    self.speech_bubbles.append(bubble)

            # Recursively load children
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
                    self.children.append(panel)

    def create_coco_annotations(self, image_id: int, start_annotation_id: int):
        """
        A function to create the coco annotations of this page
        """
        leaf_children = []
        # Get all the panels to be rendered
        if len(self.leaf_children) < 1:
            get_leaf_panels(self, leaf_children)
        else:
            leaf_children = self.leaf_children

        image = {
            "id": image_id,
            "file_name": self.name + cfg.output_format,
            "license": None,
        }

        W = cfg.page_width
        H = cfg.page_height

        next_annotation_id = start_annotation_id
        annotations = []

        for panel in leaf_children:
            if panel.no_render:
                continue

            page_mask = Image.new(size=(W, H), mode="1", color="black")
            draw_rect = ImageDraw.Draw(page_mask)

            # Panel coords
            rect = panel.get_polygon()

            # Fill panel class
            if panel.circular:
                draw_rect.ellipse((*panel.x3y3, *panel.x1y1), fill=255)
            else:
                draw_rect.polygon(rect, fill=255)

            for i, po in enumerate(panel.panel_objects):
                panel_object_image, panel_object_mask, location = po.render()
                instance_segmentation = Image.new(
                    '1', (panel_object_image.width, panel_object_image.height), "white")
                page_mask.paste(instance_segmentation, location, panel_object_mask)
                # page_po_mask = Image.new(size=(W, H), mode="1", color="black")
                # page_po_mask.paste(instance_segmentation, location, panel_object_mask)
                # po_seg, po_bb, po_area = get_segmentation(page_po_mask)
                # annotations.append({
                #     "id": f"panel.name_po_{i}",
                #     "image_id": self.name,
                #     "category_id": 2,
                #     "segmentation": po_seg,
                #     "area": po_area,
                #     "bbox": po_bb,
                #     "iscrowd": 0,
                # })

            for i, sb in enumerate(panel.speech_bubbles):
                bubble, mask, location = sb.render()
                # Slightly shift mask so that you get outline for bubbles
                new_mask_width = mask.size[0]+cfg.bubble_mask_x_increase
                new_mask_height = mask.size[1]+cfg.bubble_mask_y_increase
                bubble_mask = mask.resize((new_mask_width, new_mask_height))

                w, h = bubble.size
                crop_dims = (
                    5, 5,
                    5+w, 5+h,
                )
                # Uses a mask so that the "L" type bubble is cropped
                bubble_mask = bubble_mask.crop(crop_dims)

                instance_segmentation = Image.new(
                    '1', (bubble.width, bubble.height), "white")
                page_mask.paste(instance_segmentation, location, bubble_mask)
                # page_sb_mask = Image.new(size=(W, H), mode="1", color="black")
                # page_sb_mask.paste(instance_segmentation, location, bubble_mask)
                # sb_seg, sb_bb, sb_area = get_segmentation(page_sb_mask)
                # annotations.append({
                #     "id": f"panel.name_sb_{i}",
                #     "image_id": self.name,
                #     "category_id": 1,
                #     "segmentation": sb_seg,
                #     "area": sb_area,
                #     "bbox": sb_bb,
                #     "iscrowd": 0,
                # })

            if self.transform_rotation is not None and self.transform_rotation != 0:
                page_mask = page_mask.rotate(self.transform_rotation, expand=True)
                self.width, self.height = page_mask.size

            panel_segmentation, panel_bb, panel_area = get_segmentation(page_mask)

            # draw_rect.rectangle((x, y, x+w, y+h), outline="white")
            # page_mask.save("test_page.png")
            # test = Image.new(size=(W, H), mode="1", color="black")
            # test_draw = ImageDraw.Draw(test)
            # test_draw.polygon(segmentation, fill=None, outline="white")
            # test.save("test.png")

            panel_annotation = {
                "id": next_annotation_id,
                "image_id": image_id,
                "category_id": 1,
                "segmentation": panel_segmentation,
                "area": panel_area,
                "bbox": panel_bb,
                "iscrowd": 0,
            }
            annotations.append(panel_annotation)
            next_annotation_id += 1

        image["width"] = int(self.width)
        image["height"] = int(self.height)
        return image, annotations

    def render(self, show=False):
        """
        A function to render this page to an image

        :param show: Whether to return this image or to show it

        :type show: bool, optional
        """

        leaf_children = []
        # if self.num_panels > 1:
        # Get all the panels to be rendered
        if len(self.leaf_children) < 1:
            get_leaf_panels(self, leaf_children)
        else:
            leaf_children = self.leaf_children

        W = cfg.page_width
        H = cfg.page_height

        boundary_width = np.random.randint(
            cfg.boundary_width_min, cfg.boundary_width_max)
        boundary_color = (np.random.randint(0, 10), np.random.randint(
                    0, 10), np.random.randint(0, 10))

        # Create a new blank image
        page_img = Image.new(size=(W, H), mode="RGBA")

        # Render panels
        for panel in leaf_children:
            if panel.no_render:
                continue

            panel_img, panel_mask = panel.render(boundary_width, boundary_color)
            page_img.paste(panel_img, (0, 0), panel_mask)

        # Render panel objects
        for panel in leaf_children:
            if len(panel.panel_objects) < 1 or panel.no_render:
                continue
            # For each panel_object
            for po in panel.panel_objects:
                image, mask, location = po.render()
                page_img.paste(image, location, mask)

        # Render bubbles
        for panel in leaf_children:
            if len(panel.speech_bubbles) < 1 or panel.no_render:
                continue
            # For each bubble
            for sb in panel.speech_bubbles:
                bubble, mask, location = sb.render()
                # Slightly shift mask so that you get outline for bubbles
                new_mask_width = mask.size[0]+cfg.bubble_mask_x_increase
                new_mask_height = mask.size[1]+cfg.bubble_mask_y_increase
                bubble_mask = mask.resize((new_mask_width, new_mask_height))

                w, h = bubble.size
                crop_dims = (
                    5, 5,
                    5+w, 5+h,
                )
                # Uses a mask so that the "L" type bubble is cropped
                bubble_mask = bubble_mask.crop(crop_dims)
                page_img.paste(bubble, location, bubble_mask)

        if self.transform_rotation is not None and self.transform_rotation != 0:
            page_img = page_img.rotate(self.transform_rotation, expand=True)
            self.width, self.height = page_img.size

        W, H = page_img.size

        # Set background if needed
        if self.background is not None:
            if self.background == "#color":
                # TODO: Parameterize
                bg = np.zeros([H, W, 3], dtype=np.uint8)
                if np.random.random() < cfg.background_add_chance:
                    bg[:, :, :] = (np.random.randint(0, 255), np.random.randint(
                        0, 255), np.random.randint(0, 255))
                else:
                    bg[:, :, :] = (np.random.randint(245, 255), np.random.randint(
                        245, 255), np.random.randint(245, 255))
                crop_array = bg
            else:
                bg = Image.open(self.background).convert("RGB")
                crop_array = crop_image_only_outside(bg)

            bg = Image.fromarray(crop_array)
            bg = bg.resize((W, H))
            bg.paste(page_img, (0, 0), page_img)
            page_img = bg

        # Add noise
        noise = add_noise(blank_image(
                    W, H), sigma=self.transform_noise)
        page_img_arr = np.multiply(np.asarray(page_img), noise/255.0)
        page_img = Image.fromarray(page_img_arr.astype(np.uint8))
        
        # Add texture
        if np.random.rand() < cfg.texture_probability:
            texture_path = random.choice(cfg.texture_images)
            texture = Image.open(texture_path).convert("RGBA")
            # texture = texture.rotate(np.random.randint(-15, 15))
            texture = texture.resize((W, H))
            texture_mask = Image.new(mode="L", size=(W, H), color=np.random.randint(125, 245))
            page_img = Image.composite(page_img, texture, texture_mask)

        if show:
            page_img.show()
        else:
            return page_img
