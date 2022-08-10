# **Page rendering**
page_width = 1200
page_height = 1700

page_size = (page_width, page_height)

output_format = ".png"

boundary_width = 15
boundary_color = "black"

# **Font coverage**
# How many characters of the dataset should the font files support
font_character_coverage = 0.80


# **Panel Drawing**
# *Panel ratios*

# TODO: Figure out page type distributions
num_pages_ratios = {
    1: 0.125,
    2: 0.125,
    3: 0.125,
    4: 0.125,
    5: 0.125,
    6: 0.125,
    7: 0.125,
    8: 0.125
}

vertical_horizontal_ratios = {
    "v": 0.1,
    "h": 0.1,
    "vh": 0.8
}

solid_background_probability = 0.75

# Panel transform chance

panel_transform_chance = 0.30

# Panel shrinking

panel_shrink_amount = -25

# Panel removal

panel_removal_chance = 0.01
panel_removal_max = 2

# Background adding
background_add_chance = 0.8 # 0.01

# **Speech bubbles**
max_speech_bubbles_per_panel = 2
bubble_to_panel_area_max_ratio = 0.4
bubble_to_panel_object_area_max_ratio = 0.8
bubble_mask_x_increase = 15
bubble_mask_y_increase = 15
min_font_size = 54
max_font_size = 72

# **Panel objects**
object_to_panel_area_max_ratio = 0.4
max_panel_objects_per_panel = 2

# *Transformations*

# Slicing
double_slice_chance = 0.25
slice_minimum_panel_area = 0.2
center_side_ratio = 0.7

# Box transforms
box_transform_panel_chance = 0.1
panel_box_trapezoid_ratio = 0.2

# How much at most should the trapezoid/rhombus start from
# as a ratio of the smallest panel's width or height
trapezoid_movement_limit = 50
rhombus_movement_limit = 50

full_page_movement_proportion_limit = 25
