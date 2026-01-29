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
            # 1. 尝试标准拼音姓氏匹配
            if self.pinyin_regex:
                # 查找所有可能的匹配
                for match in self.pinyin_regex.finditer(text):
                    candidate = match.group()
                    # 检查是否为缩写格式 (如 A. ), 如果是单字母缩写则跳过
                    start, end = match.span()
                    if len(candidate) == 1 and end < len(text) and text[end] == '.':
                        continue
                    found_family = candidate
                    break
            
            # 2. 如果没匹配到姓氏，尝试“缩写+全拼”逻辑 (如 Jinduan C.)
            if not found_family and self.abbr_regex.search(text):
                # 提取出所有单词（排除缩写点号部分）
                words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
                for w in words:
                    if self.is_pinyin_word(w):
                        found_family = w
                        break
            
            # 3. 如果还是没匹配到，尝试“纯拼音全名”逻辑 (如 Haijun Zhai)
            if not found_family:
                # 提取纯字母单词
                words = re.findall(r'\b[a-zA-Z]+\b', text)
                if 2 <= len(words) <= 4: # 通常姓名单词数为 2-4
                    all_pinyin = True
                    for w in words:
                        if not self.is_pinyin_word(w):
                            all_pinyin = False
                            break
                    
                    if all_pinyin:
                        # 如果全部是拼音，通常最后一个或第一个是姓。
                        # 这里我们取最后一个作为识别出的姓（符合西化格式）
                        found_family = words[-1]
        
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
