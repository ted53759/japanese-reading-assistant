# Japanese Reading Assistant Dashboard

Japanese Reading Assistant 的作品集前端，以 Vue 3、Composition API 與 Vite 建立。介面示範長文本任務監控、日文逐句閱讀及 AI 輸出品質檢核；所有內容都來自本機 mock JSON，不包含上傳、資料庫或 API 呼叫。

## 功能

- 成功、警告、失敗、待複查任務總覽
- 狀態、問題類型與關鍵字交叉篩選
- 日文原句、假名、逐詞拆解與繁體中文翻譯
- 句子遺漏、編號重複、括號格式與人工複查結果
- 初學者單字卡與進階者詞性／文法表格
- 手機任務／詳情切換與桌面雙欄工作區
- 閱讀模式偏好儲存在瀏覽器本機

## 本機執行

需求：Node.js 22.12 或更新版本、pnpm 11。

```powershell
cd web
pnpm install
pnpm dev
```

建立 production 版本：

```powershell
pnpm build
pnpm preview
```

## 資料與架構

- `src/data/tasks.json`：作品集模擬任務、句子、tokens 與檢核結果
- `src/App.vue`：Dashboard 狀態、篩選與互動
- `src/style.css`：品牌視覺、響應式與無障礙狀態
- `public/og.png`：社群分享預覽圖

統計與品質分數由前端依任務資料計算。前端不會讀取根目錄的 `sample/`，因此可獨立部署，也不會影響 Python pipeline。

## GitHub Pages

根目錄的 `.github/workflows/deploy-pages.yml` 會在 `main` 分支的 `web/` 有變更時建置並發布 `web/dist`。Vite 的 production base 已設定為 `/japanese-reading-assistant/`。

正式網址：<https://ted53759.github.io/japanese-reading-assistant/>
