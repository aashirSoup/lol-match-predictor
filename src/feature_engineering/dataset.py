"""Assembles final train/test datasets."""


import json
from pathlib import Path

import pandas as pd

from src.feature_engineering.parser import parse_match


def create_pd_data_frame(data_dir: str = 'data/raw') -> pd.DataFrame:
    rows = []
    for file in Path(data_dir).glob("*.json"):
        with open(file, encoding='utf-8') as f:
            match_data = json.load(f)
        result = parse_match(match_data)
        if result is not None:
            rows.append(result)

    df = pd.DataFrame(rows).fillna(0).astype(int)
    return df
