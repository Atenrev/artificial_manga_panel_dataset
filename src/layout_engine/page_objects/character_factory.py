import os
import numpy as np

from PIL import Image
from src.layout_engine.page_objects import Character, Panel


class CharacterFactory:
    def __init__(self,
        foregrounds_dir: list,
        foregrounds_dir_path: str
    ) -> None:
        self.foregrounds_dir = foregrounds_dir
        self.foregrounds_dir_path = foregrounds_dir_path

    def create(self, panel: Panel) -> Character:
        foregrounds_len = len(self.foregrounds_dir)
        foreground_file_idx = np.random.randint(
            0,
            foregrounds_len
        )
        character_file = os.path.join(
            self.foregrounds_dir_path, self.foregrounds_dir[foreground_file_idx])

        character_img = Image.open(character_file)
        width, height = character_img.size

        character = Character(
            character_file,
            width,
            height,
            panel_center_coords=panel.get_center(),
        )

        return character

