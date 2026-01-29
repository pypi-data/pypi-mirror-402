import sys
from okin.cd_parser.CDClasses.cd_fragment import CDFragment


class CDText(CDFragment):
    def __init__(self, xml_text):
        if isinstance(xml_text, str):
            self.label = xml_text
            return

        CDFragment.__init__(self, "text")  
        self.xml_text = xml_text
        self.id_ = super().get_attribute(self.xml_text, "id")
        original_bb = super().get_coordinates(self.xml_text, "BoundingBox")
        self.bb = super().get_bigger_bb(original_bb)
        self.label = self.get_label()
        if self.what_am_i == "stoic_f":
            # I want this to be accessible under both names
            self.factor = self.label

    def get_label(self):
        text = self.xml_text.find("s").text

        # this was in my code and has never been triggered since rework 
        # not sure if it will ever be triggered. If you manage to do so please send me your .cdx file!!
        if text == None:
            print(self.xml_text)
            print("____")
            print("Weired case happened!")
            print("Please please send your current chemdraw file to finn.bork@gmx.de I have never been able to trigger this one myself.")
            
            sys.exit()

        # differenciate between int and float for more human readable output 
        # "2 AcOH" instead of "2.0 AcOH"
        if text.isdigit():
            self.what_am_i = "stoic_f"
            text = int(text)
        elif text.replace(".","").isdigit():
            self.what_am_i = "stoic_f"
            text = float(text)
            
        return text
