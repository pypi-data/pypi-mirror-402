import numpy as np

def calculate_r_squared(y_actual, y_fitted):
    y_mean = np.mean(y_actual)
    ss_total = np.sum((y_actual - y_mean) ** 2)
    ss_residual = np.sum((y_actual - y_fitted) ** 2)
    r_squared = 1 - (ss_residual / ss_total)
    return r_squared