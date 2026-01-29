import numpy as np

class CDFragment():
    def __init__(self, what_am_i):
        self.what_am_i = what_am_i
    
    def __repr__(self):
        return self.label

    def get_attribute(self, xml_obj, attribute):
        if attribute not in xml_obj.attrib:
            raise Exception(f"XML Object {xml_obj} has no attribute {attribute}.")
        return xml_obj.attrib[attribute]

    def get_coordinates(self, xml_obj, attribute):
        if attribute not in xml_obj.attrib:
            raise Exception(f"XML Object {xml_obj} has no attribute {attribute}.") 

        coords_string = xml_obj.attrib[attribute]
        coords = np.array([ float(num) for num in coords_string.split(" ") ])

        # it is a bb
        if len(coords) == 4:
            p1 = coords[:2]
            p2 = coords[2:]
            coords = np.array([p1, p2])
        # it is a point (head or tail)
        elif len(coords) == 3:
            coords = coords[:2]

        return np.round(coords, 2)
        
    def get_bigger_bb(self, bb, scaling_x_factor=3, scaling_y_factor=1.5):
        # define a new bounding area for one fragment in which the reaction is seen as one

        # get maximum values
        # page_bb = self.get_coordinates(self.page)
        # x_max = page_bb[1][0]
        # y_max = page_bb[1][1]

        # these are the fixed max values for a normal chemdraw page
        x_max = 540 
        y_max = 719.75

        # split into points
        p1 = bb[0]
        p2 = bb[1]
        width = p2[0]-p1[0]
        height = p2[1]-p1[1]

        
        # the bigger this number the bigger the bb
        # somewhere between 150 and 300 is the sweetspot depending on the size of the largest molecule 
        # (smaller numbers for generally small molecules)
        # variable name: ¯\_(ツ)_/¯
        arbitrary = 120

        scaling_x_factor = 0.9 + (scaling_x_factor*arbitrary / (scaling_x_factor + (width**2)))
        scaling_y_factor = 0.9 + (scaling_y_factor*arbitrary / (scaling_y_factor + (height**2)))



        # calculate new points
        new_p1 = np.array( [ p1[0]-(scaling_x_factor*width/4), p1[1]-(scaling_y_factor*height/4) ] )
        new_p2 = np.array( [p2[0]+(scaling_x_factor*width/4), p2[1]+(scaling_y_factor*height/4)] )
        
        # put everything in bounds
        for point in [new_p1, new_p2]:
            if point[0] < 0:
                point[0] = 0
            if point[0] > x_max:
                point[0] = x_max
            if point[1] < 0:
                point[1] = 0
            if point[1] > y_max:
                point[1] = y_max
        
        new_bb = np.array( [np.round(new_p1, 2), np.round(new_p2, 2) ] ) 
        return new_bb
