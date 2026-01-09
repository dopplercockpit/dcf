"""
Excel Export Module for DCF Analysis
Generates Excel reports with financial data from analysis results.
"""

from datetime import datetime
from pathlib import Path

from excel_export import build_workbook_from_results


def save_excel_report(ticker, results):
    """
    Saves an Excel report to the user's Downloads folder.

    Args:
        ticker: Stock ticker symbol
        results: Full results object from DCF analysis

    Returns:
        str: Path to generated Excel file, or None if failed
    """
    try:
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = downloads_dir / f"DCF_{ticker}_{timestamp}.xlsx"

        workbook = build_workbook_from_results(ticker, results)
        workbook.save(filename)

        print(f"  Excel export saved: {filename}")
        return str(filename)
    except Exception as e:
        print(f"  Excel export failed: {e}")
        return None
