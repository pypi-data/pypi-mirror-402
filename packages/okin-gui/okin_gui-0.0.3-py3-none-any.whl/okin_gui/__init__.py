# # okin_gui packages
from okin_gui.gui_files.window_data import DataTab
from okin_gui.gui_files.window_calibration import ConversionTab
from okin_gui.gui_files.window_kinetic import KineticTab
from okin_gui.gui_files.window_math import MathTab
from okin_gui.gui_files.window_modeling import ModelingTab
from okin_gui.gui_files.window_sim import SimulationTab_

from okin.base.chem_logger import chem_logger


# external
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedLayout, QWidget
from PySide6.QtGui import QAction

# c:\users\finn\heinlab\hein_modules\okin_gui\src\okin_gui\copasi\copasi_env\python.exe


class OkinGUI(QMainWindow):
    def __init__(self, app):
        self.app = app
        super().__init__()
        self.setWindowTitle("Main Window")

        self.toolbar = self.addToolBar("Selection")
        self.stacked_layout = QStackedLayout()
        central_widget = QWidget()
        central_widget.setMinimumSize(400, 600)
        
        central_widget.setLayout(self.stacked_layout)
        self.setCentralWidget(central_widget)

        self.create_actions()
        self.setup_tabs()
        self.setup_connections()
        self.show_math_layout()


    def create_actions(self):
        self.actions = {
            "Data": self.show_data_layout,
            "MB Solver": self.show_solver_layout,
            "Kinetics": self.show_kinetic_layout,
            "K-Optimizer": self.show_kopt_layout,
            "Simulation": self.show_sim_layout,
            "Math": self.show_math_layout
        }

    def setup_tabs(self):
        self.tabs = [
            DataTab(),
            ConversionTab(),
            KineticTab(),
            ModelingTab(),
            SimulationTab_(),
            MathTab()
        ]
        for tab in self.tabs:
            self.stacked_layout.addWidget(tab.setup_ui())

    def setup_connections(self):
        for action_text, action_method in self.actions.items():
            action = QAction(action_text, self)
            action.triggered.connect(action_method)
            self.toolbar.addAction(action)

    def show_data_layout(self):
        self.setWindowTitle("Data")
        self.stacked_layout.setCurrentIndex(0)

    def show_solver_layout(self):
        self.setWindowTitle("MB Solver")
        self.stacked_layout.setCurrentIndex(1)

    def show_kinetic_layout(self):
        self.setWindowTitle("Kinetics")
        self.stacked_layout.setCurrentIndex(2)

    def show_kopt_layout(self):
        self.setWindowTitle("K-Optimizer")
        self.stacked_layout.setCurrentIndex(3)

    def show_sim_layout(self):
        self.setWindowTitle("Simulation")
        self.stacked_layout.setCurrentIndex(4)

    def show_math_layout(self):
        self.setWindowTitle("Math")
        self.stacked_layout.setCurrentIndex(5)

    def quit_app(self):
        self.app.quit()
 
    def save_current_layout(self):
        print("I should save here but i dont")
        pass

    def load_current_layout(self):
        print("I should load here but i dont")



# this should go into the main.py
app = QApplication(sys.argv)
window = OkinGUI(app)
window.resize(1000, 850)
window.show()
sys.exit(app.exec())