import os
import pandas as pd
import importlib.resources as pkg_resources

def load_dataset(name: str) -> pd.DataFrame:
    """Load a built-in dataset as a pandas DataFrame."""
    name = name.lower()
    filename = f"{name}.csv"
    try:
        # Use importlib.resources to access data inside the package
        with pkg_resources.open_text(f'geoanalytics.datasets', filename) as f:
            return pd.read_csv(f,sep='\t')
    except FileNotFoundError:
        raise ValueError(f"Dataset '{name}' not found. Check available datasets.")

def list_datasets():
    return [f.stem for f in pkg_resources.files("geoanalytics.datasets").iterdir() if f.suffix == ".csv"]