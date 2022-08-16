import json
import os
import pandas as pd
import pytest
from datetime import datetime
from preprocesing.layout_engine.page_objects.page import Page
from scraping.download_texts import download_and_extract_jesc
from scraping.download_fonts import get_font_links
from scraping.download_images import download_db_illustrations
from tqdm import tqdm
from argparse import ArgumentParser

from preprocesing.text_dataset_format_changer import convert_jesc_to_dataframe
from preprocesing.extract_and_verify_fonts import verify_font_files
from preprocesing.convert_images import convert_images_to_bw
from preprocesing.layout_engine.page_renderer import render_pages
from preprocesing.layout_engine.page_metadata_creator import (
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
    parser.add_argument("--generate_pages", "-gp", nargs=1, type=int)
    parser.add_argument("--dry", action="store_true", default=False)
    parser.add_argument("--run_tests", action="store_true")
    parser.add_argument("--output_dir", "-od", type=str, default="output_ds/",
                        help="Output directory")

    return parser.parse_args()


def _render_pages(metadata_folder, images_folder, dry):
    if not os.path.isdir(metadata_folder):
        print("There is no metadata, please generate metadata first.")
    else:
        print("Loading metadata and rendering")
        render_pages(metadata_folder, images_folder, dry=dry)


def _create_metadata(metadata_folder, n_pages, dry):
    # number of pages
    n = n_pages
    print("Loading files")
    backgrounds_dir_path = "datasets/backgrounds/"
    backgrounds_dir = os.listdir(backgrounds_dir_path)
    foregrounds_dir_path = "datasets/foregrounds/"
    foregrounds_dir = os.listdir(foregrounds_dir_path)

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
    n_errors = 0

    for _ in tqdm(range(n)):
        try:
            page = create_page_metadata(backgrounds_dir,
                                        backgrounds_dir_path,
                                        foregrounds_dir,
                                        foregrounds_dir_path,
                                        viable_font_files,
                                        text_dataset,
                                        speech_bubble_tags
                                        )
            page.dump_data(metadata_folder, dry=dry)
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except:
            print(f"ERROR: Could not create page. Continuing...")
            n_errors += 1

    print(f"Could not create {n_errors} pages.")


def _create_coco_annotations(metadata_dir, images_dir, coco_annotations_path):
    print("Loading metadata and creating COCO annotations")

    now = datetime.now()
    now_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info = {
        "year": now.year,
        "version": 1.0,
        "description": "Artificial comics and manga dataset.",
        "contributor": "Atenrev",
        "url": "https://github.com/Atenrev",
        "date_created": now_formatted,
    }

    categories = [
        {
            "id": 0,
            "name": "panel",
        }
    ]

    images = []
    annotations = []

    for filename in tqdm(os.listdir(metadata_dir)):
        if not filename.endswith(".json"):
            pass

        metadata = os.path.join(metadata_dir, filename)
        page = Page()
        page.load_data(metadata)
        page_image, page_annotations = page.create_coco_annotations()

        images.append(page_image)
        annotations.extend(page_annotations)

    coco_dict = {
        "info": info,
        "categories": categories,
        "licenses": [],
        "images": images,
        "annotations": annotations
    }

    with open(coco_annotations_path, "w") as f:
        json.dump(coco_dict, f)


def main(args):
    os.makedirs(args.output_dir, exist_ok=True)

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

    # Download and convert image from Kaggle
    if args.download_images:
        download_db_illustrations()
        convert_images_to_bw()

    if args.convert_images:
        convert_images_to_bw()

    metadata_folder = os.path.join(args.output_dir, "metadata/")
    images_folder = os.path.join(args.output_dir, "data/")
    coco_annotations_path = os.path.join(args.output_dir, "labels.json")

    if not args.dry:
        if not os.path.isdir(metadata_folder):
            os.mkdir(metadata_folder)

        if not os.path.isdir(images_folder):
            os.mkdir(images_folder)

    # Page creation
    if args.create_page_metadata is not None:
        _create_metadata(metadata_folder, args.create_page_metadata[0], args.dry)

    if args.render_pages:
        _render_pages(metadata_folder, images_folder, args.dry)

    # Combines the above in case of small size
    if args.generate_pages is not None:
        _create_metadata(metadata_folder, args.generate_pages[0], args.dry)
        _render_pages(metadata_folder, images_folder, args.dry)
        _create_coco_annotations(metadata_folder, images_folder, coco_annotations_path)

    if args.run_tests:
        pytest.main([
                "tests/unit_tests/",
                "-s",
                "-x",
                ])


if __name__ == '__main__':
    args = parse_args()
    main(args)

