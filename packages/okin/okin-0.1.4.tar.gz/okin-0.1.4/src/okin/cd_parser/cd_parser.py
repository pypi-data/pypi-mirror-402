import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from random import randint
from xml.dom import minidom
import numpy as np
import itertools

from okin.base.chem_logger import chem_logger

"""
cd = chemdraw
- Texts and stoichiometric factors are considered 'texts'
- Text and Chemicals are considered 'fragments'
- Arrows can be tilted. 'fragments' might have trouble to detect everything properly if
    they are rotated (Bounding boxes are the scaled ones from cd file and they do not rotate)

# """
from okin.cd_parser.CDClasses.cd_chem import CDChem

from okin.cd_parser.CDClasses.cd_arrow import CDArrow
from okin.cd_parser.CDClasses.cd_line import CDLine
from okin.cd_parser.CDClasses.cd_reaction import CDReaction
from okin.cd_parser.CDClasses.cd_text import CDText

# ! important difference when reading variable names:
# center = point between 2 points
# mid_ = area that is in the middle of something


# TODO Et + Et is realized as 2 Et and not as Et (current state)
# TODO Fix collision detection if you feel like it

class CDParser():
    def __init__(self, file_path, draw=True):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.draw = draw
        self.file_path = file_path
        self.logger.debug(f"using chemdraw file: {file_path}")
        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()
        self.page = self.root.find("page")
        # print(self.root.text)


        # arrows = self.root.findall('.//arrow')
        # for arrow in arrows:
        #     print(ET.tostring(arrow).decode())

    def draw_arrow_rectangle(self, center, major, minor, color="8"):
        #! add a bb for an arrow that can be tilted
        center_str = " ".join([str(round(coord, 2)) for coord in center])+" 0"
        major_str = " ".join([str(round(coord, 2)) for coord in major])+" 0"
        minor_str = " ".join([str(round(coord, 2)) for coord in minor])+" 0"

        new_graphic = Element("graphic")
        # not the smartest thing ever but it works. Not even sure if it crashes when
        # 2 ids are the same
        new_graphic.set("id", str(randint(10000, 10000000))) # id cannot collide with anything in the original document
        new_graphic.set("BoundingBox", "0 0 0 0")
        new_graphic.set("Z", "20")
        new_graphic.set("color", color)
        new_graphic.set("GraphicType", "Rectangle")
        new_graphic.set("RectangleType", "Plain")
        new_graphic.set("Center3D", center_str)
        new_graphic.set("MajorAxisEnd3D", major_str)
        new_graphic.set("MinorAxisEnd3D", minor_str)

        self.page.append(new_graphic)

    def draw_rectangle(self, bb, color="3"):
        #! add rectangle to visualize bb
        
        if len(bb) == 4:
            bb_list = [list(bb[0]) + list(bb[2])][0]

        elif type(bb) == np.ndarray:
            bb_list = [list(bb[0]) + list(bb[1])][0]
        else:
            bb_list = bb

        new_graphic = Element("graphic")
        new_graphic.set("id", str(randint(10000, 10000000)))
        new_graphic.set("BoundingBox", " ".join(
            [str(coord) for coord in bb_list]))
        new_graphic.set("Z", "18")
        new_graphic.set("color", color)
        new_graphic.set("GraphicType", "Rectangle")
        new_graphic.set("RectangleType", "Plain")

        self.page.append(new_graphic)

    def write_rectangle(self):
        #! write the changes made in self.draw_(arrow_)rectangle into a file
        new_xml = minidom.parseString(ET.tostring(self.root))
        if self.file_path.endswith(".cdxml"):
            cut_off = 6
        elif self.file_path.endswith(".cdx"):
            cut_off = 4
        file_name = self.file_path[:-cut_off] + "_show_borders.cdxml"

        try:
            with open(file_name, 'w') as xml_file:
                new_xml.writexml(xml_file)
        except:
            raise Exception(
                "___\nPlease close the cd file with the boxes and try again.")

    def end_collision_detection(self, rect1, rect2):
        #! make sure both rects have 4 points to them
        # FOR RECT1
        rect1_lx = min( [p[0] for p in rect1] )
        rect1_ly = max( [p[1] for p in rect1] )
        rect1_rx = max([p[0] for p in rect1] )
        rect1_ry = min( [p[1] for p in rect1] )

        # FOR RECT 2
        rect2_lx = min( [p[0] for p in rect2] )
        rect2_ly = max( [p[1] for p in rect2] )
        rect2_rx = max( [p[0] for p in rect2] )
        rect2_ry = min( [p[1] for p in rect2] )

        #! check collision
        # check if rect2 in rect1
        for p in rect2:
            x, y = p

            x_overlap = (x >= rect1_lx and x <= rect1_rx) or (
                x <= rect1_lx and x >= rect1_rx)
            # swapped here
            y_overlap = (y >= rect1_ly and y <= rect1_ry) or (y <= rect1_ly and y >=rect1_ry)
            isOverlap = x_overlap and y_overlap
            if isOverlap:
                return True

        # check if rect1 in rect2
        for p in rect1:
            x, y = p
            x_overlap = (x >= rect2_lx and x <= rect2_rx) or (
                x <= rect2_lx and x >= rect2_rx)
            y_overlap = (y >= rect2_ly and y <= rect2_ry) or (
                y <= rect1_ly and y >= rect1_ry)
            isOverlap = x_overlap and y_overlap
            if isOverlap:
                return True

        return False

    def collision_detection(self, rect1, rect2):
        #! checks if the 2 rectangles overlap
        # bb2 = rectangle object (bounding box) with 2 points (top_left, bot_right)
        # lx = left_x , ry = right_y

        def get_all_rect_points(rect):
            #! adds missing points so that there are all 4 bb points instead of 2
            top_left = rect[0]
            bot_right = rect[1]
            bot_left = np.array([rect[0][0], rect[1][1]])
            top_right = np.array([rect[1][0], rect[0][1]])
            new_rect1 = np.array(
                [list(top_left)] + [list(bot_right)]+[list(bot_left)]+[list(top_right)])
            return new_rect1

        #! make sure both rects have 4 points to them
        # FOR RECT1
        if len(rect1) == 2:
            # get all 4 points of rectangle
            rect1 = get_all_rect_points(rect1)
            rect1_lx, rect1_ly = rect1[0]
            rect1_rx, rect1_ry = rect1[1]
        else:
            rect1_lx, rect1_ly = rect1[0]
            rect1_rx, rect1_ry = rect1[2]

        if len(rect1) != 4:
            raise Exception(
                f"your rect1_bb format is broken. Please enter a valid_ bb with 2 or 4 points")

        # FOR RECT 2
        if len(rect2) == 2:
            # get all 4 points of rectangle
            rect2 = get_all_rect_points(rect2)
            rect2_lx, rect2_ly = rect2[0]
            rect2_rx, rect2_ry = rect2[1]
        else:
            rect2_lx, rect2_ly = rect2[0]
            rect2_rx, rect2_ry = rect2[2]

        if len(rect2) != 4:
            raise Exception(
                f"your rect2_bb format is broken. Please enter a valid_ bb with 2 or 4 points")

        #! check collision
        # check if rect2 in rect1
        for p in rect2:
            x, y = p
            x_overlap = (x >= rect1_lx and x <= rect1_rx) or (
                x <= rect1_lx and x >= rect1_rx)
            y_overlap = (y >= rect1_ly and y <= rect1_ry)
            isOverlap = x_overlap and y_overlap
            if isOverlap:
                return True

        # check if rect1 in rect2
        for p in rect1:
            x, y = p
            x_overlap = (x >= rect2_lx and x <= rect2_rx) or (
                x <= rect2_lx and x >= rect2_rx)
            y_overlap = (y >= rect2_ly and y <= rect2_ry)
            isOverlap = x_overlap and y_overlap
            if isOverlap:
                return True

        return False

    def mid_collision_detection(self, mid_bb, mid_bb2):
        rx, ry = mid_bb[0]
        r1x, r1y = mid_bb[1]
        lx, ly = mid_bb[2]
        l1x, l1y = mid_bb[3]

        for p in mid_bb2:
            x, y = p
            x_overlap = (x >= lx and x <= rx) or (x <= lx and x >= rx) or (x >= l1x and x <= r1x) or (x <= l1x and x >= r1x)
            y_overlap = (y >= ly and y <= ry) or (y <= ly and y >= ry) or (y >= l1y and y <= r1y) or (y <= l1y and y >= r1y)

            if x_overlap and y_overlap:
                return True

        # also do the other way round cause it is possible to miss it if you just check if one is in the other
        rx, ry = mid_bb2[0]
        r1x, r1y = mid_bb2[1]
        lx, ly = mid_bb2[2]
        l1x, l1y = mid_bb2[3]

        for p in mid_bb:
            x, y = p
            x_overlap = (x >= lx and x <= rx) or (x <= lx and x >= rx) or (x >= l1x and x <= r1x) or (x <= l1x and x >= r1x)
            y_overlap = (y >= ly and y <= ry) or (y <= ly and y >= ry) or (y >= l1y and y <= r1y) or (y <= l1y and y >= r1y)
            if x_overlap and y_overlap:
                return True


        return False
            
    def get_mid_point(self, points):
        # returns mid_ point between 2 points
        x_mid_point = (points[0][0] + points[1][0]) / 2
        y_mid_point = (points[0][1] + points[1][1]) / 2
        mid_point = np.array([x_mid_point, y_mid_point])
        return mid_point

    def assign_stoichiometric_factors(self):

        def get_distance_2v(v1, v2):
            # returns distance between 2 vectors
            return np.linalg.norm(v1-v2)

        def stoic_detection(s_fac):
            #! matches stoichiometric factors (s_fac) with ZERO or ONE fragment
            top_right_fac = np.array([s_fac.bb[1][0], s_fac.bb[0][1]])
            bot_right_fac = s_fac.bb[1]
            points_of_fac = np.array([top_right_fac, bot_right_fac])
            mid_point_fac = self.get_mid_point(s_fac.bb)

            # all fragments that overlap with the s_fac
            possible_frags = []

            for frag in self.fragments:
                mid_point_frag = self.get_mid_point(frag.bb)
                top_left_frag = frag.bb[0]
                bot_left_frag = np.array([frag.bb[0][0], frag.bb[1][1]])
                points_of_frag = np.array([top_left_frag, bot_left_frag])

                # check if right side of num is between left side of chem_bb and mid_chem_line
                # -> stoic_factor has to be on the right side of the chem
                # also s_fac.bb should not be bigger than frag.bb
                # also both points_of_num have to be in frag.bb

                x_overlap = (top_right_fac[0] > top_left_frag[0]) and (top_right_fac[0] < mid_point_frag[0])
                y_overlap_1 = (top_right_fac[1] > top_left_frag[1]) and (top_right_fac[1] < bot_left_frag[1])
                y_overlap_2 = (bot_right_fac[1] > top_left_frag[1]) and (bot_right_fac[1] < bot_left_frag[1])

                # change second 'and' to 'or' if you want only one point to be in chem_bb for match
                # I did_ thit for default
                if x_overlap and y_overlap_1 or y_overlap_2:
                    distance_mid_to_mid_ = get_distance_2v(
                        mid_point_frag, mid_point_fac)
                    possible_frags.append([frag, distance_mid_to_mid_])

            matched_frag = None
            # set arbitrary high value
            distance = 4096
            # get the closest fragment from the possible_frags
            for possible_frag in possible_frags:
                if possible_frag[1] < distance:
                    distance = possible_frag[1]
                    matched_frag = possible_frag[0]

            return matched_frag

        # get all stoichiometric factors on the page
        stoic_factors = [
            stoic_f for stoic_f in self.fragments if stoic_f.what_am_i == "stoic_f"]

        # find matching fragment for each stoic factor and add stoic fac to the label
        for s_fac in stoic_factors:
            # returs frag with shortest distance and collision detection
            matched_frag = stoic_detection(s_fac)
            # Do not write 1 as stoic factor
            if matched_frag and (s_fac.factor != 1):
                # set "label" to "{stoic_fac} label"
                matched_frag.label = f"{s_fac.factor} " + matched_frag.label

    def parse_arrows(self, draw=True):
        arrows = self.page.findall("arrow")
        graphics = self.page.findall("graphic")
        arrow_list = []
        line_list = []

        print(graphics)

        for xml_arrow in arrows:
            if "ArrowheadHead" in xml_arrow.attrib:
                arrow = CDArrow(xml_arrow, graphics)
                arrow_list.append(arrow)
            else:
                line = CDLine(xml_arrow, graphics)
                line_list.append(line)
                

        self.arrow_list = arrow_list
        self.line_list = line_list

    def parse_fragments(self):
        chems = self.page.findall("fragment")
        texts = self.page.findall("t")

        chem_list = []
        text_list = []

        for xml_txt in texts:
            text = CDText(xml_txt)
            text_list.append(text)

        for xml_frag in chems:
            chem = CDChem(xml_frag)
            chem_list.append(chem)

        self.chems = chem_list
        self.texts = text_list
        self.fragments = chem_list + text_list

    def _draw_debugging_ends(self, bb):
        # self.draw_arrow_rectangle(arrow.head_center, arrow.head_major, arrow.head_minor)
        # self.draw_arrow_rectangle(arrow.tail_center, arrow.tail_major, arrow.tail_minor)
        self.draw_rectangle(np.array([bb[0]+1, bb[0]-1]), color="3")
        self.draw_rectangle(np.array([bb[1]+1, bb[1]-1]), color="4")
        self.draw_rectangle(np.array([bb[2]+1, bb[2]-1]), color="6")
        self.draw_rectangle(np.array([bb[3]+1, bb[3]-1]), color="8")

        self.write_rectangle()

    def draw_everything(self, draw_educt=True, draw_product=True, draw_head=True, draw_tail=True, draw_mid=True, draw_frag=True, draw_debug=False):
        
        for arrow in self.arrow_list + self.line_list:

            if draw_debug:
                self._draw_debugging_ends(arrow.head_bb)
                self._draw_debugging_ends(arrow.tail_bb)
                self._draw_debugging_ends(arrow.mid_bb)
            
            # lines do not have 
            if draw_mid and arrow.what_am_i == "arrow": 
                self.draw_arrow_rectangle(arrow.mid_center, arrow.mid_major, arrow.mid_minor, color="8")

            if draw_educt:
                self.draw_arrow_rectangle(arrow.educt_center, arrow.educt_major, arrow.educt_minor, color="8")

            if draw_product:
                self.draw_arrow_rectangle(
                    arrow.product_center, arrow.product_major, arrow.product_minor, color="8")

            if draw_head:
                self.draw_arrow_rectangle(arrow.head_center, arrow.head_major, arrow.head_minor, color="6")
                
            if draw_tail:
                self.draw_arrow_rectangle(arrow.tail_center, arrow.tail_major, arrow.tail_minor, color="5")
            

        if draw_frag:
            for frag in self.fragments:
                self.draw_rectangle(frag.bb, color="3")

        # write them to file
        self.write_rectangle()

    def find_reactions(self, draw=True):

        def delete_stoichiometric_factors(list_):
            return [frag for frag in list_ if frag.what_am_i != "stoic_f"]

        def get_chained_frags(frags_to_check):
            #! returns a list of all fragments with overlapping bounding boxes
            # already connected fragments aka all that are in arrow bb
            all_connected_frags = frags_to_check.copy()
            # keep track which fragments have been checked already by id
            frags_checked = [frag.id_ for frag in frags_to_check]

            
            while len(frags_to_check) != 0:
                curr_frag = frags_to_check.pop(0)

                # check for all currently connected fragments if they connect with any other fragment on the page
                for frag in self.fragments:
                    is_connected = self.collision_detection(
                        curr_frag.bb, frag.bb)

                    if is_connected and frag.id_ not in frags_checked:
                        all_connected_frags.append(frag)
                        frags_checked.append(frag.id_)
                        frags_to_check.append(frag)
            return all_connected_frags

        def combine_lines_and_arrows(all_combinations, reactions):

            for arrow, line in all_combinations:
                is_educt = self.mid_collision_detection(arrow.mid_bb, line.head_bb)
                is_product = self.mid_collision_detection(arrow.mid_bb, line.tail_bb)
                
                if is_educt or is_product:
                    # get the 2 reactions from these arrows
                    first_rct = None
                    scnd_rct = None
                    for rct in reactions:
                        if rct.id_ == arrow.id_:
                            first_rct = rct
                        if rct.id_ == line.id_:
                            scnd_rct = rct
                    # combine educts/products and delete the now duplicate
                    # multiple matches make it crash when they try to delete a reaction the second time
                    try:
                        if is_educt:
                            first_rct.educts += scnd_rct.educts
                            reactions.remove(scnd_rct)
                        if is_product:
                            first_rct.products += scnd_rct.products
                            reactions.remove(scnd_rct)
                            
                    except:
                        pass
            return reactions

        def combine_arrows(all_arrow_combinations, reactions):
            # check each arrow with each other arrow once
            for arrow1, arrow2 in all_arrow_combinations:
                 #! disabled this function:
                 # if 2 arrow heads collide the educts are combined C->A<-B --> "B + C -> A"

                #! HEEEEEEREEEE 
                # okay let me explain. please:
                # is_also_educt seems to get triggered from double cycle so that it breaks
                # the whole combining_arrows routine. Also noone combines arrows like this in catalysis
                # so this function is (hopefully) not needed.
                # I tested a bit and I believe this is a leftover from the only-straight-arrow version
                # as there is nothing that does not work as intended.
                is_also_product = False
                is_also_educt = False

                #* UNCOMMENT here to turn it back on

                # is_also_educt = self.end_collision_detection(
                #     arrow1.head_bb, arrow2.head_bb) or self.end_collision_detection(
                #     arrow1.tail_bb, arrow2.head_bb)
                
                # # if arrow head and arrow tail overlap the products are combined  C<-A->B --> "A -> B + C"
                # is_also_product = self.end_collision_detection(
                #     arrow1.head_bb, arrow2.tail_bb)

                


                # if "mid_bb" in dir(arrow1) and "mid_bb" in dir(arrow2):
                is_mid_overlap = self.mid_collision_detection(arrow1.mid_bb, arrow2.mid_bb)

                # only do stuff if there was a match
                if is_also_educt or is_also_product or is_mid_overlap:
                    # get the 2 reactions from these arrows
                    first_rct = None
                    scnd_rct = None
                    for rct in reactions:
                        if rct.id_ == arrow1.id_:
                            first_rct = rct
                        if rct.id_ == arrow2.id_:
                            scnd_rct = rct
                    # combine educts/products and delete the now duplicate
                    # multiple matches make it crash when they try to delete a reaction the second time

                    # print("\n_____________\n")
                    # print(f"combining [{first_rct}] and [{scnd_rct}]")
                    # print(is_also_educt, is_also_product, is_mid_overlap)

                    try:                        
                        if is_mid_overlap:
                            first_rct.educts += scnd_rct.educts
                            first_rct.products += scnd_rct.products

                        elif is_also_educt:
                            first_rct.educts += scnd_rct.educts

                        elif is_also_product:
                            first_rct.products += scnd_rct.products
                        
                        reactions.remove(scnd_rct)

                    except:
                        pass
            return reactions

        #! As I reread this I have no idea why this is here. I'll comment it out (2023_10_23)
        #! It is not 2024_08_12 and I am still baffled. i think I'll delete it next time I come across it
        # def combine_sum_formula_dict(sum_formula_dict):
        #     if "H" in sum_formula_dict.keys():
        #         if sum_formula_dict["H"] == 0:
        #             del self.sum_formula_dict["H"]
        
        #         str_sum_formula = ""
        #         for key, value in sorted(sum_formula_dict.items()):
        #             # charge should be last thing to be added so just store value and add after loop
        #             if key == "charge":
        #                 charge = value
        #                 continue

        #             str_sum_formula += str(key)
        #             if value != 1:
        #                 str_sum_formula += str(value)

        #         if "charge" in sum_formula_dict.keys():
        #             if charge != 0:
        #                 # another beauty of python to add sign to charge
        #                 str_sum_formula += f"{{{'{0:+}'.format(charge)}}}"

        #         return str_sum_formula

        self.parse_arrows()
        self.parse_fragments()
        reactions = []

        for arrow in self.arrow_list + self.line_list:
            educts = []
            products = []
            

            # see if arrow collides with a fragment
            for frag in self.fragments:
                # check if fragment overlaps on either side and sort
                is_educt = self.collision_detection(arrow.educt_bb, frag.bb)
                is_product = self.collision_detection(arrow.product_bb, frag.bb)
                # print(f"for frag: {frag}\nis_educt: {is_educt}\nis_product: {is_product}\n_______")

                if arrow.what_am_i == "arrow":
                    is_topside = self.collision_detection(arrow.mid_bb, frag.bb)
                else:
                    is_topside = False

                if is_educt or is_topside:
                    educts.append(frag)
                    #! WAS THIS continue important?? if it breaks funny put back in 
                    # continue
                if is_product:
                    products.append(frag)

            # get all overlapping chained fragments
            educts = get_chained_frags(educts)
            products = get_chained_frags(products)

            # filter out stoichiometric factors that were used for label recreation
            educts = delete_stoichiometric_factors(educts)
            products = delete_stoichiometric_factors(products)

            self.logger.info(f"in here {educts = }, {products = }, {arrow = }")


            rct = CDReaction(educts=educts, arrow_type=arrow.type, products=products, arrow_id=arrow.id_)
            reactions.append(rct)


        # Find overlapping arrows heads and combine educts
        self.assign_stoichiometric_factors()
        
        all_arrow_combinations = itertools.combinations(self.arrow_list, 2)
        reactions_ = combine_arrows(all_arrow_combinations, reactions)

        all_line_arrow_combinations = itertools.product(self.arrow_list, self.line_list)
        self.reactions = combine_lines_and_arrows(all_line_arrow_combinations, reactions_)

        self.logger.debug(f"extracted reactions:{self.reactions}\n")

        # hard coded advanced drawing options
        if self.draw:
            self.draw_everything(draw_educt=True, draw_product=True, draw_head=False, draw_tail=False, draw_mid=False, draw_frag=True, draw_debug=False)

        return self.reactions


if __name__ == "__main__":
    path = r"D:\python_code\hein_modules\okin\src\okin\cd_reader\examples\test.cdxml"
    me = CDParser(file_path=path, draw=True)
    my_rcts = me.find_reactions()

    for rct in my_rcts:
        print(rct)

