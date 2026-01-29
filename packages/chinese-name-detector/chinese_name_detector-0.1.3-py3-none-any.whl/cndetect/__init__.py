from typing import List, Optional, Iterable, Union
import pandas as pd

__version__ = "0.1.0"

def detect(text: str):
    from .core import get_detector
    return get_detector().detect(text)

def detect_batch(data: Union[Iterable[str], pd.DataFrame, pd.Series], *, column: Optional[str] = None):
    from .core import get_detector
    return get_detector().detect_batch(data, column=column)

def load_family_names(path: Optional[str] = None):
    from .core import get_detector
    return get_detector(family_names_path=path).family_names

def set_logger(level: str = "INFO", file: Optional[str] = None):
    from .logger import setup_logger
    setup_logger(level=level, log_file=file)
