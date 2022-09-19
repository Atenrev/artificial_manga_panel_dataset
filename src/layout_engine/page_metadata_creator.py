import numpy as np
import os
import pandas
from PIL import Image

import src.config_file as cfg
from src.layout_engine.page_objects.speech_bubble_factory import SpeechBubbleFactory
from src.layout_engine.page_objects import Panel, Page, PanelObject
from src.layout_engine.page_metadata_transforms import *
from src.layout_engine.page_metadata_draw import *


def add_background(page, image_dir, image_dir_path):
    """
    Add a background color or image to the page

    :param page: Page to add background to

    :type page: Page

    :param image_dir: A list of images

    :type image_dir: list

    :param image_dir_path: path to images used for adding
    the full path to the page

    :type image_dir_path: str

    :return: Page with background

    :rtype: Page
    """

    if np.random.random() < cfg.solid_background_probability:
        page.background = "#color"
    else:
        image_dir_len = len(image_dir)
        idx = np.random.randint(0, image_dir_len)
        page.background = image_dir_path + image_dir[idx]

    return page


def create_panel_object_metadata(
    panel: Panel,
    foregrounds_dir: list,
    foregrounds_dir_path: str
) -> PanelObject:
    foregrounds_len = len(foregrounds_dir)
    foreground_file_idx = np.random.randint(
        0,
        foregrounds_len
    )
    panel_object_file = os.path.join(
        foregrounds_dir_path, foregrounds_dir[foreground_file_idx])

    panel_object_img = Image.open(panel_object_file)
    width, height = panel_object_img.size

    panel_object = PanelObject(
        panel_object_file,
        width,
        height,
        panel_center_coords=panel.get_center(),
    )

    return panel_object


# Page creators
def create_single_panel_metadata(panel: Panel,
                                 backgrounds_dir: list,
                                 backgrounds_dir_path: str,
                                 foregrounds_dir: list,
                                 foregrounds_dir_path: str,
                                 font_files: list,
                                 text_dataset: pandas.DataFrame,
                                 speech_bubble_tags: pandas.DataFrame,
                                 minimum_speech_bubbles: int = 0
                                 ):
    """
    This is a helper function that populates a single panel with
    an image, and a set of speech bubbles

    :param panel: Panel to add image and speech bubble to

    :type panel: Panel

    :param image_dir: List of images to pick from

    :type image_dir: list

    :param image_dir_path: Path of images dir to add to
    panels

    :type image_dir_path: str

    :param font_files: list of font files for speech bubble
    text

    :type font_files: list

    :param text_dataset: A dask dataframe of text to
    pick to render within speech bubble

    :type text_dataset: pandas.dataframe

    :param speech_bubble_files: list of base speech bubble
    template files

    :type speech_bubble_files: list

    :param speech_bubble_tags: a list of speech bubble
    writing area tags by filename

    :type speech_bubble_tags: list

    :param minimum_speech_bubbles: Set whether panels
    have a minimum number of speech bubbles, defaults to 0

    :type  minimum_speech_bubbles: int
    """
    speech_bubble_factory = SpeechBubbleFactory(
        speech_bubble_tags, font_files, text_dataset)

    # Image to be used inside panel
    image_dir_len = len(backgrounds_dir)
    background_idx = np.random.randint(0, image_dir_len)

    if np.random.random() < cfg.panel_background_add_chance:
        background_image = backgrounds_dir[background_idx]
        panel.image = os.path.join(backgrounds_dir_path, background_image)

    # Foregrounds
    num_panel_objects = np.random.randint(0,
                                          cfg.max_panel_objects_per_panel + 1)
    if panel.image is None:
        num_panel_objects = min(1, num_panel_objects)

    for _ in range(num_panel_objects):
        panel_object = create_panel_object_metadata(
            panel, foregrounds_dir, foregrounds_dir_path)

        overlaps = False
        panel_object.place_randomly(panel)

        if np.random.random() < cfg.panel_object_bubble_speech_freq:
            speech_bubble = speech_bubble_factory.create_with_orientation(
                panel_object)
            speech_bubble.place_randomly(
                panel_object, cfg.bubble_to_panel_object_area_max_ratio)
            panel_object.add_speech_bubble(speech_bubble)

        for other_panel_object in panel.panel_objects:
            overlaps = overlaps or panel_object.overlaps(other_panel_object)

        if not overlaps:
            panel.panel_objects.append(panel_object)

    # Speech bubbles
    num_speech_bubbles = np.random.randint(minimum_speech_bubbles,
                                           cfg.max_speech_bubbles_per_panel + 1)
    if panel.image is None:
        num_speech_bubbles = min(1, num_speech_bubbles)                                    

    # Associated speech bubbles
    for speech_bubble in range(num_speech_bubbles):
        speech_bubble = speech_bubble_factory.create_with_no_orientation(panel)

        overlaps = False
        speech_bubble.place_randomly(panel, cfg.bubble_to_panel_area_max_ratio)

        for other_speech_bubble in panel.speech_bubbles:
            overlaps = overlaps or speech_bubble.overlaps(other_speech_bubble)

        for other_panel_object in panel.panel_objects:
            overlaps = overlaps or speech_bubble.overlaps(other_panel_object)

        # If width or height are greater than panel's, don't add it
        # hr, wr = speech_bubble.get_resized()

        if not overlaps: #and hr < panel.height and wr < panel.width:
            panel.speech_bubbles.append(speech_bubble)


def populate_panels(page: Page,
                    backgrounds_dir: list,
                    backgrounds_dir_path: str,
                    foregrounds_dir: list,
                    foregrounds_dir_path: str,
                    font_files: list,
                    text_dataset: pandas.DataFrame,
                    speech_bubble_tags: pandas.DataFrame,
                    minimum_speech_bubbles: int = 0
                    ):
    """
    This function takes all the panels and adds backgorund images
    and speech bubbles to them

    :param page: Page with panels to populate

    :type page: Page

    :param image_dir: List of images to pick from

    :type image_dir: list

    :param image_dir_path: Path of images dir to add to
    panels

    :type image_dir_path: str

    :param font_files: list of font files for speech bubble
    text

    :type font_files: list

    :param text_dataset: A dask dataframe of text to
    pick to render within speech bubble

    :type text_dataset: pandas.dataframe

    :param speech_bubble_files: list of base speech bubble
    template files

    :type speech_bubble_files: list

    :param speech_bubble_tags: a list of speech bubble
    writing area tags by filename

    :type speech_bubble_tags: list

    :param minimum_speech_bubbles: Set whether panels
    have a minimum number of speech bubbles, defaults to 0

    :type  minimum_speech_bubbles: int

    :return: Page with populated panels

    :rtype: Page
    """
    for child in page.leaf_children:
        child.refresh_size()
        child.refresh_drawable_area()

    for child in page.leaf_children:
        create_single_panel_metadata(child,
                                        backgrounds_dir,
                                        backgrounds_dir_path,
                                        foregrounds_dir,
                                        foregrounds_dir_path,
                                        font_files,
                                        text_dataset,
                                        speech_bubble_tags,
                                        minimum_speech_bubbles
                                        )

    return page


def create_page_metadata(backgrounds_dir,
                         backgrounds_dir_path,
                         foregrounds_dir,
                         foregrounds_dir_path,
                         font_files,
                         text_dataset,
                         speech_bubble_tags):
    """
    This function creates page metadata for a single page. It includes
    transforms, background addition, random panel removal,
    panel shrinking, and the populating of panels with
    images and speech bubbles.

    :param image_dir: List of images to pick from

    :type image_dir: list

    :param image_dir_path: Path of images dir to add to
    panels

    :type image_dir_path: str

    :param font_files: list of font files for speech bubble
    text

    :type font_files: list

    :param text_dataset: A dask dataframe of text to
    pick to render within speech bubble

    :type text_dataset: pandas.dataframe

    :param speech_bubble_files: list of base speech bubble
    template files

    :type speech_bubble_files: list

    :param speech_bubble_tags: a list of speech bubble
    writing area tags by filename

    :type speech_bubble_tags: list

    :return: Created Page with all the bells and whistles

    :rtype: Page
    """
    # Select number of panels on the page
    # between 1 and 8

    number_of_panels = np.random.choice(
        list(cfg.num_pages_ratios.keys()),
        p=list(cfg.num_pages_ratios.values())
    )

    # Select page type
    if number_of_panels > 8:
        page_type = "vh"
    else:
        page_type = np.random.choice(
        list(cfg.vertical_horizontal_ratios.keys()),
        p=list(cfg.vertical_horizontal_ratios.values())
    )

    page = get_base_panels(number_of_panels, page_type)

    if np.random.random() < cfg.panel_transform_chance:
        page = add_transforms(page)

    page = shrink_panels(page)
    page = populate_panels(page,
                           backgrounds_dir,
                           backgrounds_dir_path,
                           foregrounds_dir,
                           foregrounds_dir_path,
                           font_files,
                           text_dataset,
                           speech_bubble_tags
                           )

    if np.random.random() < cfg.panel_removal_chance:
        page = remove_panel(page)

    page = add_background(page, backgrounds_dir, backgrounds_dir_path)

    return page
