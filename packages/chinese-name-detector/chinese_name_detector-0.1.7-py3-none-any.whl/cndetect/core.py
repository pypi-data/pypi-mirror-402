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
    def __init__(self, 
                 family_names_path: Optional[str] = None, 
                 pinyin_names_path: Optional[str] = None,
                 custom_names: Optional[List[str]] = None,
                 exclude_names: Optional[List[str]] = None):
        self.family_names = self.load_family_names(family_names_path)
        self.pinyin_family_names = self.load_pinyin_family_names(pinyin_names_path)
        
        # 合并自定义姓氏
        if custom_names:
            # 区分汉字和拼音
            cn_custom = [n for n in custom_names if re.search(r'[\u4e00-\u9fff]', n)]
            py_custom = [n.lower() for n in custom_names if not re.search(r'[\u4e00-\u9fff]', n)]
            
            self.family_names = sorted(list(set(self.family_names + cn_custom)), key=len, reverse=True)
            self.pinyin_family_names = sorted(list(set(self.pinyin_family_names + py_custom)), key=len, reverse=True)
            
        # 排除特定姓氏
        if exclude_names:
            exclude_set = {n.lower() for n in exclude_names}
            self.family_names = [n for n in self.family_names if n not in exclude_set and n.lower() not in exclude_set]
            self.pinyin_family_names = [n for n in self.pinyin_family_names if n.lower() not in exclude_set]

        self.pinyin_syllables = self.load_pinyin_syllables()
        # Unicode range for Chinese characters
        self.cn_regex = re.compile(r'[\u4e00-\u9fff]')
        # 预编译拼音检测正则：确保姓氏是独立的“单词”
        if self.pinyin_family_names:
            pinyin_pattern = "|".join(re.escape(n) for n in self.pinyin_family_names)
            self.pinyin_regex = re.compile(rf'(?<![a-zA-Z])({pinyin_pattern})(?![a-zA-Z])', re.IGNORECASE)
        else:
            self.pinyin_regex = None
        
        # 缩写格式正则: X. 或 Y. (不加结尾 \b，因为点号本身不是 word 字符)
        self.abbr_regex = re.compile(r'\b[A-Z]\.')

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

    def load_pinyin_syllables(self) -> set:
        path = Path(__file__).parent / "data" / "pinyin_syllables.txt"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {line.strip().lower() for line in f if line.strip()}
        except Exception:
            return set()

    def is_pinyin_word(self, word: str) -> bool:
        """判断一个单词是否由合法的拼音音节组成 (如 Jinduan, Guangfu)"""
        word = word.lower()
        if not word or not word.isalpha():
            return False
        
        n = len(word)
        dp = [False] * (n + 1)
        dp[0] = True
        
        for i in range(1, n + 1):
            # 拼音音节长度通常在 1 到 6 之间
            for j in range(max(0, i - 6), i):
                if dp[j] and word[j:i] in self.pinyin_syllables:
                    dp[i] = True
                    break
        return dp[n]

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
            # 1. 尝试标准拼音姓氏匹配（捕获所有位置）
            if self.pinyin_regex:
                candidates = []
                for match in self.pinyin_regex.finditer(text):
                    candidate = match.group()
                    start, end = match.span()
                    # 排除单字母缩写（如 A.）
                    if len(candidate) == 1 and end < len(text) and text[end] == '.':
                        continue
                    candidates.append((candidate, start))
                
                # 优先取第一个匹配（通常为姓氏）
                if candidates:
                    found_family = candidates[0][0]
            
            # 2. 如果没匹配到姓氏，尝试"缩写+拼音"逻辑 (如 Jinduan C., Li M. Wang)
            if not found_family and self.abbr_regex.search(text):
                words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
                pinyin_words = [w for w in words if self.is_pinyin_word(w)]
                if pinyin_words:
                    # 取第一个拼音单词作为姓氏
                    found_family = pinyin_words[0]
            
            # 3. 如果还是没匹配到，尝试“纯拼音全名”逻辑 (如 Haijun Zhai)
            if not found_family:
                # 提取纯字母单词
                words = re.findall(r'\b[a-zA-Z]+\b', text)
                if 2 <= len(words) <= 4:
                    pinyin_words = [w for w in words if self.is_pinyin_word(w)]
                    
                    # 如果有 1-2 个拼音词，可能是中文姓名
                    if 1 <= len(pinyin_words) <= 2:
                        found_family = pinyin_words[0]
                    # 如果全是拼音（3-4个词），取最后一个（西化格式）
                    elif len(pinyin_words) >= 3 and len(pinyin_words) == len(words):
                        found_family = pinyin_words[-1]
        
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

def get_detector(family_names_path: Optional[str] = None, 
                 pinyin_names_path: Optional[str] = None,
                 custom_names: Optional[List[str]] = None,
                 exclude_names: Optional[List[str]] = None):
    global _detector
    # 如果传入了任何自定义参数，我们创建一个新的实例以确保配置生效
    if _detector is None or family_names_path or pinyin_names_path or custom_names or exclude_names:
        _detector = ChineseNameDetect(family_names_path, pinyin_names_path, custom_names, exclude_names)
    return _detector
