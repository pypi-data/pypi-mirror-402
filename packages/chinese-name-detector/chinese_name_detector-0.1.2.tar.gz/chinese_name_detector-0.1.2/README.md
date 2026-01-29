# chinese-name-detector：中文字符与姓氏检测利器


`chinese-name-detector`（原 `cndetect`）是一个专为中文环境设计的轻量级检测工具。它能够智能识别文本中的**中文字符**以及**常见的中文姓氏**（支持汉字识别与拼音识别）。

无论你是需要批量处理 Excel 表格的非技术人员，还是希望在代码中集成姓名检测功能的开发者，`chinese-name-detector` 都能为你提供简单、高效的解决方案。

---

## 🌟 核心特性

- **双接口支持**：既有简洁的命令行工具（CLI），也有功能完备的 Python 调用接口（API）。
- **智能识别**：支持汉字姓氏（如“王”、“欧阳”）和拼音姓氏（如“Wang”、“Ouyang”）。
- **精准匹配**：拼音识别采用“独立单词”模式，有效避免如 `Alice` 中的 `li` 被误判。
- **Excel 友好**：支持一键扫描 Excel 文件并自动生成带有检测结果的新表格。
- **隐私保护**：内置日志打码功能，自动隐藏敏感姓名信息。

---

## 📥 安装指南

### 系统要求
- **Python 版本**：Python 3.8 或更高版本（支持 Windows, macOS, Linux）。

### 安装命令
打开你的终端或命令提示符，输入以下命令即可一键安装：

```bash
pip install chinese-name-detector
```

---

## 🚀 快速上手 (命令行 CLI)

安装完成后，你可以直接在终端使用 `cndetect` 命令。

### 1. 检测单条文本
输入一段文字，查看是否包含中文字符及姓氏。
```bash
cndetect single "张三"
cndetect single "Bruce Wang"
```

### 2. 批量扫描 Excel 文件
指定一个 Excel 文件及其中的某一列，工具会自动识别并保存结果。
```bash
# -c 参数用于指定 Excel 中需要检测的列名
cndetect batch data.xlsx -c "姓名"
```
*执行后，会生成一个名为 `data_cn.xlsx` 的新文件，其中会新增三列结果：*
- **HasChinese**：是否包含中文字符（✅/❌）。
- **FamilyName**：识别出的中文姓氏（拼音或汉字）。
- **ChineseDetector**：如果识别为姓名，则保留原始值，否则为空。

### 3. 使用配置文件执行任务
当你有很多文件需要处理，或者有特定的配置需求时，可以使用配置模式。
```bash
# 生成一个默认配置模板 cndetect.yaml
cndetect config

# 修改配置文件后，按配置批量运行
cndetect run -c cndetect.yaml
```

---

## 🛠️ Python API 使用教程

如果你是一名开发者，可以将 `cndetect` 集成到你的 Python 项目中。

```python
import cndetect as cnd
import pandas as pd

# --- 场景 1：单条检测 ---
result = cnd.detect("Alice Li")
if result.has_chinese:
    print(f"包含中文！命中的姓氏是: {result.family_name}")
else:
    print(f"不含中文，但识别到拼音姓氏: {result.family_name}")

# --- 场景 2：处理 Pandas DataFrame ---
data = {'name': ["王小明", "Jack Chen", "Alibaba", "Alice"]}
df = pd.DataFrame(data)

# 批量检测指定的列
df_out = cnd.detect_batch(df, column="name")

# 查看结果
# df_out 会包含原有的列，以及新增的 'HasChinese', 'FamilyName', 'ChineseDetector' 列
print(df_out)
# 注：Alibaba 里的 'ba' 和 Alice 里的 'li' 不会被误识别，因为它们不是独立单词。
```

---

## ⚙️ 配置说明 (chinese-name-detector.yaml)

你可以通过 YAML 文件自定义工具的行为：

| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `family_name_path` | 自定义姓氏库文件路径（每行一个姓氏） | `null` (使用内置库) |
| `excel.column` | CLI 批量模式默认检测的列名 | `"Name"` |
| `excel.output_suffix` | 生成结果文件的后缀名 | `"_cn"` |
| `log.level` | 日志详细程度 (INFO, DEBUG, WARNING) | `"INFO"` |
| `log.redact_names` | 是否在日志中对姓名进行打码保护 | `true` |

---

## 🔍 匹配规则详解

为了保证识别的准确性，`chinese-name-detector` 遵循以下规则：
1. **中文优先**：如果文本包含汉字，优先进行汉字姓氏匹配。
2. **独立拼音匹配**：
   - ✅ `Alice Li` -> 识别出 `Li`
   - ✅ `li_wang` -> 识别出 `li`
   - ❌ `Alibaba` -> **不会**识别出 `ba` 或 `li`（因为它们是单词的一部分）
   - ❌ `Lily` -> **不会**识别出 `li`

---

## ❓ 常见问题 (FAQ)

**Q: 为什么我的 Excel 列没被识别？**
A: 请确保你在使用 `batch` 命令时通过 `-c` 参数准确输入了列名，注意大小写和空格。

**Q: 识别出的拼音姓氏大小写不对？**
A: `chinese-name-detector` 默认会返回文本中原本的大小写样式，但匹配过程是忽略大小写的。

**Q: 如何添加一些特殊的复姓？**
A: 你可以使用 `cndetect config` 生成配置文件，在 `family_name_path` 中指定你自己的姓氏文件。

---

## ⚠️ 注意事项

- **数据隐私**：在处理包含敏感个人信息的文件时，请确保遵守相关数据隐私法规。工具内置的日志打码仅针对日志文件，不会修改你的原始 Excel 数据。
- **环境隔离**：建议在 Python 虚拟环境中安装，以避免依赖冲突。

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。
