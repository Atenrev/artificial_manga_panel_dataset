# Artificial Comics/Manga Dataset - ACMD

## What is in this repo?
This repository contains the associated files and links to create an artificial comic/manga dataset.
Here's a sample of an image created with this code:
<br>
<img src="https://github.com/atenrev/artificial_manga_panel_dataset/blob/main/docs/misc_files/sample.png" width=425>


## Setup and usage

1. Libraqm is required for rendering CJK text properly. Follow instructions [here](https://github.com/HOST-Oman/libraqm)
2. ```pip3 install -r requirements.txt```
3. Base materials here: https://www.kaggle.com/aasimsani/ampd-base just create a `datasets/` folder and place the contents of the Kaggle repo in it. You will only need ```font_dataset```, ```speech_bubbles_dataset```, and ```text_dataset```.
4. Run ```python3 main.py --download_images``` to download the foreground and background images.
5. Create a ```textures``` directory inside ```datasets``` and place any textures you want to apply to the rendered pages.
6. In case you want to modify individual scripts for scraping or cleaning this downloaded data you can find them in ```main.py```
7. Before you start just run ```python3 main.py --run_tests``` to make sure
you have all the libraries installed and things are working fine
6. Now you can run ```python3 main.py --generate_pages N``` to make pages
  1. You can also run the metadata generation ```python3 main.py --create_page_metadata N```, the page rendering ```python3 main.py --render_pages```, and the annotations creator ```python3 main.py --create_annotations``` seperately. render_pages and create_annotations calls will read the ```datasets/page_metadata/``` folder to find files to render.
7. You can modify ```src/config_file.py``` to change how the generator works to render various parts of the page


### Directory structure

```
./datasets/
    backgrounds/
    font_dataset/
    foregrounds/
    speech_bubbles_dataset/
    text_dataset/
    textures/
    bn_danbooru_bg.csv
    bn_danbooru_fg.csv

./src/
    layout_engine/
        page_objects/
            panel.py
            ...
        ...
    scraping/
    config_file.py
    convert_images.py
    extract_and_verify_fonts.py
    text_dataset_format.changer.py

./tests/
    ...
```


## Future work:

- [ ] Add English fonts (because of this, some bubbles render empty) 
- [ ] Add bubbles outside panels 
- [ ] Create a custom speech bubble creator


## Dataset

### Data variety

- 196 fonts with >80% character coverage
- 91 unique speech bubble types
- 2,801,388 sentence pairs in Japanese and English
- 5,773 background images
- 18,054 foreground images 
- 40 texture images for augmentation


### How does the creation and rendering work?

#### Creating the metadata

1. Each Manga Page Image is represented by a Page object which is a special type of Panel object which has children panels and those have sub-panels in a tree-like fashion.
2. Each Page has N panels which is determined by segmenting the page into rectangles as follows:
  1. First a top level set of panels are created. e.g. divide the page into 2 rectnagles .
  2. Then based on which type of layout is selected one or both of the panels are further subdivided into panels e.g. I want 4 panels on this page. So I can divide two panels into two, one panel into three and leave one as is, etc.
  3. These "formulas" of layouts for pages are hard coded per number of panels, for now, up to 8 panels.
  4. In addition to this, the dividion of panels into sub-panels is not equal and the panels are sub-divided randomly across one axis. e.g. 1 panel can have 30% of the area and the other 70%.
  5. These panels as they are being subdivided are entered as children of a parent panel resulting in a tree originating at the Page as the root.
3. Once this is done the panels are then put through various affine transforms and slicing to result in the iconic "Manga Panel" like layout. Refer example above.
4. After the transformations, the panels are then shrunk in size to create panel boundaries which are visible.
5. Once shrinking is done, there's a chance of adding an image or solid color background to the whole page and subsequently removing a panel or two randomly to create a white space or a foreground effect.
6. Once this is done each panel is then populated with a background image with a high probability which is selected randomly and a number of characters and speech bubbles are created.
7. Bubbles are created as follows:
  1. First a template image for a speech bubble is selected out of the available templates. This template is then put through a series of transformations. (flipping it horizontally/vertically, rotating it slightly, inverting it, stretching it along the x or y axis).
  2. Along with this the tagged writing area within the bubble is also transformed.
  3. Once this is done, a selected font with a random font size and a selected piece of text are then resized such that they can be rendered onto the bubble either top to bottom or left to right depending on a user-defined probability.
8. Characters are created as follows:
   1. A foreground image is selected. The character image is also put through a series of transformations.
   2. A bubble is created with a random chance as a Character child.
9.  With a random chance, the panel will be circular if it's a rect.
10. After this, the metadata is written into a JSON file.
11. This creation of one page sequentially and is wrapped in a single concurrent function that allows it to be dumped to JSON in parallel.


#### Rendering the pages
1. Once the JSON files are dumped, the folder where they were dumped is scanned. Then, each file is loaded again via a load_data method in the Page class. This is then subsequently rendered by each page class's render method. This operation is done concurrently and in parallel for speed.


#### Creating the annotations
1. It follows a similar flow to the rendering. In this case, the create_coco_annotations method is called, which will create the segmentation for panels, characters, and bubbles. This method also uses the render method of each object but the Panel. This operation is also done concurrently.


### Resources used for creating dataset:

1. [JESC dataset](https://nlp.stanford.edu/projects/jesc/)
2. [Danbooru dataset](https://www.gwern.net/Danbooru2021)
3. [Fonts allowed for commerical use from Free Japanese Fonts](https://www.freejapanesefont.com/) - Licences are on individual pages
4. [Object Detection for Comics using Manga109 Annotations](https://arxiv.org/pdf/1803.08670.pdf) - Used as benchmark
5. [Speech bubbles PSD file](https://www.deviantart.com/zombiesmile/art/300-Free-Speech-Bubbles-Download-419223430)
6. [Label studio](https://labelstud.io/)

### Licences and Citations
**JESC dataset**
```
@ARTICLE{pryzant_jesc_2017,
   author = {{Pryzant}, R. and {Chung}, Y. and {Jurafsky}, D. and {Britz}, D.},
    title = "{JESC: Japanese-English Subtitle Corpus}",
  journal = {ArXiv e-prints},
archivePrefix = "arXiv",
   eprint = {1710.10639},
 keywords = {Computer Science - Computation and Language},
     year = 2017,
    month = oct,
}             ```
```

[**Speech bubble PSD file Licence**](https://friendlystock.com/terms-of-use/)
