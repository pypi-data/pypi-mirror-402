"""
Export wrapper for document export operations.
"""

import logging
from typing import Optional, List
from pathlib import Path

from .base import LeenoWrapper
from ..connection import get_bridge, get_pool
from ..utils.exceptions import ExportError, OperationError

logger = logging.getLogger(__name__)


class ExportWrapper(LeenoWrapper):
    """
    Wrapper for export operations.

    Handles PDF, CSV, and XPWE exports.
    """

    def __init__(self, doc_id: str):
        """
        Initialize export wrapper.

        Args:
            doc_id: Document ID
        """
        pool = get_pool()
        doc_info = pool.get(doc_id)
        super().__init__(doc_info)

    def export_pdf(
        self,
        output_path: str,
        sheets: Optional[List[str]] = None
    ) -> str:
        """
        Export document to PDF.

        Args:
            output_path: Path for output PDF
            sheets: Optional list of sheet names to export (None = all)

        Returns:
            Path to exported PDF

        Raises:
            ExportError: If export fails
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ExportError("UNO module not available")

        output_path = str(Path(output_path).resolve())

        try:
            # Set up export filter
            filter_name = "calc_pdf_Export"

            # If specific sheets requested, select them first
            if sheets:
                # Get sheet indices
                all_sheets = self._uno_doc.getSheets()
                sheet_indices = []
                for sheet_name in sheets:
                    if all_sheets.hasByName(sheet_name):
                        sheet = all_sheets.getByName(sheet_name)
                        sheet_indices.append(sheet.RangeAddress.Sheet)

                if not sheet_indices:
                    raise ExportError("No valid sheets to export", output_path)

            # Export properties
            props = [
                PropertyValue(Name="FilterName", Value=filter_name),
                PropertyValue(Name="Overwrite", Value=True),
            ]

            # Convert path to URL
            bridge = get_bridge()
            url = bridge._path_to_url(output_path)

            # Export
            self._uno_doc.storeToURL(url, tuple(props))

            logger.info(f"Exported PDF: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            raise ExportError(str(e), output_path)

    def export_csv(
        self,
        output_path: str,
        sheet_name: str,
        delimiter: str = ",",
        encoding: str = "UTF-8"
    ) -> str:
        """
        Export a sheet to CSV.

        Args:
            output_path: Path for output CSV
            sheet_name: Name of sheet to export
            delimiter: Field delimiter
            encoding: Text encoding

        Returns:
            Path to exported CSV

        Raises:
            ExportError: If export fails
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ExportError("UNO module not available")

        output_path = str(Path(output_path).resolve())

        if not self.has_sheet(sheet_name):
            raise ExportError(f"Sheet '{sheet_name}' not found", output_path)

        try:
            # Activate the sheet
            sheet = self.get_sheet(sheet_name)
            self._uno_doc.CurrentController.setActiveSheet(sheet)

            # Filter options for CSV
            # Format: delimiter,encoding,startrow,startcol
            if delimiter == ",":
                filter_options = "44,34,76,1"  # comma, quote, UTF-8
            elif delimiter == ";":
                filter_options = "59,34,76,1"  # semicolon
            elif delimiter == "\t":
                filter_options = "9,34,76,1"  # tab
            else:
                filter_options = f"{ord(delimiter)},34,76,1"

            props = [
                PropertyValue(Name="FilterName", Value="Text - txt - csv (StarCalc)"),
                PropertyValue(Name="FilterOptions", Value=filter_options),
                PropertyValue(Name="Overwrite", Value=True),
            ]

            bridge = get_bridge()
            url = bridge._path_to_url(output_path)

            self._uno_doc.storeToURL(url, tuple(props))

            logger.info(f"Exported CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise ExportError(str(e), output_path)

    def export_xpwe(self, output_path: str) -> str:
        """
        Export document to XPWE format.

        Args:
            output_path: Path for output XPWE file

        Returns:
            Path to exported file

        Raises:
            ExportError: If export fails
        """
        # XPWE export requires implementing the full XPWE format
        # This is complex and should use the LeenO export module
        raise OperationError("export_xpwe", "XPWE export not yet implemented via MCP")

    def get_export_formats(self) -> List[dict]:
        """
        Get list of supported export formats.

        Returns:
            List of format info dicts
        """
        return [
            {
                "id": "pdf",
                "name": "PDF Document",
                "extension": ".pdf",
                "description": "Portable Document Format"
            },
            {
                "id": "csv",
                "name": "CSV File",
                "extension": ".csv",
                "description": "Comma-separated values"
            },
            {
                "id": "xpwe",
                "name": "XPWE File",
                "extension": ".xpwe",
                "description": "Primus exchange format (not yet implemented)"
            },
            {
                "id": "ods",
                "name": "ODS Spreadsheet",
                "extension": ".ods",
                "description": "OpenDocument Spreadsheet"
            },
            {
                "id": "xlsx",
                "name": "Excel Spreadsheet",
                "extension": ".xlsx",
                "description": "Microsoft Excel format"
            }
        ]

    def export_ods(self, output_path: str) -> str:
        """
        Export/save document as ODS.

        Args:
            output_path: Path for output file

        Returns:
            Path to exported file
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ExportError("UNO module not available")

        output_path = str(Path(output_path).resolve())

        try:
            props = [
                PropertyValue(Name="FilterName", Value="calc8"),
                PropertyValue(Name="Overwrite", Value=True),
            ]

            bridge = get_bridge()
            url = bridge._path_to_url(output_path)

            self._uno_doc.storeToURL(url, tuple(props))

            logger.info(f"Exported ODS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting ODS: {e}")
            raise ExportError(str(e), output_path)

    def export_xlsx(self, output_path: str) -> str:
        """
        Export document as XLSX (Excel).

        Args:
            output_path: Path for output file

        Returns:
            Path to exported file
        """
        try:
            from com.sun.star.beans import PropertyValue
        except ImportError:
            raise ExportError("UNO module not available")

        output_path = str(Path(output_path).resolve())

        try:
            props = [
                PropertyValue(Name="FilterName", Value="Calc MS Excel 2007 XML"),
                PropertyValue(Name="Overwrite", Value=True),
            ]

            bridge = get_bridge()
            url = bridge._path_to_url(output_path)

            self._uno_doc.storeToURL(url, tuple(props))

            logger.info(f"Exported XLSX: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting XLSX: {e}")
            raise ExportError(str(e), output_path)
