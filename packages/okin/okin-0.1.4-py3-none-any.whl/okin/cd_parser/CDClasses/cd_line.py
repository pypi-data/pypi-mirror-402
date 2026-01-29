from okin.cd_parser.CDClasses.cd_arrow import CDArrow
from okin.cd_parser.CDClasses.cd_fragment import CDFragment
import numpy as np

class CDLine(CDArrow):
    def __init__(self, xml_line, xml_graphics, length_scaling_factor=1.2, height_scaling_factor=2):
        
        CDFragment.__init__(self, "line")
        self.length_scaling_factor = length_scaling_factor
        self.height_scaling_factor = height_scaling_factor

        # one line
        self.xml_line = xml_line
        # all graphics
        self.xml_graphics = xml_graphics

        self.id_ = self.get_attribute(self.xml_line, "id")
        self.type = "line"

        self.head = self.get_coordinates(self.xml_line, "Head3D")
        self.tail = self.get_coordinates(self.xml_line, "Tail3D")
        if "AngularSize" in self.xml_line.attrib:
            angular_size = float(self.get_attribute(self.xml_line, "AngularSize"))
            self.head_angle = -angular_size / 2
            self.tail_angle = angular_size / 2
        else:
            self.head_angle = 0
            self.tail_angle = 0

        self.set_helper_nums()
        
        # just set to default height of small arrow
        self.head_size = np.array( [7, 9] )
       
        # fuck everything! why do you have to call fucking .copy() on numpy arrays. FUCK! 2 stunden dafür. 
        self.head_bb, self.head_center, self.head_major, self.head_minor = self.get_end_bb(self.head.copy())
        self.tail_bb, self.tail_center, self.tail_major, self.tail_minor = self.get_end_bb(self.tail.copy(), is_tail=True)
        
        self.educt_bb, self.educt_center, self.educt_major, self.educt_minor = self.get_connection_points(self.tail_bb.copy(), scaling_factor=0.1)
        self.product_bb, self.product_center, self.product_major, self.product_minor = self.get_connection_points(self.head_bb.copy(), is_tail=True, scaling_factor=0.1)
        

    def __repr__(self):
        return "line_" + str(self.id_)