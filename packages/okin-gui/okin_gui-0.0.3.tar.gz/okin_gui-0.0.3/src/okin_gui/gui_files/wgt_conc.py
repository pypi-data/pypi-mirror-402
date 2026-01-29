from PySide6.QtWidgets import QMainWindow, QWidget, QScrollArea, QLabel, QLineEdit, QGridLayout,QApplication
import sys
from PySide6.QtCore import Qt

class ConcentrationWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.c_dict = {f"species {s}": {"QElem": None, "value": 0} for s in range(1, 6)}
        self.setWindowTitle("Concentration")
        self.setup_ui()
        self.update_species(species=self.c_dict.keys())

    def update_species_c_val(self,  s, text):
        self.c_dict[s]["value"] = self.c_dict[s]["QElem"].text()
        # print(f"{s = }, {self.c_dict[s]['value'] = }")
               

    def setup_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.grid_layout = QGridLayout()

        conc_wgt = QWidget()
        conc_wgt.setLayout(self.grid_layout)
        self.scroll_area.setWidget(conc_wgt)
        self.setCentralWidget(self.scroll_area)

    def update_conc(self, c_dict, overwrite=False):
        for s, c in c_dict.items():

            if s in self.c_dict.keys() and self.c_dict[s]["value"] == 0 or overwrite:
                c_val = round(c, 4)
                self.c_dict[s]["QElem"].setText(str(c_val))
                self.c_dict[s]["QElem"].setStyleSheet("background-color: rgba(100, 100, 100, 25);")




    def update_species(self, species):
        # Clear the layout before updating
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            widget.setParent(None)

        row = 0
        for s in species:
            if s not in self.c_dict.keys():
                self.c_dict[s] = {"QElem": None, "value": 0}

            c_val = self.c_dict[s]["value"]
            l_text = f"[{s}]₀ =" if not s.startswith("[") else f"{s}₀ ="
            label = QLabel(l_text)
            label.setAlignment(Qt.AlignRight)
            self.grid_layout.addWidget(label, row, 0)
            
            widget = QLineEdit(str(c_val))
            widget.setFixedWidth(60)
            widget.textChanged.connect(lambda text, key=s: self.update_species_c_val(key, text))

            self.c_dict[s]["QElem"] = widget

            self.grid_layout.addWidget(widget, row, 1)

            row += 1

        self.delete_unused_s(species=species)

    def delete_unused_s(self, species):
        # delete unused keys
        keys_to_delete = [key for key in self.c_dict if key not in species]
        for key in keys_to_delete:
            del self.c_dict[key]

    def get_c_dict(self):
        c_dict = {}
        for s, sub_dict in self.c_dict.items():
            c_dict[s] = round(float(sub_dict["value"]), 4)

        return c_dict


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConcentrationWidget()
    window.show()
    window.c_dict["species 4"]["QElem"].setText(str(5))
    window.update_species(species=["test", "finn", "species 1", "species 4"])

    sys.exit(app.exec())