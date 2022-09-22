import os
import json
import concurrent
from datetime import datetime
from tqdm import tqdm

from src import config_file as cfg
from src.layout_engine.page_objects.page import Page


def create_single_page_coco_annotations(data):
        id = data[0]
        filename = data[1]

        if not filename.endswith(".json"):
            pass

        metadata = os.path.join(cfg.METADATA_DIR, filename)
        page = Page()
        page.load_data(metadata)
        page_image, page_annotations = page.create_coco_annotations(id)

        return page_image, page_annotations


def create_coco_annotations(coco_annotations_path):
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
            "supercategory": "comic",
            "id": 1,
            "name": "panel",
        },
        {
            "supercategory": "comic",
            "id": 2,
            "name": "speech_bubble",
        },
        {
            "supercategory": "comic",
            "id": 3,
            "name": "character",
        }
    ]

    filenames = [(id + 1, filename)
                 for id, filename in enumerate(os.listdir(cfg.METADATA_DIR))
                 if filename.endswith(".json")]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(create_single_page_coco_annotations, filenames),
                            total=len(filenames)))
                            
    images, annotations = zip(*results)
    annotations = [ann for anns in annotations for ann in anns]

    for id, ann in enumerate(annotations):
        ann["id"] = id + 1

    coco_dict = {
        "info": info,
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }

    with open(coco_annotations_path, "w") as f:
        json.dump(coco_dict, f)