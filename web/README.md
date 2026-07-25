# Japanese Reading Assistant Web

這是原有 Python pipeline 的本機操作介面。介面會將 TXT 以每批 5、10 或 20 句逐批處理，保留全域句子編號，並把各批結果累積成同一份 TXT／JSON 下載檔。處理時會同時顯示整份文件與目前批次的真實逐句進度，也能在目前句子完成後暫停。

## 安裝

在專案根目錄建立 Python 虛擬環境並安裝依賴：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

安裝前端依賴：

```powershell
cd web
pnpm install
```

## 開發模式

第一個終端機：

```powershell
.\.venv\Scripts\python.exe web\server.py
```

第二個終端機：

```powershell
cd web
pnpm dev
```

開啟 `http://127.0.0.1:5173`。

## 建置後執行

```powershell
cd web
pnpm build
cd ..
.\.venv\Scripts\python.exe web\server.py
```

開啟 `http://127.0.0.1:8000`。

API Key 只會送到 `127.0.0.1` 的本機 Python 服務，僅在當次請求的記憶體中使用，不會寫入檔案。完成後可下載保留固定排版的 UTF-8 TXT，或下載 JSON。
