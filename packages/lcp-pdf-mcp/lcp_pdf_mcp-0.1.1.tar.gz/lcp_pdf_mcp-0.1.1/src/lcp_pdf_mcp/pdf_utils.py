"""
PDF 處理工具模組
提供 PDF 分割、合併、取得資訊等功能
"""
import os
import zipfile
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter, PdfMerger


def create_zip_archive(source_files: list[str], output_zip_path: str) -> str:
    """
    將多個檔案壓縮成 ZIP 檔
    
    Args:
        source_files: 來源檔案路徑列表
        output_zip_path: 輸出 ZIP 檔案路徑
        
    Returns:
        建立的 ZIP 檔案路徑
    """
    if not source_files:
        raise ValueError("請提供至少一個檔案進行壓縮")
        
    output_dir = os.path.dirname(output_zip_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_files:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
            else:
                # 簡單記錄或忽略，這裡選擇忽略不存在的檔案以避免中斷
                pass
                
    return output_zip_path



def get_pdf_info(file_path: str) -> dict:
    """
    取得 PDF 檔案資訊
    
    Args:
        file_path: PDF 檔案路徑
        
    Returns:
        包含頁數、標題、作者等資訊的字典
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")
    
    reader = PdfReader(file_path)
    metadata = reader.metadata
    
    return {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "page_count": len(reader.pages),
        "title": metadata.title if metadata else None,
        "author": metadata.author if metadata else None,
        "subject": metadata.subject if metadata else None,
        "creator": metadata.creator if metadata else None,
    }


def split_pdf_by_pages(file_path: str, output_dir: Optional[str] = None) -> list[str]:
    """
    將 PDF 分割成每頁一個檔案
    
    Args:
        file_path: 來源 PDF 檔案路徑
        output_dir: 輸出目錄，預設為來源檔案所在目錄
        
    Returns:
        分割後的檔案路徑列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")
    
    reader = PdfReader(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        
        output_path = os.path.join(output_dir, f"{base_name}_page_{i}.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        output_files.append(output_path)
    
    return output_files


def split_pdf_by_range(
    file_path: str, 
    start_page: int, 
    end_page: int, 
    output_path: Optional[str] = None
) -> str:
    """
    按頁碼範圍分割 PDF
    
    Args:
        file_path: 來源 PDF 檔案路徑
        start_page: 起始頁碼（從 1 開始）
        end_page: 結束頁碼（包含）
        output_path: 輸出檔案路徑，預設為來源檔名加上頁碼範圍
        
    Returns:
        分割後的檔案路徑
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")
    
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    
    # 驗證頁碼範圍
    if start_page < 1:
        raise ValueError("起始頁碼必須大於等於 1")
    if end_page > total_pages:
        raise ValueError(f"結束頁碼不能超過總頁數 {total_pages}")
    if start_page > end_page:
        raise ValueError("起始頁碼不能大於結束頁碼")
    
    writer = PdfWriter()
    for i in range(start_page - 1, end_page):
        writer.add_page(reader.pages[i])
    
    if output_path is None:
        base_name = os.path.splitext(file_path)[0]
        output_path = f"{base_name}_pages_{start_page}-{end_page}.pdf"
    
    with open(output_path, "wb") as output_file:
        writer.write(output_file)
    
    return output_path


def split_pdf_by_pages_list(
    file_path: str, 
    pages: list[int], 
    output_path: str
) -> str:
    """
    [2026-01-16] 按指定頁碼列表擷取 PDF (支援不連續頁面)
    
    Args:
        file_path: 來源 PDF 檔案路徑
        pages: 頁碼列表（從 1 開始），如 [1, 3, 5]
        output_path: 輸出檔案路徑
        
    Returns:
        輸出檔案路徑
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")
    
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    
    # 過濾有效頁碼並排序
    valid_pages = sorted(set(p for p in pages if 1 <= p <= total_pages))
    
    if not valid_pages:
        raise ValueError(f"沒有有效的頁碼。總頁數: {total_pages}，輸入: {pages}")
    
    writer = PdfWriter()
    for page_num in valid_pages:
        writer.add_page(reader.pages[page_num - 1])  # 轉為 0-based index
    
    # 確保輸出目錄存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "wb") as output_file:
        writer.write(output_file)
    
    return output_path


def merge_pdfs(file_paths: list[str], output_path: str) -> str:
    """
    合併多個 PDF 檔案
    
    Args:
        file_paths: PDF 檔案路徑列表（按順序合併）
        output_path: 輸出檔案路徑
        
    Returns:
        合併後的檔案路徑
    """
    if not file_paths:
        raise ValueError("請提供至少一個 PDF 檔案")
    
    # 驗證所有檔案都存在
    for path in file_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到檔案: {path}")
    
    merger = PdfMerger()
    
    try:
        for path in file_paths:
            merger.append(path)
        
        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, "wb") as output_file:
            merger.write(output_file)
    finally:
        merger.close()
    
    return output_path


if __name__ == "__main__":
    # 簡單測試
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        info = get_pdf_info(test_file)
        print(f"PDF 資訊: {info}")
    else:
        print("用法: python pdf_utils.py <pdf_file>")
