# Workflow

這個專案的目標是將日文長文本轉換成逐字拆解學習材料。

整體流程分成五個步驟：

```text
EPUB / TXT
↓
文字抽取與清理
↓
句子切分
↓
chunk 合併
↓
API 逐字拆解
↓
最終輸出合併
```

---

## Pipeline

### 00_extract_epub_text.py

將 EPUB 轉成 TXT。

主要功能：

- 依照 OPF spine 順序讀取 EPUB 章節
- 移除 ruby、rt、rb 等振假名標籤
- 清理 HTML / XHTML 內容
- 輸出純文字 TXT

如果已經有 TXT，可以跳過這一步。

---

### 01_split_paragraphs.py

將 TXT 切成句子與小檔案。

主要功能：

- 統一換行格式
- 處理日文對話引號
- 依照日文句尾標點切句
- 每 8 句輸出成一個 chunk
- 自動加上句子編號

輸出位置：

```text
sample/chunks/
```

---

### 02_merge_chunks.py

將多個 chunk 合併成 API 輸入檔。

輸出：

```text
sample/merged_chunks.txt
```

合併時會保留 FILE 編號與句子範圍，例如：

```text
<<<FILE 001 | 1-8>>>
...
<<<END FILE 001>>>
```

這樣可以追蹤每個 API 輸入區塊的來源。

---

### 03_run_api.py

讀取 `merged_chunks.txt`，逐一呼叫 LLM API 產生逐字拆解。

主要功能：

- 解析 FILE 區塊
- 呼叫 API 產生逐字拆解
- 將每個結果存成獨立檔案
- 記錄處理進度
- 檢查輸出格式
- 發現嚴重問題時自動重試

輸出位置：

```text
sample/api_outputs/
```

---

### 04_merge_outputs.py

將 API 輸出結果合併成最終 Markdown 文件。

輸出：

```text
sample/final_output.md
```

---

## Two-stage Chunking Strategy

這個專案使用兩階段切分策略。

第一階段先將長文本切成句子與小 chunk，避免句子或對話被切斷。

第二階段再將 chunk 合併成可追蹤的 API 輸入格式，保留 FILE 編號與句子範圍。

這樣可以避免：

- token 超限
- 句子被切壞
- API 輸出格式不穩
- 中途失敗後難以恢復
- 錯誤來源難以追蹤

---

## Standard Commands

從 EPUB 開始：

```powershell
python scripts/00_extract_epub_text.py "path\to\input.epub" "sample\input_sample.txt"
python scripts/01_split_paragraphs.py
python scripts/02_merge_chunks.py
python scripts/03_run_api.py
python scripts/04_merge_outputs.py
```

如果已經有 TXT：

```powershell
python scripts/01_split_paragraphs.py
python scripts/02_merge_chunks.py
python scripts/03_run_api.py
python scripts/04_merge_outputs.py
```

---

## Design Goal

這個專案不是單純呼叫 AI 翻譯，而是把日文長文本處理成一個可重複執行的 pipeline。

重點包含：

- 長文本切分
- API 批次處理
- prompt 格式控制
- 輸出驗證
- 錯誤追蹤
- 最終文件合併