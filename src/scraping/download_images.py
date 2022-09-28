import os
import subprocess
import json
from tqdm import tqdm

import src.config_file as cfg


class JSONLogger:
    log_file = "download_logger.json"

    def __init__(self) -> None:
        if os.path.isfile(self.log_file):
            with open(self.log_file, 'r', encoding="utf-8") as f:
                self.log = json.load(f)
        else:
            self.log = {
                "download_finished": False,
                "last_file": None,
                "current_type": "bg",
                "download_ok": [],
                "download_nok": []
            }

    def set_current_type(self, t: str) -> None:
        self.log["current_type"] = t
        self.dump()

    def get_current_type(self) -> str:
        return self.log["current_type"]

    def get_last_file(self) -> int:
        return self.log["last_file"]

    def log_download(self, id: int, success: bool) -> None:
        if success:
            self.log["download_ok"].append({"id": id})
        else:
            self.log["download_nok"].append({"id": id})

        self.log["last_file"] = id

        self.dump()
    
    def finish(self) -> None:
        self.log["download_finished"] = True
        self.dump()

    def dump(self) -> None:
        with open(self.log_file, 'w', encoding="utf-8") as f:
            json.dump(self.log, f)


def download_image(id: int, dst: str, extension: str = '.png') -> bool:
    bucket = str(id % 1000).zfill(4)
    error_code = subprocess.call([
        'wsl',
        'rsync',
        f'rsync://176.9.41.242:873/danbooru2021/original/{bucket}/{id}.{extension}',
        dst
    ], shell=True)
    return error_code == 0


def download_db_illustrations():
    os.makedirs(cfg.bg_folder, exist_ok=True)
    os.makedirs(cfg.fg_folder, exist_ok=True)

    logger = JSONLogger()

    if logger.get_current_type() == "bg":
        with open(cfg.bg_data, 'r', encoding='utf-8') as bg_data_file:
            ids = [int(line) for line in bg_data_file.readlines()]

            if logger.get_last_file() is not None:
                last_file_index = ids.index(logger.get_last_file())
                ids = ids[last_file_index+1:]

            for row in tqdm(ids):
                id = int(row)
                success = download_image(id, cfg.bg_folder, extension='jpg')

                if not success:
                    success = download_image(id, cfg.bg_folder, extension='png')

                logger.log_download(id, success)

    print("Finished downloading backgrounds. Downloading foregrounds...")
    logger.set_current_type("fg")

    with open(cfg.fg_data, 'r', encoding='utf-8') as fg_data_file:
        ids = [int(line) for line in fg_data_file.readlines()]

        if logger.get_last_file() is not None:
            last_file_index = ids.index(logger.get_last_file())
            ids = ids[last_file_index+1:]

        for row in tqdm(ids):
            id = int(row)
            success = download_image(id, cfg.fg_folder, extension='png')

            if not success:
                success = download_image(id, cfg.fg_folder, extension='jpg')

            logger.log_download(id, success)

    print("Finished downloading foregrounds.")
    logger.finish()