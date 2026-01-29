import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel,QPushButton, QTextEdit, QHBoxLayout,QVBoxLayout, QLineEdit, QSpinBox, QCheckBox, QFrame, QScrollArea
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton

from okin_gui.gui_files.wgt_reactions import ReactionWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.gui_files.wgt_save import SavingWidget
from okin.simulation.simulator import Simulator
from okin_gui.gui_files.wgt_conc import ConcentrationWidget
from okin.base.chem_logger import chem_logger
from okin.base.chem_plot_utils import apply_acs_layout
import numpy as np
import matplotlib.pyplot as plt

from okin_gui.utils.storage_paths import temp_file_path
from okin.simulation.tc_engine import InteractiveTimeCourse

class SimulationTab(QMainWindow):
    get_sb = Signal(str)
    def __init__(self):
        super().__init__()
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.img_path = f"{temp_file_path}\\sim.png"
        self.settings = {"to_plot": {"QElem": "", "value": ""}, "nr_samples": {"QElem": "", "value": 20}, "pct_noise": {"QElem": "", "value": 0}, "true_cat": {"QElem": "", "value": False}, "stop": {"QElem": "", "value": 10}}
        self.conc_wgt = None
        self.sim = Simulator()
        self.sb_is_valid = False
        self.setup_ui()
        
        
    def setup_ui(self):
        sim_tab = QWidget()
        # sim_tab.setStyleSheet("border: 1px solid black;")
        self.setCentralWidget(sim_tab)
        sim_lyt = QVBoxLayout(sim_tab)

        input_lyt = QHBoxLayout()

        self.rct_wgt = ReactionWidget()
        

        input_lyt.addWidget(self.rct_wgt, 8)

        self.conc_wgt = ConcentrationWidget()
        self.conc_wgt.setFixedHeight(215)
        self.rct_wgt.used_chem_change.connect(self.conc_wgt.update_species)
        input_lyt.addWidget(self.conc_wgt, 2)


        sb_b = QPushButton("Generate Sb String")
        sb_b.clicked.connect(self.generate_sb_string)

        opt_wgt = self.get_opt_wgt()

        run_b_lyt = QHBoxLayout()

        run_sim_b = QPushButton("Simulate")
        run_sim_b.clicked.connect(self.run_sim)

        run_interactive_tc_b = QPushButton("Interactive Time Course")
        run_interactive_tc_b.clicked.connect(self.run_interactive)
        run_interactive_tc_b.setObjectName("tc")

        run_interactive_vtna_b = QPushButton("Interactive VTNA")
        run_interactive_vtna_b.clicked.connect(self.run_interactive)
        run_interactive_vtna_b.setObjectName("vtna")

        run_interactive_phase_b = QPushButton("Interactive Phase")
        run_interactive_phase_b.clicked.connect(self.run_interactive)    
        run_interactive_phase_b.setObjectName("phase")

        
        run_b_lyt.addWidget(run_interactive_phase_b)
        run_b_lyt.addWidget(run_interactive_tc_b)
        run_b_lyt.addWidget(run_interactive_vtna_b)
        run_b_lyt.addWidget(run_sim_b)

        self.img_wgt = ImageWidget(initial_width=1200)
        self.save_wgt = SavingWidget(parent=self, button_names=["Save CSV", "Save Image"])
       

        sim_lyt.addLayout(input_lyt)
        sim_lyt.addWidget(sb_b)
        sim_lyt.addWidget(opt_wgt)
        sim_lyt.addLayout(run_b_lyt)
        sim_lyt.addWidget(self.img_wgt)
        sim_lyt.addWidget(self.save_wgt)

        return sim_tab

    def get_opt_wgt(self):
        wgt = QWidget()
        lyt = QHBoxLayout(wgt)

        opt_wgt = QWidget()
        opt_lyt = QHBoxLayout(opt_wgt)
        opt_lyt.setAlignment(Qt.AlignCenter)
        # lyt.setAlignment(Qt.)

        pairs = [
            (QLabel("To Plot"), QLineEdit("A, P"), 40, 130, self.settings["to_plot"]),
            (QLabel("# Samples"), QSpinBox(), 50, 80, self.settings["nr_samples"]),
            (QLabel("% Noise"), QSpinBox(), 45, 80, self.settings["pct_noise"]),
            (QLabel("True Cat"), QCheckBox(), 45, 20, self.settings["true_cat"]),
            (QLabel("Stop Time"), QLineEdit("10"), 60, 60, self.settings["stop"]),
            
        ]

        pairs[1][1].setValue(20) # set value for nr_samples
        pairs[1][1].setMaximum(999) # set value for nr_samples
        pairs[1][1].setMinimum(1) # set value for nr_samples
        pairs[2][1].setMaximum(100)  # Set maximum for noise_sb
        pairs[2][1].setValue(0)

        # Iterate over pairs and pack matching pairs into QHBoxLayouts
        for label, widget, lwidth, qwidth, qdict in pairs:
            pair_lyt = QHBoxLayout()
            if label:
                pair_lyt.addWidget(label)
                label.setFixedWidth(lwidth)
            
            pair_lyt.addWidget(widget)
            widget.setFixedWidth(qwidth)
            qdict["QElem"] = widget
            opt_lyt.addLayout(pair_lyt)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        calc_end_b = QPushButton("Determine end")

        lyt.addWidget(opt_wgt)
        lyt.addWidget(separator)
        lyt.addWidget(calc_end_b)

        return wgt
    
    def update_sb_string(self, sb_string, sb_is_valid):
        self.logger.info(f"Updated Sb String: \n{sb_string}")
        self.sb_string = sb_string
        self.sb_is_valid = sb_is_valid            

    def generate_sb_string(self):
        """
        - this function generates the Sb string from initial data.
        - the sb string is send to the Sb wgt where it is checkd for validity
        - the Sb string gets updated in self.update_sb_string(), which is triggered by a Signal from the Sb wgt
        """
        self.logger.info(f"Now creating Sb string from reactions")
       
        rcts = self.rct_wgt.get_reaction_list()
        k_dict = self.rct_wgt.get_k_dict()
        c_dict = self.conc_wgt.get_c_dict()
        self.used_chems = self.rct_wgt.get_used_chems()
        sb_string = self.sim._get_antimony_str(reactions=rcts, c_dict=c_dict, k_dict=k_dict)

        self.get_sb.emit(sb_string)

    def set_dict_values(self, settings_dict):
        for key, wgt_dct in settings_dict.items():
            widget = wgt_dct["QElem"]

            if isinstance(widget, QLineEdit):
                val = widget.text()
            
            elif isinstance(widget, QSpinBox):
                val = widget.value()

            elif isinstance(widget, QWidget):
                checkboxes = widget.findChildren(QCheckBox)
                if checkboxes:
                    val = {k: ch.isChecked() for k, ch in zip(self.ta_species_list, checkboxes)}
                else:
                    val = widget.isChecked()
            
            print(key, val)
            settings_dict[key]["value"] = val

    def run_sim(self):
        if not self.sb_is_valid:
            self.logger.warning(f"The given Sb String is incorrect.")
            return

        self.set_dict_values(settings_dict=self.settings)

        start = 0
        stop = float(self.settings["stop"]["value"])
        nr_points = int(self.settings["nr_samples"]["value"])
        const_cat = self.settings["true_cat"]["value"]
        to_plot = ["time"] + [s.strip() for s in self.settings["to_plot"]["value"].split(",")]
        noise = int(self.settings["pct_noise"]["value"])/100
        # make Sb string, send to sb wgt, check if valid
        # self.sim.simulate(sb_string=self.sb_string, start=start, stop=stop, nr_time_points=nr_points, use_const_cat=const_cat, selections=to_plot)
        self.sim.simulate(sb_string=self.sb_string, start=start, stop=stop, nr_time_points=nr_points, selections=to_plot)
        df = self.sim.result

        for col in df.columns:
            if col != "time":
                df[col] *= (1 + np.random.uniform(-noise, noise, size=len(df)))

                plt.scatter(df["time"], df[col], label=col)
            
        plt.xlabel("time")
        plt.ylabel("concentration")
        apply_acs_layout()
        plt.legend(loc="upper right")
        plt.savefig(self.img_path)
        
        self.img_wgt.set_image_path(self.img_path)
        plt.clf()
        self.results_df = df.copy()

    def run_interactive(self):
        sender = self.sender()
        mode = sender.objectName()
        
        self.logger.info(f"Started interactive session in {mode} mode")

        rcts = [str(rct)[3:].replace("->", "=") for rct in self.rct_wgt.get_reaction_list()]
        # k_dict = self.rct_wgt.get_k_dict()
        c_dict = self.conc_wgt.get_c_dict()

        session = InteractiveTimeCourse(mechanism=rcts, initial_conditions=c_dict, conserved_species=None, k_init={}, mode=mode)
        session.run()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationTab()
    window.setup_ui()
    window.resize(1000, 850)
    window.show()

    sys.exit(app.exec())