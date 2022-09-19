import numpy as np
import math
import random
import pyclipper

import src.config_file as cfg
from src.layout_engine.page_objects import Page
from src.layout_engine.helpers import (
    get_leaf_panels,
    get_min_area_panels,
    find_parent_with_multiple_children,
    move_children_to_line
)
from src.layout_engine.page_metadata_draw import *


# Page transformations
def single_slice_panels(page: Page,
                        horizontal_vertical=None,
                        type_choice=None,
                        skew_side=None,
                        number_to_slice=0
                        ):
    """Slices a panel once at an angle into two new panels

    :param page: Page to have panels sliced

    :type page: Page

    :param horizontal_vertical:  Whether the slice should be horizontal
    or vertical

    :type horizontal_vertical: str

    :param type_choice: Specify whether the panel should be
    sliced down the "center" or on a "side", defaults to None

    :type type_choice: str, optional

    :param skew_side: Based on the type of slicing which direction should
    it be sliced

    :type skew_side: str

    :param number_to_slice: Number of panels to slice

    :type number_to_slice: int

    :return: page with sliced panels

    :rtype: Page
    """

    # Remove panels which are too small
    relevant_panels = []
    if len(page.children) > 0:
        get_min_area_panels(page,
                            cfg.slice_minimum_panel_area,
                            ret_panels=relevant_panels
                            )
    else:
        relevant_panels = [page]

    # Shuffle panels for randomness
    random.shuffle(relevant_panels)

    # single slice close
    if type_choice is None:
        type_choice_prob = np.random.random()
        if type_choice_prob < cfg.center_side_ratio:
            type_choice = "center"
        else:
            type_choice = "side"

    num_panels_added = 0

    # Slice panels down the center
    if type_choice == "center":
        if len(relevant_panels) < 1:
            return page

        if number_to_slice == 0:
            if len(relevant_panels) > 1:
                number_to_slice = np.random.randint(1, len(relevant_panels))
            else:
                number_to_slice = 1

        for idx in range(number_to_slice):
            panel = relevant_panels[idx]
            num_panels_added += 1

            # Decide which direction to cut in
            if horizontal_vertical is None:
                horizontal_vertical = np.random.choice(["h", "v"])

            # Skew it by a percentage
            skew_amount = np.random.randint(25, 100)/100

            # Get center line
            # Vertical slice
            if horizontal_vertical == "v":
                panel_chosen_coord_length = (panel.x2y2[0] - panel.x1y1[0])/2

                # Slice panel
                draw_n(2, panel, "v")

                # Skew it left or right
                if skew_side is None:
                    skew_side = np.random.choice(["left", "right", "center"])

                skew_amount = skew_amount*panel_chosen_coord_length

                # Perform transform
                p1 = panel.get_child(0)
                p2 = panel.get_child(1)

                # Panels are non standard polygons
                p1.non_rect = True
                p2.non_rect = True

                p1.sliced = True
                p2.sliced = True

                if skew_side == "left":
                    p1.x2y2 = (p1.x2y2[0] - skew_amount, p1.x2y2[1])
                    p1.x3y3 = (p1.x3y3[0] + skew_amount, p1.x3y3[1])

                    p1.refresh_coords()

                    p2.x1y1 = (p2.x1y1[0] - skew_amount, p2.x1y1[1])
                    p2.x4y4 = (p2.x4y4[0] + skew_amount, p2.x4y4[1])

                    p2.refresh_coords()

                elif skew_side == "right":
                    p1.x2y2 = (p1.x2y2[0] + skew_amount, p1.x2y2[1])
                    p1.x3y3 = (p1.x3y3[0] - skew_amount, p1.x3y3[1])

                    p1.refresh_coords()

                    p2.x1y1 = (p2.x1y1[0] + skew_amount, p2.x1y1[1])
                    p2.x4y4 = (p2.x4y4[0] - skew_amount, p2.x4y4[1])

                    p2.refresh_coords()

                elif skew_side == "center":
                    skew_amount = skew_amount // 2
                    num_vertex = np.random.randint(3, 10)
                    height = p1.x3y3[1] - p1.x2y2[1]
                    height_n = height // (num_vertex - 1)
                    p1_coords = []

                    for v in range(num_vertex):
                        if v % 2 == 0:
                            skam = -skew_amount
                        else:
                            skam = skew_amount

                        xy = (p1.x2y2[0] + skam, p1.x2y2[1] + height_n * v)
                        p1_coords.append(xy)

                    p1.coords = [
                        p1.x1y1,
                        *p1_coords,
                        p1.x4y4,
                        p1.x1y1
                    ]
                    p1.refresh_size()

                    p2_coords = []

                    for v in range(num_vertex):
                        if v % 2 == 0:
                            skam = -skew_amount
                        else:
                            skam = skew_amount

                        xy = (p2.x1y1[0] + skam, p2.x1y1[1] + height_n * v)
                        p2_coords.insert(0, xy)

                    p2.coords = [
                        p2_coords[-1],
                        p2.x2y2,
                        p2.x3y3,
                        *p2_coords
                    ]
                    p2.refresh_size()

                else:
                    raise Exception("Incorrect skew side chosen")

            # Horizontal slice
            else:
                panel_chosen_coord_length = (panel.x3y3[1] - panel.x2y2[1])/2

                # Slice panel
                draw_n(2, panel, "h")

                # Skew it left or right
                if skew_side is None:
                    skew_side = np.random.choice(["down", "up", "center"])

                skew_amount = skew_amount*panel_chosen_coord_length

                p1 = panel.get_child(0)
                p2 = panel.get_child(1)

                # Panels are non standard polygons
                p1.non_rect = True
                p2.non_rect = True

                p1.sliced = True
                p2.sliced = True
                if skew_side == "down":
                    p1.x4y4 = (p1.x4y4[0], p1.x4y4[1] + skew_amount)
                    p1.x3y3 = (p1.x3y3[0], p1.x3y3[1] - skew_amount)

                    p1.refresh_coords()

                    p2.x1y1 = (p2.x1y1[0], p2.x1y1[1] + skew_amount)
                    p2.x2y2 = (p2.x2y2[0], p2.x2y2[1] - skew_amount)

                    p2.refresh_coords()

                elif skew_side == "up":
                    p1.x4y4 = (p1.x4y4[0], p1.x4y4[1] - skew_amount)
                    p1.x3y3 = (p1.x3y3[0], p1.x3y3[1] + skew_amount)

                    p1.refresh_coords()

                    p2.x1y1 = (p2.x1y1[0], p2.x1y1[1] - skew_amount)
                    p2.x2y2 = (p2.x2y2[0], p2.x2y2[1] + skew_amount)

                    p2.refresh_coords()
                
                elif skew_side == "center":
                    skew_amount = skew_amount // 2
                    num_vertex = np.random.randint(3, 10)
                    width = p1.x3y3[0] - p1.x4y4[0]
                    width_n = width // (num_vertex - 1)
                    p1_coords = []

                    for v in range(num_vertex):
                        if v % 2 == 0:
                            skam = -skew_amount
                        else:
                            skam = skew_amount

                        xy = (p1.x4y4[0] + width_n * v, p1.x4y4[1] + skam)
                        p1_coords.insert(0, xy)

                    p1.coords = [
                        p1.x1y1,
                        p1.x2y2,
                        *p1_coords,
                        p1.x1y1
                    ]
                    p1.refresh_size()

                    p2_coords = []

                    for v in range(num_vertex):
                        if v % 2 == 0:
                            skam = -skew_amount
                        else:
                            skam = skew_amount

                        xy = (p2.x1y1[0] + width_n * v, p2.x1y1[1] + skam)
                        p2_coords.append(xy)

                    p2.coords = [
                        *p2_coords,
                        p2.x3y3,
                        p2.x4y4,
                        p2_coords[0]
                    ]
                    p2.refresh_size()

                else:
                    print("Chose incorrect skew_side")

    # Slice panel sides
    else:
        if len(relevant_panels) < 1:
            return page

        if number_to_slice == 0:
            if len(relevant_panels) > 1:
                number_to_slice = np.random.choice([1, 3])
            else:
                number_to_slice = 1

        for panel in relevant_panels[0:number_to_slice]:

            if skew_side is None:
                skew_side = np.random.choice(["tr", "tl", "br", "bl"])

            draw_n(2, panel, "h")
            num_panels_added += 1

            p1 = panel.get_child(0)
            p2 = panel.get_child(1)

            # Panels are non standard polygons
            p1.non_rect = True
            p2.non_rect = True

            p1.sliced = True
            p2.sliced = True

            cut_y_proportion = np.random.randint(25, 75)/100
            cut_x_proportion = np.random.randint(25, 75)/100

            cut_y_length = (panel.x4y4[1] - panel.x1y1[1])*cut_y_proportion
            cut_x_length = (panel.x3y3[0] - panel.x4y4[0])*cut_x_proportion

            # bottom left corner
            if skew_side == "bl":
                p1_cut_x1y1 = (panel.x4y4[0], panel.x4y4[1] - cut_y_length)
                p1_cut_x2y2 = (panel.x4y4[0] + cut_x_length, panel.x4y4[1])
                p1_cut_x3y3 = (panel.x4y4)

                p1.coords = [p1_cut_x1y1, p1_cut_x2y2,
                             p1_cut_x3y3, p1_cut_x1y1]

                p2.coords = [panel.x1y1, panel.x2y2, panel.x3y3,
                             p1_cut_x2y2, p1_cut_x1y1, panel.x1y1]

            # bottom right corner
            elif skew_side == "br":
                p1_cut_x1y1 = (panel.x3y3[0], panel.x3y3[1] - cut_y_length)
                p1_cut_x2y2 = (panel.x3y3)
                p1_cut_x3y3 = (panel.x3y3[0] - cut_x_length, panel.x3y3[1])

                p1.coords = [p1_cut_x1y1, p1_cut_x2y2,
                             p1_cut_x3y3, p1_cut_x1y1]

                p2.coords = [panel.x1y1, panel.x2y2, p1_cut_x1y1,
                             p1_cut_x3y3, panel.x4y4, panel.x1y1]

            # top left corner
            elif skew_side == "tl":
                p1_cut_x1y1 = panel.x1y1
                p1_cut_x2y2 = (panel.x1y1[0] + cut_x_length, panel.x1y1[1])
                p1_cut_x3y3 = (panel.x1y1[0], panel.x1y1[1] + cut_y_length)

                p1.coords = [p1_cut_x1y1, p1_cut_x2y2,
                             p1_cut_x3y3, p1_cut_x1y1]
                p2.coords = [p1_cut_x2y2, panel.x2y2, panel.x3y3,
                             panel.x4y4, p1_cut_x3y3, p1_cut_x2y2]

            # top right corner
            elif skew_side == "tr":
                p1_cut_x1y1 = (panel.x2y2[0] - cut_x_length, panel.x2y2[1])
                p1_cut_x2y2 = panel.x2y2
                p1_cut_x3y3 = (panel.x2y2[0], panel.x2y2[1] + cut_y_length)

                p1.coords = [p1_cut_x1y1, p1_cut_x2y2,
                             p1_cut_x3y3, p1_cut_x1y1]

                p2.coords = [panel.x1y1, p1_cut_x1y1, p1_cut_x3y3,
                             panel.x3y3, panel.x4y4, panel.x1y1]
            else:
                raise Exception("Incorrect skew side chosen")


    page.num_panels += num_panels_added

    return page


def box_transform_panels(page: Page, type_choice=None, pattern=None):
    """
    This function move panel boundaries to transform them
    into trapezoids and rhombuses

    :param page: Page to be transformed

    :type page: Page

    :param type_choice: If you want to specify
    a particular transform type: rhombus or trapezoid, defaults to None

    :type type_choice: str, optional

    :param pattern: Based on the type choice choose a pattern.
    For rhombus it's left or right, for trapezoid it's A or V
    defaults to None

    :type pattern: str, optional

    :return: Transformed Page

    :rtype: Page
    """

    if type_choice is None:
        type_choice_prob = np.random.random()
        if type_choice_prob < cfg.panel_box_trapezoid_ratio:
            type_choice = "trapezoid"
        else:
            type_choice = "rhombus"

    if type_choice == "trapezoid":
        if page.num_panels <= 2:
            return page

        # Get parent panel which satisfies the criteria for the transform
        relevant_panels = find_parent_with_multiple_children(page, 3)

        if len(relevant_panels) > 0:
            if len(relevant_panels) > 1:
                num_panels = np.random.randint(1, len(relevant_panels)+1)
            else:
                num_panels = 1

            # For each panel
            for idx in range(num_panels):
                panel = relevant_panels[idx]

                # Get the three child panels
                # Since panels are created in order
                p1 = panel.get_child(0)
                p2 = panel.get_child(1)
                p3 = panel.get_child(2)

                # Panels are non standard polygons
                p1.non_rect = True
                p2.non_rect = True
                p3.non_rect = True

                min_width = math.inf
                min_height = math.inf

                # Get the smallest height and width
                for child in [p1, p2, p3]:

                    if child.width < min_width:
                        min_width = child.width

                    if child.height < min_height:
                        min_height = child.height

                # Choose trapezoid pattern
                if pattern is None:
                    trapezoid_pattern = np.random.choice(["A", "V"])
                else:
                    trapezoid_pattern = pattern

                movement_proportion = np.random.randint(
                    10,
                    cfg.trapezoid_movement_limit)

                # If parent panel is horizontal the children are vertical
                if panel.orientation == "h":

                    # Get how much the lines of the child panels move
                    # on the x axis to make the trapezoid
                    x_movement = min_width*(movement_proportion/100)

                    # Make an A pattern horizontally
                    if trapezoid_pattern == "A":

                        # Get the coords of the first line to be moved
                        line_one_top = (p1.x2y2[0] + x_movement,
                                        p1.x2y2[1])

                        line_one_bottom = (p1.x3y3[0] - x_movement,
                                            p1.x3y3[1])

                        # Move line between child 1 and 2
                        p1.x2y2 = line_one_top
                        p1.x3y3 = line_one_bottom

                        p1.refresh_coords()

                        p2.x1y1 = line_one_top
                        p2.x4y4 = line_one_bottom

                        # Get the coords of the second line to be moved
                        line_two_top = (p2.x2y2[0] - x_movement,
                                        p2.x2y2[1])
                        line_two_bottom = (p2.x3y3[0] + x_movement,
                                            p2.x3y3[1])

                        # Move line two between child 2 and 3
                        p2.x2y2 = line_two_top
                        p2.x3y3 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_top
                        p3.x4y4 = line_two_bottom

                        p3.refresh_coords()

                    # Make a V pattern horizontally
                    else:

                        # Get the coords of the first line to be moved
                        line_one_top = (p1.x2y2[0] - x_movement,
                                        p1.x2y2[1])

                        line_one_bottom = (p1.x3y3[0] + x_movement,
                                            p1.x3y3[1])

                        # Move line between child 1 and 2
                        p1.x2y2 = line_one_top
                        p1.x3y3 = line_one_bottom

                        p1.refresh_coords()

                        p2.x1y1 = line_one_top
                        p2.x4y4 = line_one_bottom

                        # Get the coords of the second line to be moved
                        line_two_top = (p2.x2y2[0] + x_movement,
                                        p2.x2y2[1])

                        line_two_bottom = (p2.x3y3[0] - x_movement,
                                            p2.x3y3[1])

                        # Move line two between child 2 and 3
                        p2.x2y2 = line_two_top
                        p2.x3y3 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_top
                        p3.x4y4 = line_two_bottom

                        p3.refresh_coords()

                # If panel is vertical children are horizontal
                # so the A and the V are at 90 degrees to the page
                else:
                    # Get how much the lines of the child panels move
                    # on the y axis to make the trapezoid
                    y_movement = min_height*(movement_proportion/100)

                    # Make an A pattern vertically
                    if trapezoid_pattern == "A":

                        # Get the coords of the first line to be moved
                        line_one_top = (p2.x2y2[0],
                                        p2.x2y2[1] + y_movement)

                        line_one_bottom = (p2.x1y1[0],
                                            p2.x1y1[1] - y_movement)

                        # Move line between child 1 and 2
                        p2.x2y2 = line_one_top
                        p2.x1y1 = line_one_bottom

                        p1.x3y3 = line_one_top
                        p1.x4y4 = line_one_bottom

                        p1.refresh_coords()

                        # Get the coords of the second line to be moved
                        line_two_top = (p2.x3y3[0],
                                        p2.x3y3[1] - y_movement)

                        line_two_bottom = (p2.x4y4[0],
                                            p2.x4y4[1] + y_movement)

                        # Move line two between child 2 and 3
                        p2.x3y3 = line_two_top
                        p2.x4y4 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_bottom
                        p3.x2y2 = line_two_top

                        p3.refresh_coords()
                    # Make a V pattern vertically
                    else:

                        # Get the coords of the first line to be moved
                        line_one_top = (p2.x2y2[0],
                                        p2.x2y2[1] - y_movement)

                        line_one_bottom = (p2.x1y1[0],
                                            p2.x1y1[1] + y_movement)

                        # Move line between child 1 and 2
                        p2.x2y2 = line_one_top
                        p2.x1y1 = line_one_bottom

                        p1.x3y3 = line_one_top
                        p1.x4y4 = line_one_bottom

                        p1.refresh_coords()
                        # Get the coords of the second line to be moved
                        line_two_top = (p2.x3y3[0],
                                        p2.x3y3[1] + y_movement)

                        line_two_bottom = (p2.x4y4[0],
                                            p2.x4y4[1] - y_movement)

                        # Move line two between child 2 and 3
                        p2.x3y3 = line_two_top
                        p2.x4y4 = line_two_bottom

                        p2.refresh_coords()
                        p3.x1y1 = line_two_bottom
                        p3.x2y2 = line_two_top

                        p3.refresh_coords()

    elif type_choice == "rhombus":

        if page.num_panels <= 1:
            return page

        # Get parent panel which satisfies the criteria for the transform
        relevant_panels = find_parent_with_multiple_children(page, 3)

        if len(relevant_panels) > 0:

            if len(relevant_panels) > 1:
                num_panels = np.random.randint(1, len(relevant_panels))
            else:
                num_panels = 1

            for idx in range(0, num_panels):

                panel = relevant_panels[idx]

                # Since panels are created in order
                p1 = panel.get_child(0)
                p2 = panel.get_child(1)
                p3 = panel.get_child(2)

                # Panels are non standard polygons
                p1.non_rect = True
                p2.non_rect = True
                p3.non_rect = True

                min_width = math.inf
                min_height = math.inf

                # Get the smallest height and width
                for child in [p1, p2, p3]:

                    if child.width < min_width:
                        min_width = child.width

                    if child.height < min_height:
                        min_height = child.height

                if pattern is None:
                    rhombus_pattern = np.random.choice(["left", "right"])
                else:
                    rhombus_pattern = pattern

                movement_proportion = np.random.randint(
                    10,
                    cfg.rhombus_movement_limit
                )

                # Logic for the section below is the same as the
                # trapezoid with the exception of the fact that the
                # rhombus pattern happens to move both lines in the
                # same direction

                if panel.orientation == "h":

                    x_movement = min_width*(movement_proportion/100)

                    if rhombus_pattern == "left":
                        line_one_top = (p1.x2y2[0] - x_movement,
                                        p1.x2y2[1])

                        line_one_bottom = (p1.x3y3[0] + x_movement,
                                            p1.x3y3[1])

                        p1.x2y2 = line_one_top
                        p1.x3y3 = line_one_bottom

                        p1.refresh_coords()

                        p2.x1y1 = line_one_top
                        p2.x4y4 = line_one_bottom

                        line_two_top = (p2.x2y2[0] - x_movement,
                                        p2.x2y2[1])

                        line_two_bottom = (p2.x3y3[0] + x_movement,
                                            p2.x3y3[1])

                        p2.x2y2 = line_two_top
                        p2.x3y3 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_top
                        p3.x4y4 = line_two_bottom

                        p3.refresh_coords()

                    else:

                        line_one_top = (p1.x2y2[0] + x_movement,
                                        p1.x2y2[1])

                        line_one_bottom = (p1.x3y3[0] - x_movement,
                                            p1.x3y3[1])

                        p1.x2y2 = line_one_top
                        p1.x3y3 = line_one_bottom

                        p1.refresh_coords()

                        p2.x1y1 = line_one_top
                        p2.x4y4 = line_one_bottom

                        line_two_top = (p2.x2y2[0] + x_movement,
                                        p2.x2y2[1])

                        line_two_bottom = (p2.x3y3[0] - x_movement,
                                            p2.x3y3[1])

                        p2.x2y2 = line_two_top
                        p2.x3y3 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_top
                        p3.x4y4 = line_two_bottom

                        p3.refresh_coords()
                else:
                    y_movement = min_height*(movement_proportion/100)

                    if rhombus_pattern == "right":

                        line_one_top = (p2.x2y2[0],
                                        p2.x2y2[1] + y_movement)

                        line_one_bottom = (p2.x1y1[0],
                                            p2.x1y1[1] - y_movement)

                        p2.x2y2 = line_one_top
                        p2.x1y1 = line_one_bottom

                        p1.x3y3 = line_one_top
                        p1.x4y4 = line_one_bottom

                        p1.refresh_coords()

                        line_two_top = (p2.x3y3[0],
                                        p2.x3y3[1] + y_movement)

                        line_two_bottom = (p2.x4y4[0],
                                            p2.x4y4[1] - y_movement)

                        p2.x3y3 = line_two_top
                        p2.x4y4 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_bottom
                        p3.x2y2 = line_two_top

                        p3.refresh_coords()
                    else:

                        line_one_top = (p2.x2y2[0],
                                        p2.x2y2[1] - y_movement)

                        line_one_bottom = (p2.x1y1[0],
                                            p2.x1y1[1] + y_movement)

                        p2.x2y2 = line_one_top
                        p2.x1y1 = line_one_bottom

                        p1.x3y3 = line_one_top
                        p1.x4y4 = line_one_bottom

                        p1.refresh_coords()

                        line_two_top = (p2.x3y3[0],
                                        p2.x3y3[1] - y_movement)

                        line_two_bottom = (p2.x4y4[0],
                                            p2.x4y4[1] + y_movement)

                        p2.x3y3 = line_two_top
                        p2.x4y4 = line_two_bottom

                        p2.refresh_coords()

                        p3.x1y1 = line_two_bottom
                        p3.x2y2 = line_two_top

                        p3.refresh_coords()

    return page


def box_transform_page(page: Page, direction_list=[]):
    """
    This function takes all the first child panels of a page
    and moves them to form a zigzag or a rhombus pattern

    :param page: Page to be transformed

    :type page: Page

    :param direction_list: A list of directions the page
    should move it's child panel's corner's to

    :return: Transformed page

    :rtype: Page
    """

    if len(page.children) > 1:

        # For all children of the page
        for idx in range(0, len(page.children)-1):

            # Take two children at a time
            p1 = page.get_child(idx)
            p2 = page.get_child(idx+1)

            p1.non_rect = True
            p2.non_rect = True

            change_proportion = np.random.randint(
                10,
                cfg.full_page_movement_proportion_limit
            )

            change_proportion /= 100

            # Randomly move the line between them up or down one side
            if len(direction_list) < 1:
                direction = np.random.choice(["rup", "lup"])
            else:
                direction = direction_list[idx]

            # If the first panel is horizontal therefore the second is too
            if p1.orientation == "h":

                # Get the maximum amount the line can move
                change_max = min([(p1.x4y4[1] - p1.x1y1[1]),
                                  (p2.x4y4[1] - p2.x1y1[1])])

                change = change_max*change_proportion

                # Specify the line to move
                line_top = p2.x1y1
                line_bottom = p2.x2y2

                # If the panel has children then recursively
                # find the leaf children and move them to the new line
                if len(p1.children) > 0:
                    move_children_to_line(p1,
                                          (line_top, line_bottom),
                                          change,
                                          "h",
                                          direction
                                          )

                # Otherwise move the current panels to line
                else:
                    if direction == "rup":
                        p1.x4y4 = (p1.x4y4[0], p1.x4y4[1] + change)
                        p1.refresh_coords()
                    else:
                        p1.x4y4 = (p1.x4y4[0], p1.x4y4[1] - change)
                        p1.refresh_coords()

                if len(p2.children) > 0:
                    move_children_to_line(p2,
                                          (line_top, line_bottom),
                                          change,
                                          "h",
                                          direction
                                          )
                else:
                    if direction == "rup":
                        p2.x1y1 = (p2.x1y1[0], p2.x1y1[1] + change)
                        p2.refresh_coords()
                    else:
                        p2.x1y1 = (p2.x1y1[0], p2.x1y1[1] - change)
                        p2.refresh_coords()

            # If the first panel is vertical therefore the second
            # is too since they are siblings
            else:
                # Get the maximum amount the line can move
                change_max = min([(p1.x2y2[0] - p1.x1y1[0]),
                                  (p2.x2y2[0] - p2.x1y1[0])])

                change = change_max*change_proportion

                # Specify the line to move
                line_top = p2.x1y1
                line_bottom = p2.x4y4

                # If the panel has children then recursively
                # find the leaf children and move them to the new line
                if len(p1.children) > 0:
                    move_children_to_line(p1,
                                          (line_top, line_bottom),
                                          change,
                                          "v",
                                          direction
                                          )

                # Otherwise just move the panel since it's a leaf
                else:
                    if direction == "rup":
                        p1.x2y2 = (p1.x2y2[0] - change, p1.x2y2[1])
                    else:
                        p1.x2y2 = (p1.x2y2[0] + change, p1.x2y2[1])

                if len(p2.children) > 0:
                    move_children_to_line(p2,
                                          (line_top, line_bottom),
                                          change,
                                          "v",
                                          direction
                                          )
                else:
                    if direction == "rup":
                        p2.x1y1 = (p2.x1y1[0] - change, p2.x1y1[1])
                    else:
                        p2.x1y1 = (p2.x1y1[0] + change, p2.x1y1[1])

    return page


def circular_transform_panels(page: Page):
    for panel in page.children:
        if panel.non_rect or panel.sliced:
            continue

        panel.circular = np.random.random() < cfg.circular_panel_probability

    return page


def add_transforms(page: Page):
    """Adds panel boundary transformations
    to the page

    :param page: Page to be transformed

    :type page: Page

    :return: Page with transformed panels

    :rtype: Page
    """
    # Transform types

    # Allow choosing multiple
    transform_choice = ["slice", "box", "circular"]

    # Slicing panels into multiple panels
    # Works best with large panels
    if "slice" in transform_choice and np.random.random() < cfg.slice_transform_chance:
        transform_choice.pop(2)
        page = single_slice_panels(page)

        # Makes v cuts happen more often 1/4 chance
        if np.random.random() < cfg.double_slice_chance:
            page = single_slice_panels(page)
        
        return page

    if "box" in transform_choice and np.random.random() < cfg.box_transform_chance:
        if len(transform_choice) > 2:
            transform_choice.pop(2)

        if np.random.random() < cfg.box_transform_panel_chance:
            page = box_transform_panels(page)

        page = box_transform_page(page)

    if "circular" in transform_choice:
        page = circular_transform_panels(page)

    return page


def shrink_panels(page):
    """
    A function that uses the pyclipper library]
    to reduce the size of the panel polygon

    :param page: Page whose panels are to be
    shrunk

    :type page: Page

    :return: Page with shrunk panels

    :rtype: Page
    """

    panels = []
    if len(page.leaf_children) < 1:
        get_leaf_panels(page, panels)
        page.leaf_children = panels
    else:
        panels = page.leaf_children

    panel_shrink_amount = np.random.randint(
        cfg.panel_shrink_amount_min, cfg.panel_shrink_amount_max)

    # For each panel
    for panel in panels:
        # Shrink them
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(panel.get_polygon(),
                    pyclipper.JT_ROUND,
                    pyclipper.ET_CLOSEDPOLYGON
                    )

        solution = pco.Execute(panel_shrink_amount)

        # Get the solutions
        changed_coords = []
        if len(solution) > 0:
            for item in solution[0]:
                changed_coords.append(tuple(item))

            changed_coords.append(changed_coords[0])

            # Assign them
            panel.coords = changed_coords
            panel.x1y1 = changed_coords[0]
            panel.x2y2 = changed_coords[1]
            panel.x3y3 = changed_coords[2]
            panel.x4y4 = changed_coords[3]
        else:
            # Assign them as is if there are no solutions
            pass

    return page


def remove_panel(page):
    """
    This function randomly removes
    a panel from pages which have
    more than n+1 panels

    :param page: Page to remove panels from

    :type page: Page

    :return: Page with panels removed

    :rtype: Page
    """

    # If page has > n+1 children so there's
    # at least 1 panel left
    if page.num_panels > cfg.panel_removal_max + 1:

        # Remove 1 to n panels
        remove_number = np.random.choice([1, cfg.panel_removal_max])

        # Remove panel
        for i in range(remove_number):
            page.leaf_children.pop()

    return page