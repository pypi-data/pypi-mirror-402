"""
Core OCR processing functions
"""

import json
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from openai import OpenAI
from tqdm import tqdm
import pymupdf

try:
    from typhoon_ocr import prepare_ocr_messages
except ImportError:
    prepare_ocr_messages = None


def get_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> OpenAI:
    """Get OpenAI client with configuration."""
    return OpenAI(
        base_url=base_url or os.getenv("OCR_BASE_URL"),
        api_key=api_key or os.getenv("OCR_API_KEY")
    )


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF file."""
    try:
        doc = pymupdf.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        print(f"Error getting page count for {pdf_path}: {e}")
        return 0


def process_single_page(
    pdf_path: str,
    page_num: int,
    task_type: str = "default",
    client: Optional[OpenAI] = None,
    model: Optional[str] = None
) -> dict:
    """
    Process a single page of a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number (1-indexed)
        task_type: OCR task type ("default" or "structure")
        client: OpenAI client (optional, will create if not provided)
        model: Model name (optional, uses OCR_MODEL env var)
    
    Returns:
        dict with page_num, text, status, and error
    """
    if prepare_ocr_messages is None:
        raise ImportError("typhoon-ocr package is required. Install with: pip install typhoon-ocr")
    
    if client is None:
        client = get_client()
    
    if model is None:
        model = os.getenv("OCR_MODEL", "typhoon-ocr-7b")
    
    result = {
        "page": page_num,
        "text": "",
        "status": "success",
        "error": None
    }
    
    try:
        messages = prepare_ocr_messages(
            pdf_or_image_path=pdf_path,
            task_type=task_type,
            target_image_dim=1800,
            target_text_length=8000,
            page_num=page_num
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=16384,
            extra_body={
                "repetition_penalty": 1.2,
                "temperature": 0.1,
                "top_p": 0.6,
            },
        )
        
        text_output = response.choices[0].message.content
        result["text"] = text_output
        
        # Try to parse JSON and extract natural_text
        try:
            json_data = json.loads(text_output)
            natural_text = json_data.get('natural_text', "")
            natural_text = natural_text.replace("<figure>", "").replace("</figure>", "")
            natural_text = natural_text.replace("\\n", "\n")
            result["text"] = natural_text
        except json.JSONDecodeError:
            result["text"] = text_output
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        
    return result


def process_pdf_file(
    pdf_path: str,
    output_path: str,
    task_type: str = "default",
    show_progress: bool = True,
    max_workers: int = 4,
    client: Optional[OpenAI] = None,
    model: Optional[str] = None
) -> dict:
    """
    Process all pages of a PDF file and save results to JSONL.
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Path to output JSONL file
        task_type: OCR task type
        show_progress: Whether to show progress bar
        max_workers: Number of parallel workers
        client: OpenAI client (optional)
        model: Model name (optional)
    
    Returns:
        dict with processing summary
    """
    if client is None:
        client = get_client()
    
    if model is None:
        model = os.getenv("OCR_MODEL", "typhoon-ocr-7b")
    
    summary = {
        "input_file": pdf_path,
        "output_file": output_path,
        "total_pages": 0,
        "successful_pages": 0,
        "failed_pages": 0,
        "errors": []
    }
    
    page_count = get_pdf_page_count(pdf_path)
    if page_count == 0:
        summary["errors"].append("Could not read PDF or PDF has no pages")
        return summary
    
    summary["total_pages"] = page_count
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    results = [None] * page_count
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_page = {
            executor.submit(
                process_single_page, pdf_path, page_num, task_type, client, model
            ): page_num
            for page_num in range(1, page_count + 1)
        }
        
        completed_futures = as_completed(future_to_page)
        if show_progress:
            completed_futures = tqdm(
                completed_futures,
                total=page_count,
                desc=f"Processing {os.path.basename(pdf_path)}",
                unit="page"
            )
        
        for future in completed_futures:
            page_num = future_to_page[future]
            try:
                result = future.result()
                results[page_num - 1] = result
                
                if result["status"] == "success":
                    summary["successful_pages"] += 1
                else:
                    summary["failed_pages"] += 1
                    summary["errors"].append(f"Page {page_num}: {result['error']}")
            except Exception as e:
                summary["failed_pages"] += 1
                summary["errors"].append(f"Page {page_num}: {str(e)}")
                results[page_num - 1] = {
                    "page": page_num,
                    "text": "",
                    "status": "error",
                    "error": str(e)
                }
    
    elapsed = time.time() - start_time
    print(f"  Processed {page_count} pages in {elapsed:.1f}s ({elapsed/page_count:.1f}s/page)")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    return summary


def find_pdf_files(input_folder: str) -> list:
    """Find all PDF files in a folder recursively."""
    pdf_files = []
    input_path = Path(input_folder)
    
    for pdf_file in input_path.rglob("*.pdf"):
        pdf_files.append(str(pdf_file))
    
    for pdf_file in input_path.rglob("*.PDF"):
        if str(pdf_file) not in pdf_files:
            pdf_files.append(str(pdf_file))
    
    return sorted(pdf_files)


def get_output_path(input_file: str, input_folder: str, output_folder: str) -> str:
    """Calculate output path maintaining folder structure."""
    input_path = Path(input_file)
    input_base = Path(input_folder)
    
    try:
        relative_path = input_path.relative_to(input_base)
    except ValueError:
        relative_path = input_path.name
    
    output_path = Path(output_folder) / relative_path
    output_path = output_path.with_suffix('.jsonl')
    
    return str(output_path)


def process_folder(
    input_folder: str,
    output_folder: str = "output",
    task_type: str = "default",
    max_workers: int = 4,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> dict:
    """
    Process all PDF files in a folder.
    
    Args:
        input_folder: Input folder containing PDF files
        output_folder: Output folder for JSONL files
        task_type: OCR task type
        max_workers: Number of parallel workers
        base_url: API base URL (optional)
        api_key: API key (optional)
        model: Model name (optional)
    
    Returns:
        dict with overall processing summary
    """
    client = get_client(base_url, api_key)
    if model is None:
        model = os.getenv("OCR_MODEL", "typhoon-ocr-7b")
    
    overall_summary = {
        "input_folder": input_folder,
        "output_folder": output_folder,
        "total_files": 0,
        "successful_files": 0,
        "failed_files": 0,
        "total_pages": 0,
        "successful_pages": 0,
        "file_summaries": []
    }
    
    pdf_files = find_pdf_files(input_folder)
    overall_summary["total_files"] = len(pdf_files)
    
    if not pdf_files:
        print(f"No PDF files found in {input_folder}")
        return overall_summary
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    print(f"Output folder: {output_folder}")
    print(f"Task type: {task_type}")
    print(f"Workers: {max_workers}")
    print("-" * 50)
    
    for pdf_file in pdf_files:
        output_path = get_output_path(pdf_file, input_folder, output_folder)
        
        print(f"\nProcessing: {pdf_file}")
        print(f"Output: {output_path}")
        
        summary = process_pdf_file(
            pdf_path=pdf_file,
            output_path=output_path,
            task_type=task_type,
            show_progress=True,
            max_workers=max_workers,
            client=client,
            model=model
        )
        
        overall_summary["file_summaries"].append(summary)
        overall_summary["total_pages"] += summary["total_pages"]
        overall_summary["successful_pages"] += summary["successful_pages"]
        
        if summary["failed_pages"] == 0 and summary["total_pages"] > 0:
            overall_summary["successful_files"] += 1
            print(f"✓ Completed: {summary['successful_pages']}/{summary['total_pages']} pages")
        else:
            if summary["successful_pages"] > 0:
                overall_summary["successful_files"] += 1
                print(f"⚠ Partially completed: {summary['successful_pages']}/{summary['total_pages']} pages")
            else:
                overall_summary["failed_files"] += 1
                print(f"✗ Failed: {summary['errors']}")
    
    return overall_summary
