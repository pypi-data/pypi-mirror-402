import re
from dataclasses import dataclass
from typing import List, Optional, Iterable, Union
from pathlib import Path
import pandas as pd
from .logger import logger, redact_name

@dataclass
class DetectResult:
    text: str
    has_chinese: bool
    family_name: Optional[str] = None

class ChineseNameDetect:
    def __init__(self, family_names_path: Optional[str] = None, pinyin_names_path: Optional[str] = None):
        self.family_names = self.load_family_names(family_names_path)
        self.pinyin_family_names = self.load_pinyin_family_names(pinyin_names_path)
        # Unicode range for Chinese characters
        self.cn_regex = re.compile(r'[\u4e00-\u9fff]')
        # 预编译拼音检测正则：确保姓氏是独立的“单词”（不被其他字母包围）
        # 使用 (?<![a-zA-Z]) 和 (?![a-zA-Z]) 代替 \b，以确保即使是下划线或数字也能作为分隔符
        if self.pinyin_family_names:
            pinyin_pattern = "|".join(re.escape(n) for n in self.pinyin_family_names)
            self.pinyin_regex = re.compile(rf'(?<![a-zA-Z])({pinyin_pattern})(?![a-zA-Z])', re.IGNORECASE)
        else:
            self.pinyin_regex = None

    def load_family_names(self, path: Optional[str] = None) -> List[str]:
        if path is None:
            # Load default
            path = Path(__file__).parent / "data" / "family.txt"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]
                # Sort by length descending to match longest first (e.g. 欧阳 before 欧)
                return sorted(names, key=len, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to load family names from {path}: {e}. Falling back to default.")
            if path != Path(__file__).parent / "data" / "family.txt":
                return self.load_family_names(None)
            return []

    def load_pinyin_family_names(self, path: Optional[str] = None) -> List[str]:
        if path is None:
            path = Path(__file__).parent / "data" / "pinyin_family.txt"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                names = [line.strip().lower() for line in f if line.strip()]
                # Sort by length descending to match longest first
                return sorted(names, key=len, reverse=True)
        except Exception as e:
            logger.warning(f"Failed to load pinyin family names from {path}: {e}")
            return []

    def detect(self, text: str) -> DetectResult:
        if not text or not isinstance(text, str):
            return DetectResult(text=str(text), has_chinese=False)
        
        has_chinese = bool(self.cn_regex.search(text))
        found_family = None
        
        if has_chinese:
            # 中文字符检测：识别成中文姓氏
            for name in self.family_names:
                if name in text:
                    found_family = name
                    break
        else:
            # 非中文字符检测：按照拼音识别（不区分大小写）
            if self.pinyin_regex:
                match = self.pinyin_regex.search(text)
                if match:
                    found_family = match.group()
        
        return DetectResult(text=text, has_chinese=has_chinese, family_name=found_family)

    def detect_batch(self, data: Union[Iterable[str], pd.DataFrame, pd.Series], column: Optional[str] = None) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            if column is None:
                raise ValueError("Column name must be specified when passing a DataFrame.")
            if column not in data.columns:
                # Basic similarity check could be added here
                raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {list(data.columns)}")
            
            series = data[column]
        elif isinstance(data, pd.Series):
            series = data
        else:
            series = pd.Series(data)

        def _row_detect(val):
            res = self.detect(str(val))
            has_cn = "✅" if res.has_chinese else "❌"
            fam_name = res.family_name if res.family_name else ""
            
            # ChineseDetector 逻辑
            detector_val = val if (res.has_chinese or fam_name) else ""
            
            return pd.Series({
                "HasChinese": has_cn,
                "FamilyName": fam_name,
                "ChineseDetector": detector_val
            })

        results = series.apply(_row_detect)
        
        if isinstance(data, pd.DataFrame):
            df_out = pd.concat([data, results], axis=1)
            return df_out
        else:
            df_out = pd.concat([series, results], axis=1)
            df_out.columns = ["Original", "HasChinese", "FamilyName", "ChineseDetector"]
            return df_out

# Singleton instance for easy access
_detector = None

def get_detector(family_names_path: Optional[str] = None, pinyin_names_path: Optional[str] = None):
    global _detector
    if _detector is None or family_names_path or pinyin_names_path:
        _detector = ChineseNameDetect(family_names_path, pinyin_names_path)
    return _detector
