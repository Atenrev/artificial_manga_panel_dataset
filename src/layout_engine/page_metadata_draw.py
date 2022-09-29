import numpy as np

import src.config_file as cfg
from src.layout_engine.helpers import (
    invert_for_next, choose, choose_and_return_other,
)
from src.layout_engine.page_objects import Panel
from src.layout_engine.page_metadata_transforms import *
from src.layout_engine.page_objects import Panel, Page
from src.layout_engine.page_metadata_draw import *


def get_base_panels(num_panels=0,
                    layout_type=None,
                    type_choice=None,
                    page_name=None):
    """
    This function creates the base panels for one page
    it specifies how a page should be layed out and
    how many panels should be in it

    :param num_panels: how many panels should be on a page
    if 0 then the function chooses, defaults to 0

    :type num_panels: int, optional

    :param layout_type: whether the page should consist of
    vertical, horizontal or both types of panels, defaults to None

    :type layout_type: str, optional

    :param type_choice: If having selected vh panels select a type
    of layout specifically, defaults to None

    :type type_choice: str, optional

    :param page_name: A specific name for the page

    :type page_name: str, optional

    :return: A Page object with the panels initalized

    :rtype: Page
    """

    # TODO: Skew panel number distribution

    # Page dimensions turned to coordinates
    topleft = (0.0, 0.0)
    topright = (cfg.page_width, 0.0)
    bottomleft = (0.0, cfg.page_height)
    bottomright = cfg.page_size
    coords = [
        topleft,
        topright,
        bottomright,
        bottomleft
    ]

    if layout_type is None:
        layout_type = np.random.choice(["v", "h", "vh"])

    # Panels encapsulated and returned within page
    if page_name is None:
        page = Page(coords, layout_type, num_panels)
    else:
        page = Page(coords, layout_type, num_panels, name=page_name)

    # If you want only vertical panels
    if layout_type == "v":
        max_num_panels = 4
        if num_panels < 1:
            num_panels = np.random.choice([3, 4])
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels
        
        draw_n_shifted(num_panels, page, "v")

    # If you want only horizontal panels
    elif layout_type == "h":
        max_num_panels = 5
        if num_panels < 1:
            num_panels = np.random.randint(3, max_num_panels+1)
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels

        draw_n_shifted(num_panels, page, "h")

    # If you want both horizontal and vertical panels
    elif layout_type == "vh":

        max_num_panels = 8

        if num_panels < 1:
            num_panels = np.random.randint(2, max_num_panels+1)
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels

        if num_panels <= 2:
            # Draw 2 rectangles
            # vertically or horizontally
            horizontal_vertical = np.random.choice(["h", "v"])
            draw_n_shifted(num_panels, page, horizontal_vertical)

        elif num_panels == 3:
            # Draw 2 rectangles
            # Vertically or Horizontally

            horizontal_vertical = np.random.choice(["h", "v"])
            draw_two_shifted(page, horizontal_vertical)

            next_div = invert_for_next(horizontal_vertical)

            # Pick one and divide it into 2 rectangles
            choice_idx = choose(page)
            choice = page.get_child(choice_idx)

            draw_two_shifted(choice, next_div)

        elif num_panels == 4:
            horizontal_vertical = np.random.choice(["h", "v"])

            # Possible layouts with 4 panels
            if type_choice is None:
                type_choice = np.random.choice(["eq", "uneq", "div",
                                                "trip", "twoonethree"])

            # Draw two rectangles
            if type_choice == "eq":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide each into 2 rectangles equally
                shift_min = 25
                shift_max = 75
                shift = np.random.randint(shift_min, shift_max)
                shift = shift/100

                draw_two_shifted(page.get_child(0), next_div, shift)
                draw_two_shifted(page.get_child(1), next_div, shift)

            # Draw two rectangles
            elif type_choice == "uneq":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide each into 2 rectangles unequally
                draw_two_shifted(page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

            elif type_choice == "div":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick one and divide into 2 rectangles
                choice1_idx = choose(page)
                choice1 = page.get_child(choice1_idx)

                draw_two_shifted(choice1, next_div)

                # Pick one of these two and divide that into 2 rectangles
                choice2_idx = choose(choice1)
                choice2 = choice1.get_child(choice2_idx)

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice2, next_div)

            # Draw three rectangles
            elif type_choice == "trip":
                draw_n(3, page, horizontal_vertical)

                # Pick one and divide it into two
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)

                draw_two_shifted(choice, next_div)

            # Draw two rectangles
            elif type_choice == "twoonethree":

                draw_two_shifted(page, horizontal_vertical)

                # Pick one and divide it into 3 rectangles
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)

                draw_n_shifted(3, choice, next_div)

        elif num_panels == 5:

            # Draw two rectangles
            horizontal_vertical = np.random.choice(["h", "v"])

            # Possible layouts with 5 panels
            if type_choice is None:
                type_choice = np.random.choice(["eq", "uneq", "div",
                                                "twotwothree", "threetwotwo",
                                                "fourtwoone"])

            if type_choice == "eq" or type_choice == "uneq":

                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick one and divide it into two then
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                draw_two_shifted(choice, next_div)

                # Divide each into 2 rectangles equally
                if type_choice == "eq":
                    shift_min = 25
                    shift_max = 75
                    shift = np.random.randint(shift_min, shift_max)
                    set_shift = shift/100
                else:
                    # Divide each into 2 rectangles unequally
                    set_shift = None

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice.get_child(0),
                                 next_div,
                                 shift=set_shift)

                draw_two_shifted(choice.get_child(1),
                                 next_div,
                                 shift=set_shift)

            # Draw two rectangles
            elif type_choice == "div":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide both equally
                draw_two_shifted(page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

                # Pick one of all of them and divide into two
                page_child_chosen = np.random.choice(page.children)
                choice_idx, left_choices = choose_and_return_other(
                    page_child_chosen
                )

                choice = page_child_chosen.get_child(choice_idx)

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice,
                                 horizontal_vertical=next_div,
                                 shift=0.5
                                 )

            # Draw two rectangles
            elif type_choice == "twotwothree":

                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick which one gets 2 and which gets 3
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                # Divide one into 2
                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice, next_div)

                # Divide other into 3
                draw_n(3, other, next_div)

            # Draw 3 rectangles (horizontally or vertically)
            elif type_choice == "threetwotwo":

                draw_n(3, page, horizontal_vertical)
                next_div = invert_for_next(horizontal_vertical)

                choice1_idx, left_choices = choose_and_return_other(page)
                choice2_idx = np.random.choice(left_choices)
                choice1 = page.get_child(choice1_idx)
                choice2 = page.get_child(choice2_idx)

                # Pick two and divide each into two
                draw_two_shifted(choice1, next_div)
                draw_two_shifted(choice2, next_div)

            # Draw 4 rectangles vertically
            elif type_choice == "fourtwoone":
                draw_n(4, page, horizontal_vertical)

                # Pick one and divide into two
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice, next_div)

        elif num_panels == 6:

            # Possible layouts with 6 panels
            if type_choice is None:
                type_choice = np.random.choice(["tripeq", "tripuneq",
                                                "twofourtwo", "twothreethree",
                                                "fourtwotwo"])

            horizontal_vertical = np.random.choice(["v", "h"])

            # Draw 3 rectangles (V OR H)
            if type_choice == "tripeq" or type_choice == "tripuneq":
                draw_n_shifted(3, page, horizontal_vertical)
                # Split each equally
                if type_choice == "tripeq":
                    shift = np.random.randint(25, 75)
                    shift = shift/100
                # Split each unequally
                else:
                    shift = None

                next_div = invert_for_next(horizontal_vertical)
                for panel in page.children:
                    draw_two_shifted(panel, next_div, shift=shift)

            # Draw 2 rectangles
            elif type_choice == "twofourtwo":
                draw_two_shifted(page, horizontal_vertical)
                # Split into 4 one half 2 in another
                next_div = invert_for_next(horizontal_vertical)
                draw_n_shifted(4, page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

            # Draw 2 rectangles
            elif type_choice == "twothreethree":
                # Split 3 in each
                draw_two_shifted(page, horizontal_vertical)
                next_div = invert_for_next(horizontal_vertical)

                for panel in page.children:
                    # Allow each inital panel to grow to up to 75% of 100/n
                    n = 3
                    shifts = []
                    choice_max = round((100/n)*1.5)
                    choice_min = round((100/n)*0.5)
                    for i in range(0, n):
                        shift_choice = np.random.randint(
                            choice_min,
                            choice_max
                        )

                        choice_max = choice_max + ((100/n) - shift_choice)
                        shifts.append(shift_choice)

                    to_add_or_remove = (100 - sum(shifts))/len(shifts)

                    normalized_shifts = []
                    for shift in shifts:
                        new_shift = shift + to_add_or_remove
                        normalized_shifts.append(new_shift/100)

                    draw_n_shifted(3,
                                   panel,
                                   next_div,
                                   shifts=normalized_shifts
                                   )

            # Draw 4 rectangles
            elif type_choice == "fourtwotwo":
                draw_n_shifted(4, page, horizontal_vertical)

                # Split two of them
                choice1_idx, left_choices = choose_and_return_other(page)
                choice2_idx = np.random.choice(left_choices)
                choice1 = page.get_child(choice1_idx)
                choice2 = page.get_child(choice2_idx)

                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice1, next_div)
                draw_two_shifted(choice2, next_div)

        elif num_panels == 7:

            # Possible layouts with 7 panels
            types = ["twothreefour", "threethreetwotwo", "threefourtwoone",
                     "threethreextwoone", "fourthreextwo"]

            if type_choice is None:
                type_choice = np.random.choice(types)

            # Draw two split 3-4 - HV
            # Draw two rectangles
            if type_choice == "twothreefour":
                horizontal_vertical = np.random.choice(["h", "v"])

                draw_two_shifted(page, horizontal_vertical, shift=0.5)

                # Pick one and split one into 4 rectangles
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                next_div = invert_for_next(horizontal_vertical)

                draw_n_shifted(4, choice, next_div)

                # Some issue with the function calls and seeding
                n = 3
                shifts = []
                choice_max = round((100/n)*1.5)
                choice_min = round((100/n)*0.5)
                for i in range(0, n):
                    shift_choice = np.random.randint(choice_min, choice_max)
                    choice_max = choice_max + ((100/n) - shift_choice)
                    shifts.append(shift_choice)

                to_add_or_remove = (100 - sum(shifts))/len(shifts)

                normalized_shifts = []
                for shift in shifts:
                    new_shift = shift + to_add_or_remove
                    normalized_shifts.append(new_shift/100)

                # Pick another and split into 3 rectangles
                draw_n_shifted(3, other, next_div, shifts=normalized_shifts)

            # Draw three rectangles
            elif type_choice == "threethreetwotwo":
                draw_n(3, page, "h")

                # Pick one and split it into 3 rectangles
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)

                draw_n_shifted(3, choice, "v")

                # Split the other two into 2 rectangles
                draw_two_shifted(page.get_child(left_choices[0]), "v")
                draw_two_shifted(page.get_child(left_choices[1]), "v")

            # Draw 3 rectangles
            elif type_choice == "threefourtwoone":
                draw_n(3, page, "h")

                # Pick two of three rectangles and let one be
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other_idx = np.random.choice(left_choices)
                other = page.get_child(other_idx)

                # Of the picked split one into 4 rectangles
                draw_n_shifted(4, choice, "v")

                # Split the other into 2 rectangles
                draw_two_shifted(other, "v")

            # Draw 3 rectangles
            elif type_choice == "threethreextwoone":

                draw_n(3, page, "h")

                # Pick two and leave one
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                # Of the picked split one into 3
                draw_n_shifted(3, choice, "v")

                # Some issue with the function calls and seeding
                n = 3
                shifts = []
                choice_max = round((100/n)*1.5)
                choice_min = round((100/n)*0.5)
                for i in range(0, n):
                    shift_choice = np.random.randint(choice_min, choice_max)
                    choice_max = choice_max + ((100/n) - shift_choice)
                    shifts.append(shift_choice)

                to_add_or_remove = (100 - sum(shifts))/len(shifts)

                normalized_shifts = []
                for shift in shifts:
                    new_shift = shift + to_add_or_remove
                    normalized_shifts.append(new_shift/100)

                # Split the other into 3 as well
                draw_n_shifted(3, other, "v", shifts=normalized_shifts)

            # Draw 4 split 3x2 - HV

            # Draw 4 rectangles
            elif type_choice == "fourthreextwo":
                horizontal_vertical = np.random.choice(["h", "v"])
                draw_n(4, page, horizontal_vertical)

                # Choose one and leave as is
                choice_idx, left_choices = choose_and_return_other(page)

                # Divide the rest into two
                next_div = invert_for_next(horizontal_vertical)
                for panel in left_choices:
                    draw_two_shifted(page.get_child(panel), next_div)

        elif num_panels == 8:

            # Possible layouts for 8 panels
            types = ["fourfourxtwoeq", "fourfourxtwouneq",
                     "threethreethreetwo", "threefourtwotwo",
                     "threethreefourone"]

            if type_choice is None:
                type_choice = np.random.choice(types)

            # Draw 4 rectangles
            # equal or uneqal 4-4x2
            if type_choice == types[0] or type_choice == types[1]:
                # panels = draw_n_shifted(4, *coords, "h")
                draw_n(4, page, "h")
                # Equal
                if type_choice == "fourfourxtwoeq":
                    shift_min = 25
                    shift_max = 75
                    shift = np.random.randint(shift_min, shift_max)
                    set_shift = shift/100
                # Unequal
                else:
                    set_shift = None

                # Drivide each into two
                for panel in page.children:

                    draw_two_shifted(panel, "v", shift=set_shift)

            # Where three rectangles need to be drawn
            if type_choice in types[2:]:
                draw_n(3, page, "h")

                # Draw 3 rectangles then
                if type_choice == "threethreethreetwo":

                    # Choose one and divide it into two
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)
                    draw_two_shifted(choice, "v")

                    # Divide the rest into 3
                    for panel in left_choices:
                        # Some issue with the function calls and seeding
                        n = 3
                        shifts = []
                        choice_max = round((100/n)*1.5)
                        choice_min = round((100/n)*0.5)
                        for i in range(0, n):
                            shift_choice = np.random.randint(
                                choice_min,
                                choice_max
                            )

                            choice_max = choice_max + ((100/n) - shift_choice)
                            shifts.append(shift_choice)

                        to_add_or_remove = (100 - sum(shifts))/len(shifts)

                        normalized_shifts = []
                        for shift in shifts:
                            new_shift = shift + to_add_or_remove
                            normalized_shifts.append(new_shift/100)

                        draw_n_shifted(3,
                                       page.get_child(panel),
                                       "v",
                                       shifts=normalized_shifts
                                       )

                # Draw 3 rectangles then
                elif type_choice == "threefourtwotwo":

                    # Choosen one and divide it into 4
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)

                    draw_n_shifted(4, choice, "v")

                    for panel in left_choices:
                        draw_two_shifted(page.get_child(panel), "v")

                # Draw 3 3-4-1 - H

                # Draw three rectangles then
                elif type_choice == "threethreefourone":

                    # Choose two and leave one as is
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)
                    other_idx = np.random.choice(left_choices)
                    other = page.get_child(other_idx)

                    # Divide one into 3 rectangles
                    draw_n_shifted(3, choice, "v")

                    # Some issue with the function calls and seeding
                    n = 4
                    shifts = []
                    choice_max = round((100/n)*1.5)
                    choice_min = round((100/n)*0.5)
                    for i in range(0, n):
                        shift_choice = np.random.randint(
                            choice_min,
                            choice_max
                        )

                        choice_max = choice_max + ((100/n) - shift_choice)
                        shifts.append(shift_choice)

                    to_add_or_remove = (100 - sum(shifts))/len(shifts)

                    normalized_shifts = []
                    for shift in shifts:
                        new_shift = shift + to_add_or_remove
                        normalized_shifts.append(new_shift/100)

                    # Divide the other into 4 rectangles
                    draw_n_shifted(4, other, "v", shifts=normalized_shifts)
        else:
            horizontal_n = np.random.randint(2, num_panels // 2)
            draw_n(horizontal_n, page, "h")

            # vertical_n = num_panels
            vertical_ns = []

            for _ in range(horizontal_n):
                # n = np.random.randint(1, vertical_n - horizontal_n + 1)
                n = np.random.randint(1, num_panels // 2)
                # horizontal_n -= 1
                # vertical_n -= n
                vertical_ns.append(n)

            # Drivide each into two
            for i, panel in enumerate(page.children):
                draw_n_shifted(vertical_ns[i], panel, "v")

    return page


# Creation helpers
def draw_n_shifted(n, parent, horizontal_vertical, shifts=[]):
    """
    A function to take a parent Panel and divide it into n
    sub-panel's vertically or horizontally with each panels having
    specified size ratios along the axis perpendicular to their orientation

    NOTE: This function performs actions by reference

    :param n: Number of sub-panels

    :type n: int

    :param parent: The parent panel being split

    :type parent: Panel

    :param horizontal_vertical: Whether to render the sub-panels vertically
    or horizontally in regards to the page

    :type horizontal_vertical: str

    :param shifts: Ratios to divide the panel into sub-panels

    :type shifts: list
    """

    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    if n == 1:
        poly_coords = (topleft, topright, bottomright, bottomleft, topleft)
        panel = Panel(poly_coords,
                        parent.name+"-0",
                        orientation=horizontal_vertical,
                        parent=parent,
                        children=[]
                        )

        parent.add_child(panel)
        # parent.leaf_children.append(panel)
        return parent

    # Allow each inital panel to grow to up to 150% of 100/n
    # which would be all panel's equal.
    # This is then normalized down to a smaller number
    choice_max = round((100/n)*1.5)
    choice_min = round((100/n)*0.5)

    normalized_shifts = []

    # If there are no ratios specified
    if len(shifts) < 1:
        shifts = []
        for i in range(0, n):
            # Randomly select a size for the new panel's side
            shift_choice = np.random.randint(choice_min, choice_max)
            # Change the maximum range acoording to available length
            # of the parent panel's size
            choice_max = choice_max + ((100/n) - shift_choice)

            # Append the shift
            shifts.append(shift_choice)

        # Amount of length to add or remove
        to_add_or_remove = (100 - sum(shifts))/len(shifts)

        # Normalize panels such that the shifts all sum to 1.0
        for shift in shifts:
            new_shift = shift + to_add_or_remove
            normalized_shifts.append(new_shift/100)
    else:
        normalized_shifts = shifts

    # If the panel is horizontal to the page
    if horizontal_vertical == "h":
        shift_level = 0.0

        # For each new panel
        for i in range(0, n):
            # If it's the first panel then it's
            # has the same left side as the parent top side
            if i == 0:
                x1y1 = topleft
                x2y2 = topright

            # If not it has the same top side as it's previous
            # sibiling's bottom side
            else:
                # this shift level is the same as the bottom side
                # of the sibling panel
                shift_level += normalized_shifts[i-1]

                # Specify points for the top side
                x1y1 = (bottomleft[0],
                        topleft[1] +
                        (bottomleft[1] - topleft[1])*shift_level)

                x2y2 = (bottomright[0],
                        topright[1] +
                        (bottomright[1] - topright[1])*shift_level)

            # If it's the last panel then it has the
            # same right side as the parent bottom side
            if i == (n-1):
                x3y3 = bottomright
                x4y4 = bottomleft

            # If not it has the same bottom side as it's next
            # sibling's top side
            else:
                # Same shift level as the left side of next sibling
                next_shift_level = shift_level + normalized_shifts[i]

                # Specify points for the bottom side
                x3y3 = (bottomright[0], topright[1] +
                        (bottomright[1] - topright[1])*next_shift_level)

                x4y4 = (bottomleft[0], topleft[1] +
                        (bottomleft[1] - topleft[1])*next_shift_level)

            # Create a Panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)

    # If the panel is vertical
    if horizontal_vertical == "v":
        shift_level = 0.0

        # For each new panel
        for i in range(0, n):

            # If it's the first panel it has the same
            # top side as the parent's left side
            if i == 0:
                x1y1 = topleft
                x4y4 = bottomleft

            # if not it's left side is the same as it's
            # previous sibling's right side
            else:
                # Same shift level as the right side of previous sibling
                shift_level += normalized_shifts[i-1]

                # Specify points for left side
                x1y1 = (topleft[0] +
                        (topright[0] - topleft[0])*shift_level,
                        topright[1])

                x4y4 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*shift_level,
                        bottomright[1])

            # If it's the last panel i thas the same
            # right side as it's parent panel
            if i == (n-1):
                x2y2 = topright
                x3y3 = bottomright

            # If not then it has the same right side as it's next sibling's
            # left side
            else:
                # Same shift level as next sibling's left side
                next_shift_level = shift_level + normalized_shifts[i]

                # Specify points for right side
                x2y2 = (topleft[0] +
                        (topright[0] - topleft[0])*next_shift_level,
                        topright[1])

                x3y3 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*next_shift_level,
                        bottomright[1])

            # Create a panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)


def draw_n(n, parent, horizontal_vertical):
    """
    A function to take a parent Panel and divide it into n
    sub-panels vertically or horizontally with each panels having
    equal size ratios along the axis perpendicular to their orientation


    NOTE: This function performs actions by reference

    :param n: Number of sub-panels

    :type n: int

    :param parent: The parent panel being split

    :type parent: Panel

    :param horizontal_vertical: Whether to render the sub-panels vertically
    or horizontally in regards to the page

    :type horizontal_vertical: str
    """
    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    # if input out of bounds i.e. 1:
    if n == 1:
        poly_coords = (topleft, topright, bottomright, bottomleft, topleft)
        panel = Panel(poly_coords,
                        parent.name+"-0",
                        orientation=horizontal_vertical,
                        parent=parent,
                        children=[]
                        )

        parent.add_child(panel)

    # If the panel is horizontal to the page
    if horizontal_vertical == "h":

        # For each new panel
        for i in range(0, n):

            # If it's the first panel then it's
            # has the same left side as the parent top side
            if i == 0:
                x1y1 = topleft
                x2y2 = topright
            # If not it has the same top side as its
            # previous sibiling's bottom side
            else:

                # Specify points for the top side
                # Since it's equally divided the size is dictated by (i/n)
                x1y1 = (bottomleft[0],
                        topleft[1] + (bottomleft[1] - topleft[1])*(i/n))

                x2y2 = (bottomright[0],
                        topright[1] + (bottomright[1] - topright[1])*(i/n))

            # If it's the last panel then it has the
            # same right side as the parent bottom side
            if i == (n-1):
                x3y3 = bottomright
                x4y4 = bottomleft

            # If not it has the same bottom side as it's
            # next sibling's top side
            else:
                # Specify points for the bottom side
                # Since it's equally divided the size is dictated by (i/n)
                x3y3 = (bottomright[0],
                        topright[1] + (bottomright[1] - topright[1])*((i+1)/n))
                x4y4 = (bottomleft[0],
                        topleft[1] + (bottomleft[1] - topleft[1])*((i+1)/n))

            # Create a Panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)

    # If the panel is vertical
    if horizontal_vertical == "v":
        # For each new panel
        for i in range(0, n):

            # If it's the first panel it has the same
            # top side as the parent's left side
            if i == 0:
                x1y1 = topleft
                x4y4 = bottomleft

            # If not it's left side is the same as it's
            # previous sibling's right side
            else:
                # Specify points for left side
                # Since it's equally divided the size is dictated by (i/n)
                x1y1 = (topleft[0] +
                        (topright[0] - topleft[0])*(i/n),
                        topright[1])

                x4y4 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*(i/n),
                        bottomright[1])

            # If it's the last panel i thas the same
            # right side as it's parent panel
            if i == (n-1):
                x2y2 = topright
                x3y3 = bottomright

            # If not then it has the same right side as it's next sibling's
            # left side
            else:
                # Specify points for right side
                # Since it's equally divided the size is dictated by (i/n)
                x2y2 = (topleft[0] +
                        (topright[0] - topleft[0])*((i+1)/n),
                        topright[1])

                x3y3 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*((i+1)/n),
                        bottomright[1])

            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)


def draw_two_shifted(parent, horizontal_vertical, shift=None):
    """
    Draw two subpanels of a parent panel

    :param parent: The parent panel to be split

    :type parent: Parent

    :param horizontal_vertical: Orientation of sub-panels in refrence
    to the page

    :type horizontal_vertical: str

    :param shift: by what ratio should the 2 panels be split, defaults to None

    :type shift: float, optional
    """

    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    # If shift's are not specified select them
    if shift is None:
        shift_min = 25
        shift_max = 75
        shift = np.random.randint(shift_min, shift_max)
        shift = shift/100

    # If panel is horizontal
    if horizontal_vertical == "h":

        # Spcify the first panel's coords
        r1x1y1 = topleft
        r1x2y2 = topright
        r1x3y3 = (bottomright[0],
                  topright[1] + (bottomright[1] - topright[1])*shift)
        r1x4y4 = (bottomleft[0],
                  topleft[1] + (bottomleft[1] - topleft[1])*shift)

        poly1_coords = (r1x1y1, r1x2y2, r1x3y3, r1x4y4, r1x1y1)

        # Specify the second panel's coords
        r2x1y1 = (bottomleft[0],
                  topleft[1] + (bottomleft[1] - topleft[1])*shift)
        r2x2y2 = (bottomright[0],
                  topright[1] + (bottomright[1] - topright[1])*shift)

        r2x3y3 = bottomright
        r2x4y4 = bottomleft

        poly2_coords = (r2x1y1, r2x2y2, r2x3y3, r2x4y4, r2x1y1)

        # Create panels
        poly1 = Panel(poly1_coords,
                      parent.name + "-0",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        poly2 = Panel(poly2_coords,
                      parent.name + "-1",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        parent.add_children([poly1, poly2])

    # If the panel is vertical
    if horizontal_vertical == "v":

        # Specify the first panel's coords
        r1x1y1 = topleft
        r1x2y2 = (topleft[0] + (topright[0] - topleft[0])*shift, topright[1])
        r1x3y3 = (bottomleft[0] + (bottomright[0] - bottomleft[0])*shift,
                  bottomright[1])
        r1x4y4 = bottomleft

        poly1_coords = (r1x1y1, r1x2y2, r1x3y3, r1x4y4, r1x1y1)

        # Specify the second panel's coords
        r2x1y1 = (topleft[0] + (topright[0] - topleft[0])*shift, topright[1])
        r2x2y2 = topright
        r2x3y3 = bottomright
        r2x4y4 = (bottomleft[0] + (bottomright[0] - bottomleft[0])*shift,
                  bottomright[1])

        poly2_coords = (r2x1y1, r2x2y2, r2x3y3, r2x4y4, r2x1y1)

        # Create panels
        poly1 = Panel(poly1_coords,
                      parent.name + "-0",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        poly2 = Panel(poly2_coords,
                      parent.name + "-1",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        parent.add_children([poly1, poly2])