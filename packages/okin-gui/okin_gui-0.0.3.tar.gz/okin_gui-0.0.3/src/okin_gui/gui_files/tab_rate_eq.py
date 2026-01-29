import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel,QPushButton, QTextEdit, QHBoxLayout,QVBoxLayout
from PySide6.QtGui import QPixmap

from okin_gui.gui_files.wgt_reactions import ReactionWidget

from okin.simulation.rate_equation import RateEquation
from okin.base.chem_logger import chem_logger

class RateEquationTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.img_path = r"./rate_equation.png"
        self.rate_eq_outputs = {"debug_string": {"QElem": "", "value": ""}, "latex_img": {"QElem": "", "value": ""}}
        self.setup_ui()
        
    def setup_ui(self):
        rate_eq_tab = QWidget()
        self.setCentralWidget(rate_eq_tab)
        rate_eq_lyt = QVBoxLayout(rate_eq_tab)

        input_lyt = QHBoxLayout()

        self.rct_wgt = ReactionWidget()
        input_lyt.addWidget(self.rct_wgt, 7)
        empty_l = QLabel("")
        input_lyt.addWidget(empty_l, 3)

        run_rate_eq_b = QPushButton("Do Rate")
        run_rate_eq_b.clicked.connect(self.run_rate_eq_solver)

        rate_eq_img_wgt = QLabel()
        rate_eq_img_wgt.setGeometry(100, 100, 200, 150)  # Set the position and size of the QLabel
        rate_eq_img_wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rate_eq_outputs["latex_img"]["QElem"] = rate_eq_img_wgt

        req_log_te = QTextEdit()
        req_log_te.setReadOnly(True)
        self.rate_eq_outputs["debug_string"]["QElem"] = req_log_te

        rate_eq_lyt.addLayout(input_lyt)
        rate_eq_lyt.addWidget(run_rate_eq_b)
        rate_eq_lyt.addWidget(rate_eq_img_wgt)
        rate_eq_lyt.addWidget(req_log_te)

        return rate_eq_tab


    def run_rate_eq_solver(self):
        # get reactions
        import copy
        # rate_eq_rcts = self.rct_wgt.get_reaction_list().copy()
        rate_eq_rcts = copy.deepcopy(self.rct_wgt.get_reaction_list())
        self.logger.debug(f"{rate_eq_rcts[0] = }")
        # create RateEquation
        rate_eq = RateEquation(reactions=rate_eq_rcts, show_steady_states=True, show_used_reactions=True)

        self.rate_eq_outputs["debug_string"]["QElem"].setText(rate_eq.log_string + rate_eq.debug_string)
        rate_eq.show_latex_rate_law(self.img_path)
        curr_req = QPixmap(self.img_path)
        self.rate_eq_outputs["latex_img"]["QElem"].setPixmap(curr_req)

        # del rate_eq

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RateEquationTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())