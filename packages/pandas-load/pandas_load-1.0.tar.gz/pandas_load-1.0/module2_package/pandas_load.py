import pandas as pd

def load_data(file_name):
    df = pd.read_csv(file_name)
    return df