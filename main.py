import os
import pandas as pd
import pytest
import concurrent
from tqdm import tqdm
from argparse import ArgumentParser

from src import config_file as cfg
from src.layout_engine.page_annotations_creator import create_coco_annotations
from src.layout_engine.page_objects.page import Page
from src.scraping.download_texts import download_and_extract_jesc
from src.scraping.download_fonts import get_font_links
from src.scraping.download_images import download_db_illustrations
from src.text_dataset_format_changer import convert_jesc_to_dataframe
from src.extract_and_verify_fonts import verify_font_files
from src.convert_images import convert_images_to_bw
from src.layout_engine.page_renderer import render_pages
from src.layout_engine.page_metadata_creator import (
    create_metadata,
    create_page_metadata
)


def parse_args():
    usage_message = """
                    This file is designed you to create the AMP dataset
                    To learn more about how to use this open the README.md
                    """

    parser = ArgumentParser(usage=usage_message)

    parser.add_argument("--download_jesc", "-dj",
                        action="store_true",
                        help="Download JESC Japanese/English dialogue corpus")
    parser.add_argument("--download_fonts", "-df",
                        action="store_true",
                        help="Scrape font files")
    parser.add_argument("--download_images", "-di",
                        action="store_true",
                        help="Download anime illustrtations from Kaggle")
    parser.add_argument("--download_speech_bubbles", "-ds",
                        action="store_true",
                        help="Download speech bubbles from Gcloud")

    parser.add_argument("--verify_fonts", "-vf",
                        action="store_true",
                        help="Verify fonts for minimum coverage from")

    parser.add_argument("--convert_images", "-ci",
                        action="store_true",
                        help="Convert downloaded images to black and white")

    parser.add_argument("--create_page_metadata", "-pm", nargs=1, type=int)
    parser.add_argument("--render_pages", "-rp", action="store_true")
    parser.add_argument("--create_annotations", "-ca", action="store_true")
    parser.add_argument("--generate_pages", "-gp", nargs=1, type=int)
    parser.add_argument("--dry", action="store_true", default=False)
    parser.add_argument("--run_tests", action="store_true")

    return parser.parse_args()


def _create_metadata(n_pages: int, dry: bool):
    create_metadata(n_pages, dry)


def _render_pages(dry):
    if not os.path.isdir(cfg.METADATA_DIR):
        print("There is no metadata, please generate metadata first.")
    else:
        print("Loading metadata and rendering")
        render_pages(dry=dry)


def _create_annotations(annotations_path):
    if not os.path.isdir(cfg.METADATA_DIR):
        print("There is no metadata, please generate metadata first.")
    else:
        print("Loading metadata and creating COCO annotations")
        create_coco_annotations(annotations_path)


def main(args):
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # Wrangling with the text dataset
    if args.download_jesc:
        download_and_extract_jesc()
        convert_jesc_to_dataframe()

    # Font dataset
    # TODO: Add an automatic scraper
    if args.download_fonts:
        get_font_links()
        print("Please run scraping/font_download_manual.ipynb" +
              " and download fonts manually from the links" +
              "that were scraped then place them in" +
              "datasets/font_dataset/font_file_raw_downloads/")

        print("NOTE: There's no need to extract them this program does that")

    # Font verification
    if args.verify_fonts:
        font_dataset_path = "datasets/font_dataset/"
        text_dataset_path = "datasets/text_dataset/"
        # fonts_raw_dir = font_dataset_path+"font_file_raw_downloads/"
        # fonts_zip_output = font_dataset_path+"fonts_zip_output/"
        font_file_dir = font_dataset_path+"font_files/"
        dataframe_file = text_dataset_path+"jesc_dialogues"
        render_text_test_file = font_dataset_path + "render_test_text.txt"

        # extract_fonts()
        verify_font_files(
            dataframe_file,
            render_text_test_file,
            font_file_dir,
            font_dataset_path
        )

    # Download and danbooru images using Rsync
    if args.download_images:
        download_db_illustrations()
        convert_images_to_bw()

    if args.convert_images:
        convert_images_to_bw()

    coco_annotations_path = os.path.join(cfg.OUTPUT_DIR, "labels.json")

    if not os.path.isdir(cfg.IMAGES_DIR):
        os.mkdir(cfg.IMAGES_DIR)

    # Page creation
    if args.create_page_metadata is not None:
        if not os.path.isdir(cfg.METADATA_DIR):
            os.mkdir(cfg.METADATA_DIR)

        _create_metadata(args.create_page_metadata[0], args.dry)

    if args.render_pages:
        _render_pages(args.dry)

    if args.create_annotations:
        _create_annotations(coco_annotations_path)

    # Combines the above in case of small size
    if args.generate_pages is not None:
        if not os.path.isdir(cfg.METADATA_DIR):
            os.mkdir(cfg.METADATA_DIR)
        _create_metadata(args.generate_pages[0], args.dry)
        _render_pages(args.dry)
        _create_annotations(coco_annotations_path)

    if args.run_tests:
        pytest.main([
            "tests/unit_tests/",
            "-s",
            "-x",
        ])


if __name__ == '__main__':
    args = parse_args()
    main(args)
