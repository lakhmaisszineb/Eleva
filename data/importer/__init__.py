"""
data.importer – Safe import of company data (CSV/Excel).

Pipeline:
1. Read header (column names only)
2. LLM maps columns to Eleva schema
3. Clean + validate rows
4. Write normalized JSON for CompanyStore
"""

from data.importer.csv_importer import import_csv

__all__ = ["import_csv"]