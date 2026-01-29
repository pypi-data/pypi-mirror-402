# PDF Tools MCP Server

這是一個基於 [FastMCP](https://github.com/jlowin/fastmcp) 構建的 MCP (Model Context Protocol) 伺服器，提供多種 PDF 處理工具。

## 功能

- **PDF 分割 (Split)**:
  - 支援將每頁分割為獨立檔案 (`split_pdf_all`)
  - 支援指定頁碼範圍分割 (`split_pdf_range`)
  - 支援指定特定頁碼 (如 1, 3, 5) 分割 (`split_pdf_pages`)
  - 自動打包分割後的檔案為 ZIP 下載
- **PDF 合併 (Merge)**:
  - 將多個 PDF 檔案合併為一個 (`merge_pdfs`)
- **安全功能**:
  - 自動產生 UUID 檔名以防止預測
  - 自動清理過期檔案 (預設 5 分鐘)
  - 禁止目錄列表瀏覽

## 安裝

```bash
pip install pdf-tool-mcp
```

## 使用方法

### 啟動伺服器

您可以直接透過命令列啟動：

```bash
pdf-tool-mcp
```

或使用 MCP Inspector 進行測試：

```bash
npx @modelcontextprotocol/inspector pdf-tool-mcp
```

### 工具說明

| 工具名稱 | 描述 |
|----------|------|
| `split_pdf_all` | 將 PDF 的每一頁分割成單獨的檔案 |
| `split_pdf_range` | 擷取 PDF 的連續頁面範圍 (例如第 1-5 頁) |
| `split_pdf_pages` | 擷取 PDF 的指定頁面 (不連續，例如第 1, 3, 5 頁) |
| `merge_pdfs` | 合併多個 PDF 檔案 |

## 開發

1. 下載專案
2. 安裝相依套件:
   ```bash
   pip install -e .
   ```
3. 執行伺服器:
   ```bash
   python src/lcp_chart_mcp/server.py
   ```

## Requirements

- Python 3.10+
- fastmcp
- pypdf2