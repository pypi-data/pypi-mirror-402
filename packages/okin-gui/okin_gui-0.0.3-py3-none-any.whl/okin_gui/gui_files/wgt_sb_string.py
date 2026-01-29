from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QWidget, QPushButton
from PySide6.QtCore import Signal, QEvent
from PySide6.QtGui import QFocusEvent
import sys

from okin.base.chem_logger import chem_logger
import tellurium as te

class SbStringWidget(QMainWindow):
    sb_change = Signal(str, bool)

    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setWindowTitle("Sb-String")
        self.setup_ui()
        self._set_sb_once = True
                       
    def setup_ui(self):
        sb_tab = QWidget()
        self.setCentralWidget(sb_tab)
        sb_lyt = QVBoxLayout(sb_tab)
      
        self.sb_te = QTextEdit()
        # self.sb_te.setReadOnly(False)
        self.sb_te.focusOutEvent = self.focus_out_event
        # self.sb_te.focusInEvent = self.focus_in_event

        pointless_b = QPushButton("Check Sb String")
                
        sb_lyt.addWidget(self.sb_te)
        sb_lyt.addWidget(pointless_b)
        # print("setup sb ui")

    # def focus_in_event(self, event):
    #     self.sb_te.setStyleSheet("")
    #     event.accept()  # Accept the event to ensure normal event processing

    def focus_out_event(self, event):
        print("out")
        self.sb_string = self.sb_te.toPlainText()
        self.sb_is_valid()

        if not self.is_valid and self.sb_string:
            self.sb_te.setStyleSheet("background-color: rgba(255, 0, 0, 25);")
        else:
            self.sb_te.setStyleSheet("")
            # if its valid and done editing (focus out) -> send it
            self.logger.info(f"Emit Sb String")
            self.sb_change.emit(self.get_sb_str(), self.is_valid)
        event.accept()
        
    def set_sb_string(self, sb_string):
        self.logger.info(f"Setting Sb string")
        # if self._set_sb_once:
        self.sb_te.setText(sb_string)
        #     self._set_sb_once = False

        self.focus_out_event(QFocusEvent(QEvent.FocusOut))

    def sb_is_valid(self):
        is_valid = True
        try:
            te.loada(self.sb_string)
        except:
            is_valid = False

        self.is_valid = is_valid

    def get_sb_str(self):
        if self.is_valid:
            return self.sb_string
        else:
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SbStringWidget()
    window.show()

    sys.exit(app.exec())