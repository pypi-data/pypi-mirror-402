import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget,QPushButton,QHBoxLayout,QVBoxLayout, QFrame, QLineEdit, QSpacerItem, QSizePolicy, QApplication, QMainWindow, QLabel, QComboBox, QTabWidget, QCheckBox, QGridLayout, QSpinBox

from okin_gui.utils.convert_to_df import load_file_to_df
from okin_gui.gui_files.wgt_table import TableWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.gui_files.wgt_save import SavingWidget
from okin_gui.utils.storage_paths import temp_file_path

from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_logger import chem_logger
from okin.kinetics.vtna import ClassicVTNA, PointVTNA

import pandas as pd
import matplotlib.pyplot as plt

class ModernKineticsLayout(QMainWindow):
    def __init__(self):
        super().__init__()

        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.left_df = None
        self.right_df = None
        self.c_vtna = None
        self.settings = {"species": {"QElem": None, "value": ""}, "func_type": {"QElem": None, "value": ""}, "func": {"QElem": None, "value": ""}, "nth_poly": {"QElem": None, "value": ""}, "symbol_func": {"QElem": None, "value": ""}}
        # self.outputs = {"r2": {"QElem": None, "value": ""}, "fitted_func": {"QElem": None, "value": ""}}
        
        self.tc_settings = {"species": {"QElem": None, "value": []}, "+x": {"QElem": None, "value": 0}, "+y": {"QElem": None, "value": 0}, "rate": {"QElem": None, "value": False}, "both": {"QElem": None, "value": False}}
        self.cv_settings = {"species": {"QElem": None, "value": ""}, "product": {"QElem": None, "value": ""}, "order": {"QElem": None, "value": ""}, "error": {"QElem": None, "value": ""}}
        self.pv_settings = {"species": {"QElem": None, "value": ""}, "product": {"QElem": None, "value": ""}, "window": {"QElem": None, "value": ""}, "avg_order": {"QElem": None, "value": ""}, "c_vtna_order": {"QElem": None, "value": ""}}

        self.tc_img_path = f"{temp_file_path}\\tc.png"
        self.ta_img_path = f"{temp_file_path}\\ta.png"
        self.cv_img_path = f"{temp_file_path}\\cv.png"
        self.pv_img_path = f"{temp_file_path}\\pv.png"

        self.tc_results_df = pd.DataFrame()
        self.ta_results_df = pd.DataFrame()
        self.cv_results_df = pd.DataFrame()
        self.pv_results_df = pd.DataFrame()
        
        
        self.setup_ui()

    def setup_ui(self):
        #* I decided to not split this TabWidget into multiple files as they share the initial data and their setup is minimal

        mkin_tab = QWidget()
        self.setCentralWidget(mkin_tab)
        mkin_lyt = QVBoxLayout(mkin_tab)

        #! ___________________MAIN INPUT layout
        input_wgt = self.get_input_lyt()
       


        #! __________________ MAIN OUTPUT layout
        tab_widget = QTabWidget()
        # tab_widget.currentChanged.connect(lambda: print("he"))


        tc_tab = self.get_tc_tab()
        tab_widget.addTab(tc_tab, "Time Course")

        cv_tab = self.get_cv_tab()
        tab_widget.addTab(cv_tab, "Classic VTNA")

        pv_tab = self.get_pv_tab()
        tab_widget.addTab(pv_tab, "Point VTNA")

        mkin_lyt.addWidget(input_wgt, 2)
        mkin_lyt.addWidget(tab_widget, 8)

    def get_input_lyt(self):
        input_wgt = QWidget()
        input_lyt = QHBoxLayout(input_wgt)
        input_lyt.setAlignment(Qt.AlignCenter)
        table_list = [{"name": "left csv file", "width_%": 0.97, "enable_dragdrop": True}]
        self.left_csv_wgt = TableWidget(table_list=table_list, num_row=5)
        self.left_csv_wgt.MAGIC_TABLE_PADDING = 0
        self.left_csv_wgt.new_selected.connect(self.on_new_selected)
        # self.left_csv_wgt.double_click_trigger.connect(self.run_fitting)

        table_list = [{"name": "right csv file", "width_%": 0.97, "enable_dragdrop": True}]
        self.right_csv_wgt = TableWidget(table_list=table_list, num_row=5)
        self.right_csv_wgt.MAGIC_TABLE_PADDING = 0
        self.right_csv_wgt.new_selected.connect(self.on_new_selected)
        # self.left_csv_wgt.double_click_trigger.connect(self.run_fitting)

        csv_input_l = QLabel("VS")
        csv_input_l.setFixedWidth(20)

        input_lyt.addWidget(self.left_csv_wgt, 4.0)
        input_lyt.addWidget(csv_input_l, 0.5)
        input_lyt.addWidget(self.right_csv_wgt, 4.0)
        # input_lyt.addWidget(species_wgt, 1.5)
        # input_lyt.addStretch(1)
        return input_wgt

    def get_tc_tab(self):
        self.ta_species_list = [f"species {x}" for x in range(1, 7)]
        tc_wgt = QWidget()
        tc_lyt = QVBoxLayout(tc_wgt)

        tc_input_lyt = QHBoxLayout()

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)

        

        #! _______ create chs (checkboxes) for species
        

        species_wgt = QWidget()
        # species_wgt.setStyleSheet("border: 1px solid black;")
        species_lyt = QGridLayout(species_wgt)
        # species_lyt.setAlignment(Qt.AlignLeft)
    
        row = 0
        col = 0
        for string in self.ta_species_list:
            ch = QCheckBox(string)
            species_lyt.addWidget(ch, row, col)

            col += 1
            if col == 3:
                col = 0
                row += 1
                
        #! _______ create time adjust settings
        ta_wgt = QWidget()        
        ta_lyt = QHBoxLayout(ta_wgt)
        ta_lyt.setAlignment(Qt.AlignCenter)
        

        left_x_label = QLabel("+ x on left csv:")
        left_x_label.setFixedWidth(80)
        
        x_ta = QLineEdit()
        x_ta.setText("0")
        x_ta.setFixedWidth(60)

        spacer_item = QSpacerItem(50, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        left_y_label = QLabel("+ y on left csv:")
        left_y_label.setFixedWidth(80)
        
        y_ta = QLineEdit()
        y_ta.setText("0")
        y_ta.setFixedWidth(60)
        
        ta_lyt.addWidget(left_x_label)
        ta_lyt.addWidget(x_ta)
        ta_lyt.addSpacerItem(spacer_item)
        ta_lyt.addWidget(left_y_label)
        ta_lyt.addWidget(y_ta)


        #! _______ create ches for settings
        opt_wgt = QWidget()
        opt_lyt = QHBoxLayout(opt_wgt)
        opt_lyt.setAlignment(Qt.AlignCenter)

        rate_ch = QCheckBox("convert to rate")
        both_ch = QCheckBox("show both")
        rate_ch.stateChanged.connect(self.run_tc)
        both_ch.stateChanged.connect(self.run_tc)

        opt_lyt.addWidget(rate_ch)
        opt_lyt.addWidget(both_ch)


        #! _______ add to lyt
        tc_input_lyt.addWidget(species_wgt, 3)
        tc_input_lyt.addWidget(separator, 0.5)
        tc_input_lyt.addWidget(ta_wgt, 3.5)
        tc_input_lyt.addWidget(separator2, 0.5)
        tc_input_lyt.addWidget(opt_wgt, 2)


        #! _______ update settings
        self.tc_settings["species"]["QElem"] = species_wgt
        self.tc_settings["rate"]["QElem"] = rate_ch
        self.tc_settings["both"]["QElem"] = both_ch
        self.tc_settings["+x"]["QElem"] = x_ta
        self.tc_settings["+y"]["QElem"] = y_ta


        #! ______ add button, img and save wgt
        do_tc_b = QPushButton("Do Time Course")
        do_tc_b.clicked.connect(self.run_tc)

        self.tc_img_wgt = ImageWidget(initial_width=1200)
        self.tc_save_wgt = SavingWidget(parent=self, button_names=["save csv", "save image"])

        #! _____ add to lyt
        tc_lyt.addLayout(tc_input_lyt)
        # tc_lyt.addWidget(ta_wgt)
        tc_lyt.addWidget(do_tc_b)
        tc_lyt.addWidget(self.tc_img_wgt)
        tc_lyt.addWidget(self.tc_save_wgt)

        return tc_wgt

    def change_ch_names(self, wgt, new_list):
        # Find all checkboxes in the widget
        checkboxes = wgt.findChildren(QCheckBox)

        # Change the text of each checkbox to "test"
        for i, checkbox in enumerate(checkboxes):
            name = new_list[i] if (i < len(new_list)) else ""
            checkbox.setText(name)

    def set_dict_values(self, settings_dict):
        for key, wgt_dct in settings_dict.items():
            widget = wgt_dct["QElem"]

            if isinstance(widget, QComboBox):
                val = widget.currentText()

            elif isinstance(widget, QLineEdit):
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

    def run_tc(self):
        if self.left_df is None:
            self.logger.info("Missing data on left csv list")
            return
        self.set_dict_values(self.tc_settings)

        # set all variables
        df = pd.DataFrame()
        is_rate = self.tc_settings["rate"]["value"] # convert data to rate
        is_both = self.tc_settings["both"]["value"] # display data from both files
        species_dict = self.tc_settings["species"]["value"]
        plus_x = float(self.tc_settings["+x"]["value"])
        plus_y = float(self.tc_settings["+y"]["value"])

        # make df
        tc_headers = [s for s, v in species_dict.items() if v]
        left_df = self.left_df.copy()[tc_headers]

        if is_rate:
            for h in tc_headers:
                left_df[h] = left_df[h].diff().fillna(0)

        # add time col
        left_df = pd.concat([left_df, self.left_df[self.time_col]], axis=1)

        if is_both:
            right_df = self.right_df.copy()[tc_headers]

            for h in tc_headers:
                if is_rate:
                    right_df[h] = right_df[h].diff().fillna(0)

                right_df[h] += plus_y

            right_df = pd.concat([right_df, self.right_df[self.time_col]], axis=1)
            # add +x and +y
            right_df[self.time_col] += plus_x
    
        else:
            right_df = None
            
        self.create_tc_plot(left_df, tc_headers, right_df, is_both)

    def create_tc_plot(self, left_df, tc_headers, right_df=None, is_both=False):
        # create plot
        for h in tc_headers:
            if h.startswith("time"):
                continue
            plt.scatter(left_df[self.time_col], left_df[h])
            if is_both:
                plt.scatter(right_df[self.time_col], right_df[h])

        plt.xlabel("time")
        plt.ylabel("y")
        apply_acs_layout()
        plt.savefig(self.tc_img_path, dpi=400)
        self.tc_img_wgt.set_image_path(self.tc_img_path)
        plt.clf()
        # plt.show()
 
    def get_cv_tab(self):
        cv_wgt = QWidget()
        cv_lyt = QVBoxLayout(cv_wgt)
        cv_input_lyt = QHBoxLayout()
        
        # species product order error
        species_lyt = QHBoxLayout()
        species_l = QLabel("Species")
        species_l.setFixedWidth(40)
        species_cb = QComboBox()
        species_cb.setFixedWidth(120)
        species_lyt.addWidget(species_l)
        species_lyt.addWidget(species_cb)

        product_lyt = QHBoxLayout()
        product_l = QLabel("Product")
        product_l.setFixedWidth(45)
        product_cb = QComboBox()
        product_cb.setFixedWidth(120)
        product_lyt.addWidget(product_l)
        product_lyt.addWidget(product_cb)

        order_lyt = QHBoxLayout()
        order_l = QLabel("Order")
        order_l.setFixedWidth(35)
        order_ql = QLineEdit("1.00")
        order_ql.returnPressed.connect(self.show_order_cv) # for custom orders
        order_ql.setFixedWidth(50)
        order_lyt.addWidget(order_l)
        order_lyt.addWidget(order_ql)

        error_lyt = QHBoxLayout()
        error_l = QLabel("Error")
        error_l.setFixedWidth(30)
        error_ql = QLineEdit("")
        error_ql.setReadOnly(True)
        error_ql.setFixedWidth(120)
        error_lyt.addWidget(error_l)
        error_lyt.addWidget(error_ql)

        self.cv_settings["species"]["QElem"] = species_cb
        self.cv_settings["product"]["QElem"] = product_cb
        self.cv_settings["order"]["QElem"] = order_ql
        self.cv_settings["error"]["QElem"] = error_ql
        
        cv_input_lyt.addLayout(species_lyt)
        cv_input_lyt.addLayout(product_lyt)
        cv_input_lyt.addLayout(order_lyt)
        cv_input_lyt.addLayout(error_lyt)

        cv_b = QPushButton("classic VTNA")
        cv_b.clicked.connect(self.run_cv)

        self.cv_img_wgt = ImageWidget(initial_width=1000)
        self.cv_save_wgt = SavingWidget(parent=self, button_names=["Save CSV", "Save Image"])

        cv_lyt.addLayout(cv_input_lyt)
        cv_lyt.addWidget(cv_b)
        cv_lyt.addWidget(self.cv_img_wgt)
        cv_lyt.addWidget(self.cv_save_wgt)

        return cv_wgt

    def run_cv(self):
        # if not self.left_df or not self.right_df:
        #     self.logger.info("Select 2 csv files")
        #     return
        self.set_dict_values(settings_dict=self.cv_settings)

        species = self.cv_settings["species"]["value"]
        product = self.cv_settings["product"]["value"]

        self.c_vtna = ClassicVTNA(df_rct1=self.left_df, df_rct2=self.right_df, species_col_name=species, product_col_name=product, time_col_name=self.time_col)
        self.cv_settings["order"]["QElem"].setText(str(self.c_vtna.best_order))
        self.cv_settings["order"]["value"] = str(self.c_vtna.best_order)

        
        self.show_order_cv()

    def show_order_cv(self):
        if not self.c_vtna:
            self.logger.info(f"There is no VTNA yet")
            return
        
   
        order = float(self.cv_settings["order"]["QElem"].text())
        
        normalized_x_axis_1, normalized_x_axis_2, error = self.c_vtna.get_specific_order_axes(order=order, show=False)
        # error = round(self.c_vtna.get_error(x1=normalized_x_axis_1, y1=self.c_vtna.product1, x2=normalized_x_axis_2, y2=self.c_vtna.product2), 8)

        self.cv_settings["error"]["QElem"].setText(str(error))
        self.cv_settings["error"]["value"] = str(error)

        plt.xlabel(f"Σ {self.c_vtna.species_col_name}^{order}Δt")
        plt.ylabel(f"{self.c_vtna.product_col_name}")

        plt.scatter(normalized_x_axis_1, self.c_vtna.product1,
                label=f"{self.c_vtna.product_col_name} 1")
        plt.scatter(normalized_x_axis_2, self.c_vtna.product2,
                label=f"{self.c_vtna.product_col_name} 2")
        
        apply_acs_layout()
        plt.savefig(self.cv_img_path)
        self.cv_img_wgt.set_image_path(self.cv_img_path)
        plt.clf()
        
    def get_pv_tab(self):
        pv_wgt = QWidget()
        pv_lyt = QVBoxLayout(pv_wgt)
        pv_input_lyt = QHBoxLayout()
        
        # species product order error
        species_lyt = QHBoxLayout()
        species_l = QLabel("Species")
        species_l.setFixedWidth(40)
        species_cb = QComboBox()
        species_cb.setFixedWidth(120)
        species_lyt.addWidget(species_l)
        species_lyt.addWidget(species_cb)

        product_lyt = QHBoxLayout()
        product_l = QLabel("Product")
        product_l.setFixedWidth(45)
        product_cb = QComboBox()
        product_cb.setFixedWidth(120)
        product_lyt.addWidget(product_l)
        product_lyt.addWidget(product_cb)

        order_lyt = QHBoxLayout()
        order_l = QLabel("Window")
        order_l.setFixedWidth(35)
        window_sb = QSpinBox()
        window_sb.setValue(9)
        window_sb.setSingleStep(2)
        window_sb.setFixedWidth(50)
        order_lyt.addWidget(order_l)
        order_lyt.addWidget(window_sb)

        avg_order_lyt = QHBoxLayout()
        avg_order_l = QLabel("Average Order")
        avg_order_l.setFixedWidth(80)
        avg_order_ql = QLineEdit("")
        avg_order_ql.setReadOnly(True)
        avg_order_ql.setFixedWidth(80)
        avg_order_lyt.addWidget(avg_order_l)
        avg_order_lyt.addWidget(avg_order_ql)


        avg_order_lyt = QHBoxLayout()
        avg_order_l = QLabel("Average Order")
        avg_order_l.setFixedWidth(80)
        avg_order_ql = QLineEdit("")
        avg_order_ql.setReadOnly(True)
        avg_order_ql.setFixedWidth(80)
        avg_order_lyt.addWidget(avg_order_l)
        avg_order_lyt.addWidget(avg_order_ql)

        c_vtna_order_lyt = QHBoxLayout()
        c_vtna_order_l = QLabel("cVTNA Order")
        c_vtna_order_l.setFixedWidth(80)
        c_vtna_order_ql = QLineEdit("")
        c_vtna_order_ql.setReadOnly(True)
        c_vtna_order_ql.setFixedWidth(80)
        c_vtna_order_lyt.addWidget(c_vtna_order_l)
        c_vtna_order_lyt.addWidget(c_vtna_order_ql)


        self.pv_settings["species"]["QElem"] = species_cb
        self.pv_settings["product"]["QElem"] = product_cb
        self.pv_settings["window"]["QElem"] = window_sb
        self.pv_settings["avg_order"]["QElem"] = avg_order_ql
        self.pv_settings["c_vtna_order"]["QElem"] = c_vtna_order_ql
        
        pv_input_lyt.addLayout(species_lyt)
        pv_input_lyt.addLayout(product_lyt)
        pv_input_lyt.addLayout(order_lyt)
        pv_input_lyt.addLayout(avg_order_lyt)
        pv_input_lyt.addLayout(c_vtna_order_lyt)

        pv_b = QPushButton("point VTNA")
        pv_b.clicked.connect(self.run_pv)

        self.pv_img_wgt = ImageWidget(initial_width=1000)
        self.pv_save_wgt = SavingWidget(parent=self, button_names=["Save CSV", "Save Image"])

        pv_lyt.addLayout(pv_input_lyt)
        pv_lyt.addWidget(pv_b)
        pv_lyt.addWidget(self.pv_img_wgt)
        pv_lyt.addWidget(self.pv_save_wgt)

        return pv_wgt

    def run_pv(self):
        self.set_dict_values(settings_dict=self.pv_settings)

        species = self.pv_settings["species"]["value"]
        product = self.pv_settings["product"]["value"]
        window = self.pv_settings["window"]["value"]

        self.p_vtna = PointVTNA(df_rct1=self.left_df, df_rct2=self.right_df, species_col_name=species, product_col_name=product, time_col_name=self.time_col, win=window)

        avg_order = round(sum(self.p_vtna.orders)/len(self.p_vtna.orders), 2)
        self.pv_settings["avg_order"]["QElem"].setText(str(avg_order))
        self.pv_settings["c_vtna_order"]["QElem"].setText(str(self.p_vtna.best_order))

        self.show_order_pv()

    def show_order_pv(self):
        plt.clf()
        
        plt.xlabel("time")
        plt.ylabel(f"order of {self.p_vtna.species_col_name}")
        # plt.title(f"avg order: {round(sum(self.p_vtna.orders)/len(self.p_vtna.orders), 2)} c_vtna: {self.p_vtna.best_order}")
        
        plt.plot(self.p_vtna.plotting_time, self.p_vtna.orders, alpha=0.5)
        plt.scatter(self.p_vtna.plotting_time, self.p_vtna.orders, alpha=0.5)
        plt.axhline(self.p_vtna.best_order, label="classical VTNA order", color="darkgreen")

        apply_acs_layout()
        plt.savefig(self.pv_img_path)
        self.pv_img_wgt.set_image_path(self.pv_img_path)
        plt.clf()

    @Slot(list)
    def on_new_selected(self, selected_row):
        try:
            df = load_file_to_df(selected_row[0])
        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            df = pd.DataFrame()
        
        sender = self.sender()
        if sender == self.left_csv_wgt:
            self.logger.debug("Received new selection from left_csv_wgt")
            self.left_df = df
            self.ta_species_list = [c for c in df.columns if not c.startswith("time")]
            self.change_ch_names(self.tc_settings["species"]["QElem"], self.ta_species_list)

            # update headers
            
            self.headers = [c for c in df.columns if not c.startswith("time")]
            self.time_col = [c for c in df.columns if c.startswith("time")][0]

            self.update_inputs()

        elif sender == self.right_csv_wgt:
            self.logger.debug("Received new selection from right_csv_wgt")
            self.right_df = df

    def update_inputs(self):
        self.cv_settings["species"]["QElem"].addItems(self.headers)
        self.cv_settings["product"]["QElem"].addItems(self.headers)

        self.pv_settings["species"]["QElem"].addItems(self.headers)
        self.pv_settings["product"]["QElem"].addItems(self.headers)
        


        # self.logger.debug(f"Received {selected_row = }")
        

        # self.fitting_df = df
        # 

    



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernKineticsLayout()
    window.setup_ui()
    window.resize(1000, 800)
    window.show()

    sys.exit(app.exec())










            # folder_layout = QHBoxLayout()
        # self.folder_button = QPushButton("Select Folder", self)
        # self.folder_button.clicked.connect(self.select_folder)
        # self.folder_line = QLineEdit()
        # folder_layout.addWidget(self.folder_button)
        # folder_layout.addWidget(self.folder_line)
        # right_layout.addLayout(folder_layout)

        # csv_layout = QHBoxLayout()
        # csv_label = QLabel("Save all csv as conc with the ending")
        # self.csv_suffix_line = QLineEdit()
        # csv_layout.addWidget(csv_label)
        # csv_layout.addWidget(self.csv_suffix_line)
        # right_layout.addLayout(csv_layout)

        # self.csv_button = QPushButton("Save")
        # self.csv_button.pressed.connect(self.export_results)
        # right_layout.addWidget(self.csv_button)

        # input_layout.addLayout(right_layout)
