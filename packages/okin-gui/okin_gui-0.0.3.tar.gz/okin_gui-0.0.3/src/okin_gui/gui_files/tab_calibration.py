import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton

from okin.base.chem_logger import chem_logger
class CalibrationTab(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.setup_ui()
       

    def setup_ui(self):
        mb_tab = QWidget()
        self.setCentralWidget(mb_tab)
        mb_lyt = QVBoxLayout(mb_tab)
        self.resize(800, 600)
         
        placeholder_b = QPushButton("Pointless Button")
        placeholder_b.setFixedHeight(120)
        mb_lyt.addWidget(placeholder_b)
        return mb_tab


if __name__ == "__main__":

    
    app = QApplication(sys.argv)
    window = CalibrationTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())