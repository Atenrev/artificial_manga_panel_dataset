import pandas
import numpy as np
import json

from PIL import Image
from src.layout_engine.page_objects import SpeechBubble


class SpeechBubbleFactory:
    def __init__(self,
        speech_bubbles_dataset: pandas.DataFrame,
        font_files: list,
        text_dataset: pandas.DataFrame,
    ) -> None:
        speech_bubble_tags_noriented_index = speech_bubbles_dataset["orientation"].isna()
        self.speech_bubble_tags_noriented = speech_bubbles_dataset[speech_bubble_tags_noriented_index]
        speech_bubble_tags_oriented_index = speech_bubbles_dataset["orientation"].apply(isinstance, args=(str,))
        self.speech_bubble_tags_oriented = speech_bubbles_dataset[speech_bubble_tags_oriented_index]
        self.font_files = font_files
        self.text_dataset = text_dataset

    def create(self, sb_sample: pandas.DataFrame, parent):
        # Select a font
        font_dataset_len = len(self.font_files)
        font_idx = np.random.randint(0, font_dataset_len)
        font = self.font_files[font_idx]

        speech_bubble_file = sb_sample["imagename"].values[0]

        speech_bubble_writing_area = sb_sample['label'].values[0]
        assert speech_bubble_writing_area is not None
        speech_bubble_writing_area = json.loads(speech_bubble_writing_area)
        speech_orientation = sb_sample['orientation'].values[0]

        # Select text for writing areas
        text_dataset_len = len(self.text_dataset)
        texts = []
        text_indices = []
        for _ in range(len(speech_bubble_writing_area)):
            text_idx = np.random.randint(0, text_dataset_len)
            text_indices.append(text_idx)
            text = self.text_dataset.iloc[text_idx].to_dict()
            texts.append(text)

        assert speech_bubble_file is not None
        speech_bubble_img = Image.open(speech_bubble_file)
        w, h = speech_bubble_img.size
        # Create speech bubble
        speech_bubble = SpeechBubble(texts=texts,
                                    text_indices=text_indices,
                                    font=font,
                                    speech_bubble=speech_bubble_file,
                                    writing_areas=speech_bubble_writing_area,
                                    width=w,
                                    height=h,
                                    orientation=speech_orientation,
                                    parent_center_coords=parent.get_center(),
                                    )

        return speech_bubble

    def create_with_no_orientation(self, parent):
        sb_sample = self.speech_bubble_tags_noriented.sample()
        return self.create(sb_sample, parent)
    
    def create_with_orientation(self, parent):
        sb_sample = self.speech_bubble_tags_oriented.sample()
        return self.create(sb_sample, parent)

        

    