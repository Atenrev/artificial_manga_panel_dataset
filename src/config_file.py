import os
import glob


# Concurrent
CONCURRENT_MAX_WORKERS = 8

# Paths
texture_images = glob.glob("datasets/textures/*")
backgrounds_dir_path = "datasets/backgrounds/"
foregrounds_dir_path = "datasets/foregrounds/"
OUTPUT_DIR = "acmd_v3"
METADATA_DIR = os.path.join(OUTPUT_DIR, "metadata/")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "data/")
ANNOTATIONS_DIR = os.path.join(OUTPUT_DIR, "annotations/")

# **Page rendering**
page_width = 800
page_height = 1200

page_size = (page_width, page_height)

output_format = ".png"

boundary_width_min = 2
boundary_width_max = 9
boundary_color = "black"

# **Font coverage**
# How many characters of the dataset should the font files support
font_character_coverage = 0.80


# **Panel Drawing**
# *Panel ratios*

# TODO: Figure out page type distributions
num_pages_ratios = {
    1: 0.1125,
    2: 0.1125,
    3: 0.1125,
    4: 0.1125,
    5: 0.1125,
    6: 0.1125,
    7: 0.1125,
    8: 0.1125,
    32: 0.1,
}

vertical_horizontal_ratios = {
    "v": 0.1,
    "h": 0.1,
    "vh": 0.8
}

solid_background_probability = 0.9

panel_background_add_chance = 0.975

# Panel transform chance

panel_transform_chance = 0.75

# Panel shrinking

panel_shrink_amount_max = 0
panel_shrink_amount_min = -36

# Panel removal

panel_removal_chance = 0.01
panel_removal_max = 2

# Background adding
background_add_chance = 0.5 # 0.01

# **Speech bubbles**
max_speech_bubbles_per_panel = 5
bubble_to_panel_area_min_ratio = 0.2
bubble_to_panel_area_max_ratio = 0.4
bubble_to_character_area_min_ratio = 0.3
bubble_to_character_area_max_ratio = 0.6
min_bubble_size = 12
bubble_mask_x_increase = 15
bubble_mask_y_increase = 15
min_font_size = 24
max_font_size = 72

# **Characters**
overlap_offset = 24
max_characters_per_panel = 5
character_bubble_speech_freq = 0.65
object_to_panel_area_max_ratio = 0.4
min_character_size = 8

# *Transformations*

# Slicing
slice_transform_chance = 0.75
double_slice_chance = 0.25
slice_minimum_panel_area = 0.3 #0.35
center_side_ratio = 0.7

# Box transforms
box_transform_chance = 0.75
box_transform_panel_chance = 0.1
panel_box_trapezoid_ratio = 0.2

# How much at most should the trapezoid/rhombus start from
# as a ratio of the smallest panel's width or height
trapezoid_movement_limit = 50
rhombus_movement_limit = 50

# Circular panels
circular_panel_probability = 0.5

full_page_movement_proportion_limit = 25

# Other
texture_probability = 0.5
