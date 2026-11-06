"""Run `python export_excel.py --output-dir DIRECTORY` to export both workbooks."""
import sys
from database_cli import main


if __name__ == '__main__':
    main(['export', *sys.argv[1:]])
