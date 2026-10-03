"""Synthetic row/workbook and immutable-source oracles; no acquisition in tests."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from inventory_intelligence import public_sales as sales
from scripts.public_sales_adapter import verify_source


class PublicSalesOracles(unittest.TestCase):
    def row(self, invoice="536365", item="00123", qty=3, day=datetime(2010, 12, 1, 8, 26)):
        return dict(InvoiceNo=invoice, StockCode=item, Quantity=qty, InvoiceDate=day)

    def adapt(self, rows):
        return sales.adapt_rows(list(enumerate(rows, 2)), archive_sha256="a" * 64,
                                sheet="Online Retail", expected_rows=len(rows))

    def test_gross_totals_cancellations_and_returns_remain_separate(self):
        result = self.adapt([self.row(qty=3), self.row(invoice="536366", qty=4),
            self.row(invoice="C536365", qty=-3), self.row(invoice="c536367", qty=2),
            self.row(invoice="536368", qty=-1), self.row(invoice="536369", qty=0)])
        self.assertEqual(result["audit"]["status"], "assessable")
        self.assertEqual(result["series"]["00123"][0], 7)
        self.assertEqual(result["audit"]["counts"]["included_rows"], 2)
        self.assertEqual(result["audit"]["counts"]["cancellation_rows"], 2)
        self.assertEqual(result["audit"]["counts"]["nonpositive_non_cancelled_rows"], 2)
        self.assertEqual(result["audit"]["counts"]["gross_positive_units"], 7)
        self.assertEqual(result["audit"]["availability"], "unknown")

    def test_source_identity_is_not_invoice_item_and_repeats_keep_units(self):
        result = self.adapt([self.row(), self.row()])
        self.assertEqual(result["series"]["00123"][0], 6)
        self.assertEqual(result["audit"]["counts"]["repeated_invoice_stock_pairs"], 1)
        duplicate = sales.adapt_rows([(2, self.row()), (2, self.row())], archive_sha256="a" * 64,
                                    sheet="Online Retail", expected_rows=2)
        self.assertEqual(duplicate["audit"]["status"], "not_assessable")
        self.assertIsNone(duplicate["series"])

    def test_calendar_zeros_preserve_item_codes_and_raw_inputs(self):
        rows = [self.row(), self.row(invoice=536367, item=123, qty=2,
                                    day=datetime(2010, 12, 2))]
        before = deepcopy(rows)
        result = self.adapt(rows)
        self.assertEqual(result["series"]["00123"][:3], [3, 0, 0])
        self.assertEqual(result["series"]["123"][:3], [0, 2, 0])
        self.assertEqual(len(result["series"]["123"]), 374)
        self.assertEqual(rows, before)

    def test_invalid_required_values_block_whole_extraction_including_zeros(self):
        for field, bad in (("Quantity", True), ("Quantity", 1.0), ("Quantity", None),
            ("InvoiceDate", None), ("InvoiceDate", "2010-12-01"),
            ("InvoiceDate", datetime(2010, 12, 1, tzinfo=timezone.utc)),
            ("InvoiceDate", datetime(2012, 1, 1)), ("StockCode", None),
            ("InvoiceNo", " 536365"), ("InvoiceNo", True)):
            row = self.row(); row[field] = bad
            with self.subTest(field=field, bad=bad):
                result = self.adapt([self.row(), row])
                self.assertEqual(result["audit"]["status"], "not_assessable")
                self.assertEqual(result["audit"]["counts"]["invalid_rows"], 1)
                self.assertIsNone(result["series"])
                self.assertIsNone(result["source_seen_days"])

    def test_count_and_row_coverage_failure_cannot_pass_on_valid_subset(self):
        for rows in ([(2, self.row())], [(2, self.row()), (4, self.row())]):
            result = sales.adapt_rows(rows, archive_sha256="a" * 64, sheet="Online Retail", expected_rows=2)
            self.assertEqual(result["audit"]["status"], "not_assessable")
            self.assertIsNone(result["series"])
        with self.assertRaises(ValueError):
            sales.adapt_rows([], archive_sha256="wrong", sheet="Online Retail", expected_rows=1)

    def test_streaming_reader_schema_and_required_formulas(self):
        def cell(value, datatype="n"):
            return SimpleNamespace(value=value, data_type=datatype)
        header = [cell(name, "s") for name in sales.HEADER]
        row = self.row(day=datetime(2011, 12, 9))
        values = [cell(row.get(name)) for name in sales.HEADER]
        values[3] = cell("=1+2", "f")
        sheet = SimpleNamespace(title="Online Retail", iter_rows=lambda **kwargs: iter([header, values]))
        class FakeWorkbook:
            sheetnames = ["Online Retail"]
            closed = False
            def __getitem__(self, name): return sheet
            def close(self): self.closed = True
        workbook = FakeWorkbook()
        with patch.dict("sys.modules", {"openpyxl": SimpleNamespace(load_workbook=lambda *args, **kwargs: workbook)}):
            result = sales.read_workbook(Path("synthetic.xlsx"), archive_sha256="a" * 64, expected_rows=1)
        self.assertEqual(result["audit"]["status"], "not_assessable")
        self.assertIsNone(result["series"])
        self.assertTrue(workbook.closed)
        workbook.sheetnames = ["changed"]
        with patch.dict("sys.modules", {"openpyxl": SimpleNamespace(load_workbook=lambda *args, **kwargs: workbook)}):
            with self.assertRaises(ValueError):
                sales.read_workbook(Path("synthetic.xlsx"), archive_sha256="a" * 64)

    def test_accepted_hash_change_cannot_replace_source(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, workbook = [Path(folder) / name for name in ("archive.zip", "book.xlsx")]
            archive.write_bytes(b"synthetic archive"); workbook.write_bytes(b"synthetic workbook")
            manifest = dict(protocol_version=sales.VERSION, archive_url=sales.ARCHIVE_URL,
                            license_url=sales.LICENSE_URL, member=sales.MEMBER)
            for kind, path in (("archive", archive), ("workbook", workbook)):
                manifest[kind + "_bytes"] = path.stat().st_size
                manifest[kind + "_sha256"] = sales.sha256_file(path)
            verify_source(manifest, archive, workbook)
            original = workbook.read_bytes()
            archive.write_bytes(b"altered archive")
            with self.assertRaises(ValueError):
                verify_source(manifest, archive, workbook)
            self.assertEqual(workbook.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
