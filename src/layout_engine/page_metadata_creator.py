import os
import time
import concurrent
import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image

import src.config_file as cfg
from src.layout_engine.page_objects.character_factory import CharacterFactory
from src.layout_engine.page_objects.speech_bubble_factory import SpeechBubbleFactory
from src.layout_engine.page_objects import Panel, Page, Character
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


# Page creators
def create_single_panel_metadata(panel: Panel,
                                 backgrounds_dir: list,
                                 foregrounds_dir: list,
                                 font_files: list,
                                 text_dataset: pd.DataFrame,
                                 speech_bubble_tags: pd.DataFrame,
                                 minimum_speech_bubbles: int = 0,
                                 no_characters: bool = False
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
    character_factory = CharacterFactory(
        foregrounds_dir, cfg.foregrounds_dir_path)

    # Image to be used inside panel
    image_dir_len = len(backgrounds_dir)
    background_idx = np.random.randint(0, image_dir_len)

    if np.random.random() < cfg.panel_background_add_chance:
        background_image = backgrounds_dir[background_idx]
        panel.image = os.path.join(cfg.backgrounds_dir_path, background_image)

    # Foregrounds
    if no_characters:
        num_characters = 0
    else:
        num_characters = np.random.randint(0,
                                        cfg.max_characters_per_panel + 1)

    if panel.image is None:
        num_characters = min(1, num_characters)

    for _ in range(num_characters):
        character = character_factory.create(panel)
        character.place_randomly(panel)

        if np.random.random() < cfg.character_bubble_speech_freq:
            speech_bubble = speech_bubble_factory.create_with_orientation(
                character)
            speech_bubble.place_randomly(
                character, cfg.bubble_to_character_area_min_ratio, cfg.bubble_to_character_area_max_ratio)
            character.add_speech_bubble(speech_bubble)

        overlaps = False
        
        for other_character in panel.characters:
            overlaps = overlaps or character.overlaps(other_character)

        hr, wr = character.get_resized()

        if not overlaps and hr >= cfg.min_character_size and wr >= cfg.min_character_size:
            panel.characters.append(character)

    # Speech bubbles
    num_speech_bubbles = np.random.randint(minimum_speech_bubbles,
                                           cfg.max_speech_bubbles_per_panel + 1)
    if panel.image is None:
        num_speech_bubbles = min(1, num_speech_bubbles)

    # Associated speech bubbles
    for speech_bubble in range(num_speech_bubbles):
        speech_bubble = speech_bubble_factory.create_with_no_orientation(panel)

        overlaps = False
        speech_bubble.place_randomly(panel, cfg.bubble_to_panel_area_min_ratio, cfg.bubble_to_panel_area_max_ratio)

        for other_speech_bubble in panel.speech_bubbles:
            overlaps = overlaps or speech_bubble.overlaps(other_speech_bubble)

        for other_character in panel.characters:
            overlaps = overlaps or speech_bubble.overlaps(other_character)

        # If width or height are greater than panel's, don't add it
        hr, wr = speech_bubble.get_resized()

        # and hr < panel.height and wr < panel.width:
        if not overlaps and hr >= cfg.min_bubble_size and wr >= cfg.min_bubble_size:
            panel.speech_bubbles.append(speech_bubble)


def populate_panels(page: Page,
                    backgrounds_dir: list,
                    foregrounds_dir: list,
                    font_files: list,
                    text_dataset: pd.DataFrame,
                    speech_bubble_tags: pd.DataFrame,
                    minimum_speech_bubbles: int = 0,
                    no_characters: bool = False
                    ):
    """
    This function takes all the panels and adds backgorund images
    and speech bubbles to them

    :param page: Page with panels to populate

    :type page: Page

    :param image_dir: List of images to pick from

    :type image_dir: list

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
                                     foregrounds_dir,
                                     font_files,
                                     text_dataset,
                                     speech_bubble_tags,
                                     minimum_speech_bubbles,
                                     no_characters
                                     )

    return page


def create_page_metadata(backgrounds_dir,
                         foregrounds_dir,
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
                           foregrounds_dir,
                           font_files,
                           text_dataset,
                           speech_bubble_tags
                           )

    if np.random.random() < cfg.panel_removal_chance:
        page = remove_panel(page)

    page = add_background(page, backgrounds_dir, cfg.backgrounds_dir_path)

    return page


def try_create_page_metadata(data):
    page = None
    backgrounds_dir = data[0]
    foregrounds_dir = data[1]
    viable_font_files = data[2]
    text_dataset = data[3]
    speech_bubble_tags = data[4]

    seed = (os.getpid() * int(time.time())) % 4242424242
    random.seed(seed)
    np.random.seed(seed)

    try:
        page = create_page_metadata(backgrounds_dir,
                                    foregrounds_dir,
                                    viable_font_files,
                                    text_dataset,
                                    speech_bubble_tags
                                    )
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception:
        print(f"ERROR: Could not create page. Continuing...")

    return page


def create_metadata(n_pages: int, dry: bool):
    print("Loading files")
    backgrounds_dir = os.listdir(cfg.backgrounds_dir_path)
    foregrounds_dir = os.listdir(cfg.foregrounds_dir_path)

    text_dataset = pd.read_parquet("datasets/text_dataset/jesc_dialogues")

    speech_bubbles_path = "datasets/speech_bubbles_dataset/"

    speech_bubble_tags = pd.read_csv(speech_bubbles_path +
                                     "writing_area_labels.csv")
    font_files_path = "datasets/font_dataset/"
    viable_font_files = []

    with open(font_files_path+"viable_fonts.csv") as viable_fonts:
        for line in viable_fonts.readlines():
            path, viable = line.split(",")
            viable = viable.replace("\n", "")
            if viable == "True":
                viable_font_files.append(path)

    print("Running creation of metadata")

    with concurrent.futures.ProcessPoolExecutor(max_workers=cfg.CONCURRENT_MAX_WORKERS) as executor:
        jobs = {}

        pages_iter = range(n_pages)
        pages_left = n_pages

        with tqdm(total=n_pages) as pbar:
            while pages_left:
                for i in pages_iter:
                    job = executor.submit(try_create_page_metadata, (backgrounds_dir,
                                                                     foregrounds_dir,
                                                                     viable_font_files,
                                                                     text_dataset,
                                                                     speech_bubble_tags
                                                                     ))
                    jobs[job] = i

                    if len(jobs) > cfg.CONCURRENT_MAX_WORKERS:
                        break

                for job in concurrent.futures.as_completed(jobs):
                    pages_left -= 1
                    pbar.update(1)
                    page = job.result()
                    del jobs[job]

                    if page is not None:
                        page.dump_data(cfg.METADATA_DIR, dry=dry)

                    break
