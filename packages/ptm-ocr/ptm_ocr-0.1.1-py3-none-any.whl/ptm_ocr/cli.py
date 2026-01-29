"""
Command Line Interface for PTM-OCR
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from .core import process_folder


def main():
    """Main entry point for CLI."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="PTM-OCR: Batch OCR Processing for Thai Documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ptm-ocr data/pdfs
  ptm-ocr data --output output --workers 8
  ptm-ocr documents --task-type structure

Environment Variables:
  OCR_BASE_URL  API endpoint URL
  OCR_API_KEY   API authentication key
  OCR_MODEL     Model name (default: typhoon-ocr-7b)

Output format (JSONL):
  Each line contains: {"page": N, "text": "...", "status": "success/error"}
        """
    )
    
    parser.add_argument(
        "input_folder",
        help="Input folder containing PDF files"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output folder for JSONL files (default: output)"
    )
    
    parser.add_argument(
        "-t", "--task-type",
        choices=["default", "structure"],
        default="default",
        help="OCR task type (default: default)"
    )
    
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--base-url",
        help="Override OCR_BASE_URL environment variable"
    )
    
    parser.add_argument(
        "--api-key",
        help="Override OCR_API_KEY environment variable"
    )
    
    parser.add_argument(
        "--model",
        help="Override OCR_MODEL environment variable"
    )
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.isdir(args.input_folder):
        print(f"Error: Input folder '{args.input_folder}' does not exist")
        sys.exit(1)
    
    # Check environment variables
    base_url = args.base_url or os.getenv("OCR_BASE_URL")
    api_key = args.api_key or os.getenv("OCR_API_KEY")
    
    if not base_url or not api_key:
        print("Error: OCR_BASE_URL and OCR_API_KEY must be set")
        print("Set them via environment variables or --base-url/--api-key flags")
        sys.exit(1)
    
    # Process
    summary = process_folder(
        input_folder=args.input_folder,
        output_folder=args.output,
        task_type=args.task_type,
        max_workers=args.workers,
        base_url=base_url,
        api_key=api_key,
        model=args.model
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("PROCESSING COMPLETE")
    print("=" * 50)
    print(f"Total files: {summary['total_files']}")
    print(f"Successful: {summary['successful_files']}")
    print(f"Failed: {summary['failed_files']}")
    print(f"Pages: {summary['successful_pages']}/{summary['total_pages']}")


if __name__ == "__main__":
    main()
