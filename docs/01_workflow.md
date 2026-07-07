# Workflow

這個專案的目標是將日文長文本轉換成逐字拆解學習材料。

## Pipeline

```text
EPUB
↓
00_extract_epub_text.py
↓
TXT
↓
01_split_paragraphs.py
↓
chunks/
↓
02_merge_chunks.py
↓
merged_chunks.txt
↓
03_run_api.py
↓
api_outputs/
↓
04_merge_outputs.py
↓
final_output.md