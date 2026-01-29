def get_stylesheet(file_path):
    with open(file_path, "r") as f:
        stylesheet = f.read()
    return stylesheet


# print(get_stylesheet(r".\src\styles\table_styles.css"))