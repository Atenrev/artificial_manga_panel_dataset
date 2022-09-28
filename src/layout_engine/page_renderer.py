import os
import concurrent
import json
from tqdm import tqdm

from .page_objects.page import Page
from .. import config_file as cfg


def create_single_page(data):
    """
    This function is used to render a single page from a metadata json file
    to a target location.

    :param paths:  a tuple of the page metadata and output path
    as well as whether or not to save the rendered file i.e. dry run or
    wet run

    :type paths: tuple
    """
    metadata = os.path.join(cfg.METADATA_DIR, data[0])
    dry = data[1]

    page = Page()
    page.load_data(metadata)
    image_filename = os.path.join(cfg.IMAGES_DIR, page.name+cfg.output_format)

    if not os.path.isfile(image_filename) and not dry:
        img = page.render()
        img.save(image_filename)


def render_pages(dry=False):
    """
    Takes metadata json files and renders page images

    :param metadata_dir: A directory containing all the metadata json files

    :type metadata_dir: str

    :param images_dir: The output directory for the rendered pages

    :type images_dir: str
    """

    filenames = [(filename, dry, )
                 for filename in os.listdir(cfg.METADATA_DIR)
                 if filename.endswith(".json")]

    with concurrent.futures.ProcessPoolExecutor(max_workers=cfg.CONCURRENT_MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(create_single_page, filenames),
                            total=len(filenames)))
