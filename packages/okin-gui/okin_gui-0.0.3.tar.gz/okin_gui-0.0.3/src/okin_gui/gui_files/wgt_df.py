from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, Signal

import pandas as pd

from okin.base.chem_logger import chem_logger

class EditableListWidgetItem(QListWidgetItem):
    def __init__(self, text):
        super().__init__()

        self.setText(text)

        self.edit_field = QLineEdit(text)
        self.setSizeHint(self.edit_field.sizeHint())

class DataFrameWidget(QWidget):
    row_selected = Signal(list)

    def __init__(self, dataframe=None, ignore_index_col=True, round_to=3):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.ignore_index_col = ignore_index_col
        self.round_to = round_to
        self.layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(0)
        self.table_widget.setRowCount(0)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.doubleClicked.connect(self.on_table_click)

        self.layout.addWidget(self.table_widget)
        self.setLayout(self.layout)

        if dataframe is not None:
            self.set_data_frame(dataframe)


    def get_data_frame(self):
        return self.dataframe
        
    def set_data_frame(self, dataframe):
        # self.dataframe = dataframe
        dataframe = dataframe.round(self.round_to)
        self.table_widget.clear()
        
        # Determine if the first column is the index
        is_index = dataframe.columns[0] in ["index", "Unnamed: 0"]

        if is_index and self.ignore_index_col:
            self.dataframe = dataframe.drop(dataframe.columns[0], axis=1)

        num_columns = len(dataframe.columns)
        headers = dataframe.columns.tolist()
        
        self.table_widget.setColumnCount(num_columns)
        self.table_widget.setRowCount(len(dataframe))

        # Set column headers
        self.table_widget.setHorizontalHeaderLabels(headers)

        # Populate the table widget with data
        for row in range(len(dataframe)):
            for col in range(num_columns):
                value = str(dataframe.iat[row, col])
                item = QTableWidgetItem(value)
                self.table_widget.setItem(row, col, item)
                item.setTextAlignment(Qt.AlignCenter)

        self.table_widget.resizeColumnsToContents()
        self.df = dataframe

    def on_table_click(self, index):
        row = index.row()
        row_content = [self.table_widget.item(row, col).text() for col in range(len(self.df.columns))]
        self.logger.info(f"Emitting {row_content = }")
        self.row_selected.emit(row_content)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    import pandas as pd

    app = QApplication(sys.argv)

    # data = {
    #     "Column1": [1, 2, 3, 4],
    #     "Column2": [5, 6, 7, 8],
    #     "Column3": [9, 10, 11, 12]
    # }

    # df = pd.DataFrame(data)
    # df["used"] = False  # Add a "used" column to the DataFrame
    df = pd.read_csv(r"C:\Users\Finn\HeinLab\projects\modules\okin_gui\examples\900.csv")

    widget = DataFrameWidget()
    widget.set_data_frame(df)
    widget.show()

    sys.exit(app.exec_())
