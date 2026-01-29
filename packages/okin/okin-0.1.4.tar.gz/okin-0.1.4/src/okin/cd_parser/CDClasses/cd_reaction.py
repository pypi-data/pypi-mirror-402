from okin.base.reaction import Reaction
from okin.base.chem_logger import chem_logger

class CDReaction(Reaction):
    def __init__(self, educts, arrow_type, products, arrow_id):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.logger.info(f"In CDReaction {educts = }, {arrow_type}, {products = }, {arrow_id =}")
        super().__init__(educts=educts, arrow_type=arrow_type, products=products)
        self.id_ = arrow_id