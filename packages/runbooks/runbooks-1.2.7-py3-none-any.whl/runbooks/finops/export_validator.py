"""
Export Validation Framework - CLI-Export Parity Verification

v1.1.27 Track 3.2: Validates that exported files (CSV/JSON/PDF) match CLI output.

KISS Principle: Simple validation with clear parity scores
DRY Principle: Shared validation logic across export formats

Quality Gates:
- Row/key count match
- Cost value precision match (±$0.01 tolerance)
- Schema consistency validation
- SHA256 checksum generation
"""

import csv
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of export validation."""

    export_file: str
    format_type: str  # csv, json, pdf
    parity_score: float  # 0-100%
    row_count_match: bool
    value_precision_match: bool
    schema_match: bool
    errors: List[str]
    warnings: List[str]


class ExportValidator:
    """
    Validates export parity with CLI output.

    Ensures exported files match the data displayed in CLI tables:
    - CSV: Row counts and cost values match
    - JSON: Key counts and value precision match
    - PDF: Structure validation (placeholder for future implementation)
    """

    def __init__(self, tolerance: float = 0.01):
        """
        Initialize validator.

        Args:
            tolerance: Acceptable cost difference (default $0.01)
        """
        self.tolerance = tolerance

    def validate_csv(self, cli_data: List[Dict[str, Any]], csv_file: Path) -> ValidationResult:
        """
        Validate CSV export matches CLI data.

        Args:
            cli_data: List of dicts from CLI rendering (service, costs, etc)
            csv_file: Path to exported CSV file

        Returns:
            ValidationResult with parity score and details
        """
        errors = []
        warnings = []

        try:
            # Read CSV file
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                csv_rows = list(reader)

            # Check row count
            cli_row_count = len(cli_data)
            csv_row_count = len(csv_rows)
            row_count_match = cli_row_count == csv_row_count

            if not row_count_match:
                errors.append(f"Row count mismatch: CLI={cli_row_count}, CSV={csv_row_count}")

            # Check value precision (cost fields)
            value_precision_match = True
            for i, (cli_row, csv_row) in enumerate(zip(cli_data, csv_rows)):
                # Extract cost values (handle various formats)
                cli_cost = self._extract_cost(cli_row.get("current_cost", 0))
                csv_cost = self._extract_cost(csv_row.get("Current Month", "0"))

                if abs(cli_cost - csv_cost) > self.tolerance:
                    value_precision_match = False
                    errors.append(f"Row {i}: Cost mismatch CLI=${cli_cost:.2f}, CSV=${csv_cost:.2f}")

            # Check schema match (column headers)
            expected_columns = {"Service", "Current Month", "Previous Month", "Change (MTD)", "% Total", "Trend"}
            actual_columns = set(csv_rows[0].keys()) if csv_rows else set()
            schema_match = expected_columns.issubset(actual_columns)

            if not schema_match:
                missing = expected_columns - actual_columns
                warnings.append(f"Missing columns: {missing}")

            # Calculate parity score
            score_components = [
                100 if row_count_match else 0,
                100 if value_precision_match else 50,
                100 if schema_match else 75,
            ]
            parity_score = sum(score_components) / len(score_components)

            return ValidationResult(
                export_file=str(csv_file),
                format_type="csv",
                parity_score=parity_score,
                row_count_match=row_count_match,
                value_precision_match=value_precision_match,
                schema_match=schema_match,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"CSV validation failed: {e}")
            return ValidationResult(
                export_file=str(csv_file),
                format_type="csv",
                parity_score=0.0,
                row_count_match=False,
                value_precision_match=False,
                schema_match=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
            )

    def validate_json(self, cli_data: Dict[str, Any], json_file: Path) -> ValidationResult:
        """
        Validate JSON export matches CLI data.

        Args:
            cli_data: Dict from CLI rendering
            json_file: Path to exported JSON file

        Returns:
            ValidationResult with parity score and details
        """
        errors = []
        warnings = []

        try:
            # Read JSON file
            with open(json_file, "r") as f:
                json_data = json.load(f)

            # Check key count
            cli_key_count = len(cli_data)
            json_key_count = len(json_data)
            key_count_match = cli_key_count == json_key_count

            if not key_count_match:
                errors.append(f"Key count mismatch: CLI={cli_key_count}, JSON={json_key_count}")

            # Check value types and precision
            value_precision_match = True
            for key in cli_data.keys():
                if key not in json_data:
                    value_precision_match = False
                    errors.append(f"Missing key in JSON: {key}")
                    continue

                cli_val = cli_data[key]
                json_val = json_data[key]

                # For numeric values, check precision
                if isinstance(cli_val, (int, float)):
                    if not isinstance(json_val, (int, float)):
                        value_precision_match = False
                        errors.append(f"Type mismatch for {key}: CLI={type(cli_val)}, JSON={type(json_val)}")
                    elif abs(float(cli_val) - float(json_val)) > self.tolerance:
                        value_precision_match = False
                        errors.append(f"Value mismatch for {key}: CLI={cli_val}, JSON={json_val}")

            # Schema match (basic structure validation)
            schema_match = (
                all(key in json_data for key in ["account_id", "current_month", "services"])
                if isinstance(json_data, dict)
                else False
            )

            if not schema_match:
                warnings.append("Expected schema keys missing (account_id, current_month, services)")

            # Calculate parity score
            score_components = [
                100 if key_count_match else 0,
                100 if value_precision_match else 50,
                100 if schema_match else 75,
            ]
            parity_score = sum(score_components) / len(score_components)

            return ValidationResult(
                export_file=str(json_file),
                format_type="json",
                parity_score=parity_score,
                row_count_match=key_count_match,
                value_precision_match=value_precision_match,
                schema_match=schema_match,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"JSON validation failed: {e}")
            return ValidationResult(
                export_file=str(json_file),
                format_type="json",
                parity_score=0.0,
                row_count_match=False,
                value_precision_match=False,
                schema_match=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
            )

    def validate_pdf(self, cli_data: Any, pdf_file: Path) -> ValidationResult:
        """
        Validate PDF export structure (placeholder).

        Args:
            cli_data: Data from CLI rendering
            pdf_file: Path to exported PDF file

        Returns:
            ValidationResult (basic file existence check)
        """
        # v1.1.27: Basic validation - file exists and has content
        errors = []
        warnings = ["PDF content validation not implemented (future enhancement)"]

        file_exists = pdf_file.exists()
        has_content = pdf_file.stat().st_size > 0 if file_exists else False

        if not file_exists:
            errors.append(f"PDF file not found: {pdf_file}")

        parity_score = 100.0 if (file_exists and has_content) else 0.0

        return ValidationResult(
            export_file=str(pdf_file),
            format_type="pdf",
            parity_score=parity_score,
            row_count_match=file_exists,
            value_precision_match=has_content,
            schema_match=True,  # No schema validation for PDF
            errors=errors,
            warnings=warnings,
        )

    def generate_checksums(self, export_files: List[Path], output_file: Optional[Path] = None) -> Dict[str, str]:
        """
        Generate SHA256 checksums for export files.

        Args:
            export_files: List of files to checksum
            output_file: Optional path to write checksums.txt

        Returns:
            Dict mapping filename to SHA256 hash
        """
        checksums = {}

        for file_path in export_files:
            if not file_path.exists():
                logger.warning(f"File not found for checksum: {file_path}")
                continue

            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            checksums[file_path.name] = sha256_hash.hexdigest()

        # Write to file if requested
        if output_file:
            with open(output_file, "w") as f:
                for filename, checksum in checksums.items():
                    f.write(f"{checksum}  {filename}\n")

        return checksums

    def _extract_cost(self, value: Any) -> float:
        """
        Extract numeric cost from various formats.

        Args:
            value: Cost value (float, int, or string with $ and commas)

        Returns:
            Numeric cost value
        """
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Remove $, commas, and whitespace
            cleaned = value.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        return 0.0
