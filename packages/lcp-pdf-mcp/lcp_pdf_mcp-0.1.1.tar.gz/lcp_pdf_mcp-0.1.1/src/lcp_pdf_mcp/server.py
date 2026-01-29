"""
PDF Tools MCP Server
提供 PDF 處理功能 (基於 FastMCP)
"""
import os
import io
import json
import shutil
import threading
import http.server
import socketserver
from typing import Optional, List
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 嘗試匯入 PDF Utils
try:
    from pdf_utils import (
        get_pdf_info as _get_pdf_info,
        split_pdf_by_pages as _split_pdf_by_pages,
        split_pdf_by_range as _split_pdf_by_range,
        split_pdf_by_pages_list as _split_pdf_by_pages_list,
        merge_pdfs as _merge_pdfs,
        create_zip_archive as _create_zip_archive,
    )
except ImportError:
    # Fallback for docker environment where path might differ
    import sys
    sys.path.append(os.path.dirname(__file__))
    from pdf_utils import (
        get_pdf_info as _get_pdf_info,
        split_pdf_by_pages as _split_pdf_by_pages,
        split_pdf_by_range as _split_pdf_by_range,
        split_pdf_by_pages_list as _split_pdf_by_pages_list,
        merge_pdfs as _merge_pdfs,
        create_zip_archive as _create_zip_archive,
    )

# 建立 FastMCP 伺服器
mcp = FastMCP("PDF Tools 📄")

# 輸出目錄設定
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------------------
# [2026-01-16] 資安強化：停用目錄列表 + 自動清理
# 功能：
#   1. SecureHandler - 禁止瀏覽目錄，只允許下載指定檔名
#   2. cleanup_old_files - 刪除超過 5 分鐘的舊檔案
#   3. UUID 檔名 - 增加隨機性，防止猜測
# -------------------------------------------------------------
HTTP_PORT = 8090
CLEANUP_INTERVAL_SECONDS = 60  # 每 60 秒執行一次清理
CLEANUP_MAX_AGE_MINUTES = 5    # 刪除建立超過 5 分鐘的檔案

import time
import uuid

def cleanup_old_files():
    """[2026-01-16] 自動清理舊檔案的背景執行緒"""
    while True:
        try:
            now = time.time()
            for filename in os.listdir(OUTPUT_DIR):
                filepath = os.path.join(OUTPUT_DIR, filename)
                if os.path.isfile(filepath):
                    file_age_minutes = (now - os.path.getmtime(filepath)) / 60
                    if file_age_minutes > CLEANUP_MAX_AGE_MINUTES:
                        os.remove(filepath)
                        print(f"🗑️ 已清理過期檔案: {filename}")
        except Exception as e:
            print(f"清理錯誤: {e}")
        time.sleep(CLEANUP_INTERVAL_SECONDS)

# 啟動清理執行緒
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

def serve_files():
    """在背景啟動 HTTP Server 提供檔案下載"""
    # [2026-01-16] 資安強化：自訂 Handler 禁用目錄列表
    class SecureHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=OUTPUT_DIR, **kwargs)
        
        def list_directory(self, path):
            """[2026-01-16] 禁止目錄列表，回傳 403 Forbidden"""
            self.send_error(403, "Forbidden: Directory listing is disabled")
            return None

    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.ThreadingTCPServer(("", HTTP_PORT), SecureHandler) as httpd:
        print(f"📂 File Server serving at port {HTTP_PORT} (secure mode)")
        httpd.serve_forever()

# 啟動檔案伺服器執行緒
file_server_thread = threading.Thread(target=serve_files, daemon=True)
file_server_thread.start()

def generate_secure_filename(base_name: str, suffix: str) -> str:
    """[2026-01-16] 產生帶有 UUID 的安全檔名"""
    short_uuid = str(uuid.uuid4())[:8]
    return f"{short_uuid}_{base_name}{suffix}"

def get_download_url(filename: str) -> str:
    """產生檔案下載 URL"""
    return f"http://localhost:9090/{filename}"
 


@mcp.prompt()
def pdf_tools_guide() -> str:
    return f"""
    這個Tools提供以下功能，當使用者要進行分割或合併PDF的時候使用不需要進行RAG：
    1. 分割 PDF (全頁面)：{split_pdf_all}
    2. 分割 PDF (指定範圍)：{split_pdf_range}
    3. 合併 PDF：{merge_pdfs}
    4. 分割 PDF (指定頁面)：{split_pdf_pages}
    
    使用須知：
    - 從對話中尋找檔案相關資訊或attached_files中的檔案
    - 不需要解讀PDF中的文字內容，這個工具的使用只是分割與合併PDF檔案。
    - 跳過RAG，只需要對檔案進行動作。
    - 如果需要分割「最後一頁」或「特定範圍」但不知道總頁數，請直接呼叫 {split_pdf_range} 並填寫預估的結束頁碼 (例如 9999)，系統會自動修正為實際的最後一頁。
    - 所有操作完成後，都會提供 ZIP 壓縮檔的下載連結並用Markdown語法包覆連結。
    """

@mcp.tool(name="split_pdf_all")
def split_pdf_all(
    filename: str = None,
    file_id: str = None,
    file_path: str = None,
    __files__: list[dict] = None
) -> str:
    """
    將 PDF 分割成每頁一個獨立的檔案，並打包成 ZIP 下載
    """
    # Inline resolve_file_path logic
    real_path = None
    # [2026-01-19] 優先檢查 /tmp/{filename}
    if not file_path and filename:
        potential_path = os.path.join("/tmp", filename)
        if os.path.exists(potential_path):
            file_path = potential_path

    if file_path and os.path.exists(file_path):
        real_path = file_path
    else:
        search_dir = "/tmp"
        if os.path.exists(search_dir):
            try:
                for f in os.listdir(search_dir):
                    if (filename and filename in f) or (file_id and file_id in f):
                        real_path = os.path.join(search_dir, f)
                        break
            except:
                pass

    if not real_path:
        return f"找不到檔案: {filename}"

    try:
        output_files = _split_pdf_by_pages(real_path, OUTPUT_DIR)
        
        # [2026-01-16] 使用 UUID 安全檔名
        base_name = os.path.splitext(os.path.basename(real_path))[0]
        zip_filename = generate_secure_filename(base_name, "_split.zip")
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        _create_zip_archive(output_files, zip_path)
        
        results = [os.path.basename(f) for f in output_files]
        return f"成功分割成 {len(results)} 個檔案，並已打包下載。\n檔案列表:\n" + "\n".join(results[:5]) + ("\n..." if len(results) > 5 else "") + f"\n\n⬇️ 下載 ZIP: {get_download_url(zip_filename)}"
    except Exception as e:
        return f"Error splitting PDF: {str(e)}"

@mcp.tool(name="split_pdf_range")
def split_pdf_range(
    start_page: int,
    end_page: int,
    filename: str = None,
    file_id: str = None,
    file_path: str = None,
    __files__: list[dict] = None
) -> str:
    """
    擷取 PDF 的指定頁面範圍存為新檔案，並提供 ZIP 下載。
    如果 end_page 超過實際頁數，會自動修正為最後一頁。
    """
    # Inline resolve_file_path logic
    real_path = None
    # [2026-01-19] 優先檢查 /tmp/{filename}
    if not file_path and filename:
        potential_path = os.path.join("/tmp", filename)
        if os.path.exists(potential_path):
            file_path = potential_path

    if file_path and os.path.exists(file_path):
        real_path = file_path
    else:
        search_dir = "/tmp"
        if os.path.exists(search_dir):
            try:
                for f in os.listdir(search_dir):
                    if (filename and filename in f) or (file_id and file_id in f):
                        real_path = os.path.join(search_dir, f)
                        break
            except:
                pass

    if not real_path:
        return f"找不到檔案: {filename}"

    try:
        # 取得實際頁數以進行因應
        info = _get_pdf_info(real_path)
        total_pages = info.get('page_count', 0)
        
        # 自動修正頁碼範圍
        original_end_page = end_page
        if end_page > total_pages:
            end_page = total_pages
            
        if start_page > total_pages:
             return f"錯誤：起始頁碼 ({start_page}) 超過檔案總頁數 ({total_pages})。"

        base_name = os.path.splitext(os.path.basename(real_path))[0]
        output_filename = f"{base_name}_pages_{start_page}-{end_page}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        result_path = _split_pdf_by_range(real_path, start_page, end_page, output_path)
        
        # [2026-01-16] 使用 UUID 安全檔名
        zip_filename = generate_secure_filename(base_name, f"_pages_{start_page}-{end_page}.zip")
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        _create_zip_archive([result_path], zip_path)

        msg = f"成功擷取頁面 {start_page}-{end_page} (總頁數: {total_pages})。\n檔案: {os.path.basename(result_path)}\n\n⬇️ 下載 ZIP: {get_download_url(zip_filename)}"
        if original_end_page > total_pages:
            msg += f"\n(備註: 您輸入的結束頁碼 {original_end_page} 超過總頁數，已自動修正為 {total_pages})"
            
        return msg
    except Exception as e:
        return f"Error splitting PDF range: {str(e)}"

@mcp.tool(name="split_pdf_pages")
def split_pdf_pages(
    pages: list[int],
    filename: str = None,
    file_id: str = None,
    file_path: str = None,
    __files__: list[dict] = None
) -> str:
    """
    擷取指定的特定頁面 (支援不連續頁面，如 1, 3, 5)
    """
    # Inline resolve_file_path logic
    real_path = None
    # [2026-01-19] 優先檢查 /tmp/{filename}
    if not file_path and filename:
        potential_path = os.path.join("/tmp", filename)
        if os.path.exists(potential_path):
            file_path = potential_path

    if file_path and os.path.exists(file_path):
        real_path = file_path
    else:
        search_dir = "/tmp"
        if os.path.exists(search_dir):
            try:
                for f in os.listdir(search_dir):
                    if (filename and filename in f) or (file_id and file_id in f):
                        real_path = os.path.join(search_dir, f)
                        break
            except:
                pass

    if not real_path:
        return f"找不到檔案: {filename}"

    try:
        # 取得總頁數
        info = _get_pdf_info(real_path)
        total_pages = info.get('page_count', 0)
        
        # 過濾有效頁碼
        valid_pages = sorted(set(p for p in pages if 1 <= p <= total_pages))
        invalid_pages = [p for p in pages if p < 1 or p > total_pages]
        
        if not valid_pages:
            return f"錯誤：沒有有效的頁碼。總頁數: {total_pages}，輸入: {pages}"

        base_name = os.path.splitext(os.path.basename(real_path))[0]
        pages_str = "_".join(str(p) for p in valid_pages[:5])  # 限制檔名長度
        if len(valid_pages) > 5:
            pages_str += "_etc"
        output_filename = f"{base_name}_pages_{pages_str}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        result_path = _split_pdf_by_pages_list(real_path, valid_pages, output_path)
        
        # [2026-01-16] 使用 UUID 安全檔名
        zip_filename = generate_secure_filename(base_name, f"_pages_{pages_str}.zip")
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        _create_zip_archive([result_path], zip_path)

        msg = f"成功擷取頁面 {valid_pages} (總頁數: {total_pages})。\n檔案: {os.path.basename(result_path)}\n\n⬇️ 下載 ZIP: {get_download_url(zip_filename)}"
        if invalid_pages:
            msg += f"\n(備註: 以下頁碼無效已被忽略: {invalid_pages})"
            
        return msg
    except Exception as e:
        return f"Error splitting PDF pages: {str(e)}"

@mcp.tool(name="merge_pdfs")
def merge_pdfs(
    filenames: list[str],
    output_filename: str = "merged.pdf",
    __files__: list[dict] = None
) -> str:
    """
    合併多個 PDF 檔案，並提供 ZIP 下載
    """
    real_paths = []
    missing_files = []
    
    for fname in filenames:
        # Inline resolve_file_path logic
        path = None
        # Check direct path (unlikely for filename input but good to have)
        if os.path.exists(fname):
            path = fname
        # [2026-01-19] 優先檢查 /tmp/{filename}
        elif os.path.exists(os.path.join("/tmp", fname)):
            path = os.path.join("/tmp", fname)
        else:
             # Search in /tmp
            search_dir = "/tmp"
            if os.path.exists(search_dir):
                try:
                    for f in os.listdir(search_dir):
                        if fname in f: # Match filename
                            path = os.path.join(search_dir, f)
                            break
                except:
                    pass
        
        if path:
            real_paths.append(path)
        else:
            missing_files.append(fname)
            
    if missing_files:
        return f"無法找到以下檔案，請確認是否已上傳:\n" + "\n".join(missing_files)
        
    try:
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"
            
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        result_path = _merge_pdfs(real_paths, output_path)
        
        # [2026-01-16] 使用 UUID 安全檔名
        base_name = os.path.splitext(output_filename)[0]
        zip_filename = generate_secure_filename(base_name, "_merged.zip")
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)
        _create_zip_archive([result_path], zip_path)
        
        return f"成功合併 {len(real_paths)} 個檔案。\n輸出檔案: {os.path.basename(result_path)}\n\n 下載 ZIP: {get_download_url(zip_filename)}"
    except Exception as e:
        return f"Error merging PDFs: {str(e)}"

def main():
    """Entry point for PDF Tools MCP Server."""
    mcp.run()

if __name__ == "__main__":
    main()
