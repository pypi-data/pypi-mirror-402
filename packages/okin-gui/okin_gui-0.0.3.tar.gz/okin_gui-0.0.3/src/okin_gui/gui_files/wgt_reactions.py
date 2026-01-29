from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QSizePolicy, QScrollArea, QApplication, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent

from okin.base.reaction import TEReaction
from okin.cd_parser.cd_parser import CDParser
import os
from okin.base.chem_logger import chem_logger

class RctLineEdit(QLineEdit):
    """
    Class needed to emit signals on the focus_in and focus_out event
    """
    is_valid = Signal(list)
    is_focus = Signal(int, str)

    def __init__(self, index, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.key = key

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.is_focus.emit(self.index, self.key)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Call the rct_check function with the desired arguments
        self.rct_check(self.index, self.key, self.text())

    def rct_check(self, index, key, value):
        is_valid = True
        
        # is rct valid
        if key == "rct":
            value = value.replace("--", "-").replace("<->", "<=>")
            te_rct = value
            try:
                te_rct = TEReaction(reaction_string=value, id_=index)
                
            except Exception as e:
                is_valid = False

            self.is_valid.emit([index, key, te_rct, is_valid])
            
        # is k valid
        elif key == "k" or key == "kN":
            
            k_val = value
            constant = "$" in k_val
            try:
                k_val = value.replace("-", "").replace("$", "").strip()
                k_val = float(k_val)
                
            except Exception as e:
                is_valid = False
            
            if constant:
                k_val = f"${k_val}"
            self.is_valid.emit([index, key, k_val, is_valid])


class ReactionWidget(QWidget):
    used_chem_change = Signal(list)
    resized = Signal()
    QLINE_HEIGHT = 25
    VERTICAL_SPACING = 20
    
    # Both are % but in different. dont ask why. it is what is it.
    RCT_LINE_WIDTH = 7
    K_LINE_WIDTH = 1.3
    GAP_WIDTH = 0.02

    WHITE = "rgba(255, 255, 255, 128)"
    GREEN = "rgba(0, 255, 0, 25)"
    RED = "rgba(255, 0, 0, 25)"

    VALID_FILE_EXTENSIONS = [".cdxml", ".cdx"]

    def __init__(self, fixed_height=215, num_rct=5):
        self.parent=None
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__() # there was super().__init__(parent) and parent=None in __init__(self, …)

        # self.setStyleSheet("ReactionWidget { background-color: black; }")  # Set border style
        self.fixed_height = fixed_height # width is set my strech factor in parent
        self.num_rct = num_rct
        self.key_index_dict = {"rct": 0, "k": 1, "kN": 2}
        self.rcts_dict = {} # {1: {"rct": "A+ B -> C", k:0.6, kN:0.8, valid_rct: True, "QLineEdits": [qle_rct, qle_k, qle_kN]}}
        self.setup_ui()
        
    def setup_ui(self):
        # Create a widget to hold the layout
        self.content_widget = QWidget()
        self.rct_lay = QVBoxLayout()
        self.content_widget.setLayout(self.rct_lay)

        self.populate_layout()
        

        # Set the content widget of the scroll area
        scroll_area = QScrollArea()
        scroll_area.setAcceptDrops(True)
        # self.table.setDragDropMode(QAbstractItemView.DragDrop)
        scroll_area.dragEnterEvent = self.dragEnterEvent
        scroll_area.dragMoveEvent = self.dragMoveEvent
        scroll_area.dropEvent = self.dropEvent

        scroll_area.setWidgetResizable(True)  # Allow the widget inside the scroll area to resize
        scroll_area.setWidget(self.content_widget)
        scroll_area.setFixedHeight(self.fixed_height)

        # Set the layout of the ReactionWidget to a QVBoxLayout
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        
        self.logger.debug("setup done")

    def get_rct_line(self, index, rct_string=None):
        """
        Creates a QHBoxLayout with: {reaction, k, kN} QLineEdit
        Tracks changes
        Validates the input
        """
        self.rcts_dict[index] = {"rct": "", "k": 0, "kN": 0, "valid_rct": False, "QLEs": []} # set default values
        reaction_line_hlay = QHBoxLayout() 
        
        for prop, width, alignment in zip(["rct", "k", "kN"], [self.RCT_LINE_WIDTH, self.K_LINE_WIDTH, self.K_LINE_WIDTH], [Qt.AlignLeft, Qt.AlignCenter, Qt.AlignCenter]):
            # Create and add line edits to the QHBoxLayout
            qle = RctLineEdit(index=index, key=prop)
            self.rcts_dict[index]["QLEs"].append(qle)
            if rct_string:
                self.logger.debug(f"received input reaction string: {rct_string}")
                self.rcts_dict[index]["rct"] = rct_string
                self.rcts_dict[index]["QLEs"][0].setText(rct_string)

            # if index == 1:
            #     rct_string = "A + cat -> P + cat"
            #     self.rcts_dict[index]["rct"] = rct_string
            #     self.rcts_dict[index]["QLEs"][0].setText(rct_string)
            
            qle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            qle.setFixedHeight(self.QLINE_HEIGHT)
            qle.setAlignment(alignment)
            qle.textChanged.connect(lambda text, index=index, key=prop: self.update_rct_dict(index, key, text))
            qle.is_valid.connect(self.on_focus_out) # determine if the reaction is valid on focus out event
            qle.is_focus.connect(self.on_focus_in)
            reaction_line_hlay.addWidget(qle, width)
        
        # self.logger.debug(f"created reaction line {index}")
        
        return reaction_line_hlay

    def update_rct_dict(self, index, key, text):
        self.rcts_dict[index][key] = text
        self.new_line_check()

    def update_layout(self):
        parent_size = self.parentWidget().size()
        new_width = parent_size.width() * 0.5  # 50% of parent's width
        new_height = parent_size.height() * 0.5  # 50% of parent's height
        self.setFixedSize(new_width, new_height)

    def new_line_check(self):
        # Check if the last line in self.rcts_dict has text in the "rct" line edit
        last_index = max(self.rcts_dict.keys())

        if self.rcts_dict[last_index]["rct"]:
            # Generate a new reaction line underneath the old ones
            new_index = last_index + 1
            new_rct_line = self.get_rct_line(index=new_index)
            self.rct_lay.addLayout(new_rct_line)
            # self.logger.debug(f"Added a new line under line {last_index}")

    def on_focus_in(self, index, key):
        qle = self.rcts_dict[index]["QLEs"][self.key_index_dict[key]]
        background_color = "rgba(255, 255, 255, 128)"
        qle.setStyleSheet(f"background-color: {background_color};")

    def on_focus_out(self, ans):
        index, key, value, valid = ans

        # Define the valid_value based on the key
        if key == "rct":
            self.rcts_dict[index]["valid_rct"] = valid
            valid_value = bool(value)
            if valid:
                self.rcts_dict[index]["rct"] = value
                used_chem = self.get_used_chems()
                self.used_chem_change.emit(used_chem)

        elif key in ["k", "kN"]:
            valid_value = valid

        # Get the corresponding QLineEdit index using the key_index_dict
        qle_index = self.key_index_dict.get(key, None)
        if qle_index is None:
            return  # If the key is not found, exit the function

        # Get the specific QLineEdit
        qle = self.rcts_dict[index]["QLEs"][qle_index]

        # Set default background color
        background_color = self.WHITE  # White with high opacity

        # Set background color based on validity and value
        if valid and valid_value:
            background_color = self.GREEN  # Green with high opacity
        elif value:
            background_color = self.RED  # Red with high opacity

        # Update the QLineEdit's stylesheet
        qle.setStyleSheet(f"background-color: {background_color};")

        # Set text for 'k' and 'kN' keys if they have a value
        if key in ["k", "kN"]: 
            qle.setText(str(value))


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()

    def clear_layout(self):
        for i in reversed(range(self.rct_lay.count())):
            try:
                for j in reversed(range(self.rct_lay.itemAt(i).count())):
                    self.rct_lay.itemAt(i).itemAt(j).widget().setParent(None)
            except:
                self.rct_lay.itemAt(i).widget().setParent(None)

        # self.logger.debug(f"layout cleared")

    def populate_layout(self):
        label_wgt = QWidget()
        label_lyt = QHBoxLayout(label_wgt)

        rct_l = QLabel("Reaction")
        k_l = QLabel("k")
        kN_l = QLabel("kN")

        rct_l.setAlignment(Qt.AlignCenter)
        k_l.setAlignment(Qt.AlignCenter)
        kN_l.setAlignment(Qt.AlignCenter)

        label_lyt.addWidget(rct_l, self.RCT_LINE_WIDTH)
        label_lyt.addWidget(k_l, self.K_LINE_WIDTH)
        label_lyt.addWidget(kN_l, self.K_LINE_WIDTH)

        self.rct_lay.addWidget(label_wgt)
        for i in range(1, self.num_rct+1): # reaction indices start at 1 for chemist reasons
            # rct_line = self.get_rct_line(index=i, rct_string="A + B -> B")
            rct_line = self.get_rct_line(index=i)
            self.rct_lay.addLayout(rct_line) 
        # self.logger.debug(f"layout populated with {self.num_rct+1} lines")

    def set_reactions(self, rct_list):
        self.clear_layout()
        self.rcts_dict = {}
        self.logger.debug(f"setting from list: {rct_list}")
        for i, rct_string in enumerate(rct_list): # reaction indices start at 1 for chemist reasons
            # rct_line = self.get_rct_line(index=i, rct_string="A + B -> B")
            rct_line = self.get_rct_line(index=i+1, rct_string=str(rct_string))
            self.rct_lay.addLayout(rct_line)

            rct_edit = rct_line.itemAt(0).widget()
            rct_edit.rct_check(i+1, 'rct', rct_edit.text())

        self.new_line_check()

    def reset(self):
        # self.logger.debug(f"reset")
        self.clear_layout()
        self.rcts_dict = {}
        self.populate_layout()

    def extract_rcts(self, cd_file_path):
        cd_parser = CDParser(file_path=cd_file_path, draw=True)
        rcts = cd_parser.find_reactions()
        self.logger.info(f"chemdraw parser reactions: {rcts}")
        print(f"{rcts = }")
        return rcts

    def dragMoveEvent(self, event: QDragMoveEvent):
        return

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            file_extension = os.path.splitext(file_path)[1]
            if file_extension not in self.VALID_FILE_EXTENSIONS:
                continue

            rcts = self.extract_rcts(cd_file_path=file_path)
            self.set_reactions(rct_list=rcts)

    def set_k_dict(self, k_dict):
        # {1: {"rct": "A+ B -> C", k:0.6, kN:0.8, valid_rct: True, "QLEs": [qle_rct, qle_k, qle_kN]}}
        self.logger.info(f"updating k_dict with {k_dict}")

        for k_name, new_k_val in k_dict.items():
            
            if k_name.startswith("kN"):
                k_nr = int(k_name[2:])-1 # self.rct_dict starts at 1. 
                rct_dict = list(self.rcts_dict.values())[k_nr]
                rct_dict["kN"] = new_k_val
                rct_dict["QLEs"][2].setText(str(new_k_val))

            elif k_name.startswith("k"):
                
                k_nr = int(k_name[1:])-1 # self.rct_dict starts at 1. 
                rct_dict = list(self.rcts_dict.values())[k_nr]
                # self.logger.info(f"\n{k_nr = }\n{rct_dict = }\n{k_name = }\n{new_k_val = }")
                rct_dict["k"] = float(new_k_val)

                # self.logger.info(f"{rct_dict['QLEs'][1].text() = }")
                rct_dict["QLEs"][1].setText(str(new_k_val))
                # self.logger.info(f"{rct_dict['QLEs'][1].text() = }")

    def get_reaction_list(self):
        #  -> list[str] 
        """
        Used to access reactions in the widget. 
        """
        reactions = []
        for rct_dict in self.rcts_dict.values():
            if rct_dict["valid_rct"]:
                reactions.append(rct_dict["rct"])
                print(f"{type(rct_dict['rct']) = }")
        self.logger.info(f"Returning {reactions = }")
        return reactions
        
    def get_k_dict(self, as_float=True) -> dict:
        k_dict = {}
        for index, rct_dict in self.rcts_dict.items():
            if rct_dict["valid_rct"]:
                if as_float:
                    k_dict[f"k{index}"] = float(rct_dict["k"]) if rct_dict["k"] else 0
                    k_dict[f"kN{index}"] = float(rct_dict["kN"]) if rct_dict["kN"] else 0
                else:
                    k_dict[f"k{index}"] = rct_dict["k"] if rct_dict["k"] else "0"
                    k_dict[f"kN{index}"] = rct_dict["kN"] if rct_dict["kN"] else "0"

        self.logger.debug(f"send k values: {k_dict}")
        return k_dict

    def get_used_chems(self):
        #  -> list[str]
        total_chems = []
        rcts = self.get_reaction_list()
        for rct in rcts:
            for chem in (rct.educts + rct.products):
                total_chems.append(str(chem))
        used_chems = sorted(list(set(total_chems)))
        return used_chems

if __name__ == "__main__":

    # def test():



    import sys
    app = QApplication(sys.argv)
    widget = ReactionWidget(fixed_height=300)
    widget.show()

    b = QPushButton("update k")
    b.clicked.connect(widget.set_k_dict)
    widget.rct_lay.addWidget(b)


    sys.exit(app.exec())