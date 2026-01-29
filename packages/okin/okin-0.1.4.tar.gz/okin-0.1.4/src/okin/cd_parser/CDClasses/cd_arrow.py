from okin.cd_parser.CDClasses.cd_chem import CDFragment
import numpy as np


#! important difference when reading variable names:
# center = point between 2 points
# mid_ = area that is in the middle of something

# TODO create new Class CDLine that inherits from CDArrow. Right now both are handled here.

class CDArrow(CDFragment):
    def __init__(self, xml_arrow, xml_graphics, length_scaling_factor=1.2, height_scaling_factor=2):
        CDFragment.__init__(self, "arrow")
        self.length_scaling_factor = length_scaling_factor
        self.height_scaling_factor = height_scaling_factor

        # one arrow
        self.xml_arrow = xml_arrow
        # all graphics
        self.xml_graphics = xml_graphics

        self.id_ = self.get_attribute(self.xml_arrow, "id")
        self.type = self.get_type()

        self.head = self.get_coordinates(self.xml_arrow, "Head3D")
        self.tail = self.get_coordinates(self.xml_arrow, "Tail3D")
        if "AngularSize" in self.xml_arrow.attrib:
            angular_size = float(self.get_attribute(self.xml_arrow, "AngularSize"))
            self.head_angle = -angular_size / 2
            self.tail_angle = angular_size / 2
        else:
            self.head_angle = 0
            self.tail_angle = 0

        self.set_helper_nums()
 
        self.head_size = self.get_head_size( self.get_attribute(self.xml_arrow, "HeadSize") )
       
        # fuck everything! why do you have to call fucking .copy() on numpy arrays. FUCK! 2 stunden dafür. 
        self.head_bb, self.head_center, self.head_major, self.head_minor = self.get_end_bb(self.head.copy())
        self.tail_bb, self.tail_center, self.tail_major, self.tail_minor = self.get_end_bb(self.tail.copy(), is_tail=True)

        
        self.educt_bb, self.educt_center, self.educt_major, self.educt_minor = self.get_connection_points(self.tail_bb.copy())
        self.product_bb, self.product_center, self.product_major, self.product_minor = self.get_connection_points(self.head_bb.copy(), is_tail=True)

        
        self.mid_bb, self.mid_center, self.mid_major, self.mid_minor = self.get_mid_arrow()

    def __repr__(self):
        return self.type + "_" + str(self.id_) 

    def get_type(self):
        # get arrow type from graphic
        for graphic in self.xml_graphics:
            if "SupersededBy" in graphic.attrib:
                if graphic.attrib["SupersededBy"] == self.id_:
                    return graphic.attrib["ArrowType"]

    def get_head_size(self, head_size_str):
        head_size_dict = {"1000": [7, 6], "1500": [9, 7], "2250": [14, 10]}

        if head_size_str in head_size_dict.keys():
            head_size = np.array( head_size_dict[head_size_str] )
        else:
            head_size = np.array( [7, 9] )

        return head_size

    def set_helper_nums(self):
        self.direction = self.head-self.tail


        self.length = np.linalg.norm(self.direction) 
        # nd = normalized_direction
        self.nd = self.direction / self.length

        self.bb_length = self.length * self.length_scaling_factor
        
        # empirical default height of an arrow = 5
        # added scaling here cause it's a lot easier
        self.bb_height = 5.0 * self.height_scaling_factor

        # rotates 90 degree CW -> calculate points arround arrow end points
        rotational_matrix = np.array([(0, 1), (-1, 0)])
        vertical_vector = self.direction.dot(rotational_matrix)
        # nvv = normalized_vertical_vector
        self.nvv = vertical_vector / np.linalg.norm(vertical_vector)

        self.set_angle_to_x_axis()

    def set_angle_to_x_axis(self):
        x_axis = np.array([1,0])
        # returns angle between 2 vectors
        # maximum value is 180
        inner = self.direction.dot(x_axis)
        norms = np.linalg.norm(self.direction) * np.linalg.norm(x_axis)
        cos = inner / norms
        rad = np.arccos(np.clip(cos, -1.0, 1.0))
        deg = np.rad2deg(rad)
        
        # compensate for the fact that max value is 180
        if self.direction[1] < 0:
            deg = 360 - deg
        self.angle_to_x = deg
   
    def get_rotated_vector(self, v, angle):
        angle = np.deg2rad(angle)
        rotation_matrix = np.array( [[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]] )
        rotated_v = v.dot(rotation_matrix)
        return rotated_v

    def get_end_bb(self, end, is_tail=False):
        #! returns bb for one end of an arrow (either tail or head)

        # just didn't want to not type so much
        x, y = self.head_size

        rotational_matrix = np.array([(0, 1), (-1, 0)])
        

        if is_tail:
            f = 0.5*x
            direction = self.get_rotated_vector(self.nd, self.tail_angle)
        else:
            f = 0
            direction = self.get_rotated_vector(self.nd, self.head_angle)

        v_direction = direction.dot(rotational_matrix)

      
        p1 = end - direction*x - 0.5*v_direction*y + f * direction
        p2 = p1 + direction*x

         
        p4 = end - direction*x + 0.5*v_direction*y + f * direction
        p3 = p4 + direction*x

        end_bb = np.round([p1, p2, p3, p4], 2)

        end_center = end - (direction*x*0.5) + f * direction
        end_major = end - (direction*x) + f * direction  
        end_minor = end + (direction*-0.5*x) + (v_direction*0.5*y) + f * direction

        return end_bb, end_center, end_major, end_minor

    def get_center_point(self, points):
        # returns mid_ point between 2 points
        x_mid_point = (points[0][0] + points[1][0]) / 2
        y_mid_point = (points[0][1] + points[1][1]) / 2
        mid_point = np.array([x_mid_point, y_mid_point])
        return mid_point

    def get_connection_points(self, end_bb, is_tail=False, scaling_factor=0.19):
        #! connection points = bb at the end and beginning of an arrow. If these collide with a fragment
        #! the fragment gets added to educts/products depending on end.

        rotational_matrix = np.array([(0, 1), (-1, 0)])

        # I lost control long time ago. Just accept these - signs here. 
        if is_tail:
            direction = self.get_rotated_vector(self.nd, -self.tail_angle)
        else:
            direction = self.get_rotated_vector(self.nd, -self.head_angle)

        v_direction = direction.dot(rotational_matrix)

        # set bounding box to a variable length
        # f = direction * scaling_factor * self.length

        # set bounding box to a general length, // 100 = magic number that results in a good length
        f = direction * scaling_factor * 100

        if is_tail:
            end_bb[1] += f
            end_bb[2] += f
            
        else:
            end_bb[0] -= f
            end_bb[3] -= f

 
        end_center = self.get_center_point([end_bb[0], end_bb[2]])

        length = np.linalg.norm(end_bb[0] - end_bb[1])
        width = np.linalg.norm(end_bb[0] - end_bb[3])

        # I think somewhere something got inverted. These signs should be swapped in my opinion that is factually proven wrong.
        end_major = end_center - 0.5*direction*length
        end_minor = end_center + 0.5*v_direction*width

        return end_bb, end_center, end_major, end_minor

    def get_mid_arrow(self, x_scaling_factor=0.2, y_scaling_factor=0.4):
        #! get the mid_ area of the drawn arrow

        # Arrows when extended enough form a circle
        circle_center = self.get_coordinates(self.xml_arrow, "Center3D")
        radius = np.linalg.norm(self.head-circle_center)

        # match both angles 90 = -90 only in different direction
        if self.tail_angle > 0:
            radius *= -1

        if self.tail_angle == 0:
            mid_center = self.get_center_point([self.head, self.tail])
            # ppl are more likely to add sth on top of arrow if it is straight so make box larger
            # also it cannot ruin a circle if it is straight
            y_scaling_factor *= 1.9
            x_scaling_factor *= 1.45
        else:
            mid_center = circle_center - self.nvv * radius


        # define size of mid_bb
        x_offset = self.length * x_scaling_factor
        y_offset = self.bb_height * y_scaling_factor

        p1 = mid_center - self.nd * x_offset - self.nvv * y_offset
        p2 = mid_center + self.nd * x_offset - self.nvv * y_offset
        p3 = mid_center + self.nd * x_offset + self.nvv * y_offset
        p4 = mid_center - self.nd * x_offset + self.nvv * y_offset
     
        mid_bb = np.round( np.array( [p1, p2, p3, p4] ), 2)

        mid_major = mid_center - self.nd * x_offset
        mid_minor = mid_center - self.nvv * y_offset

        return mid_bb, mid_center, mid_major, mid_minor

