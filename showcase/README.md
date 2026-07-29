# Japanese Reading Assistant｜公開展示版

這是給履歷與作品集瀏覽者使用的互動展示頁。

展示頁使用自製的日文短文與預先準備的結果，呈現工具的核心流程：

- 日文文本切句預覽
- 模擬處理進度
- 初學者／進階者閱讀模式
- 單字、假名與繁體中文翻譯
- 輸出品質檢核提醒

## 安全性

展示頁不會要求或儲存 OpenAI API Key，也不會上傳使用者檔案。
實際可處理 TXT／EPUB 與 OpenAI API 的本機工具位於專案根目錄的 `web/`。

## 本機執行

```bash
pnpm install
pnpm dev
```
