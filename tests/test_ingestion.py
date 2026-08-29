"""Tests for multi-file, multi-format ingestion (ordino.ingestion).

The central behaviours under test are honesty behaviours: unreadable or
unsupported files must be declined with an explanation, documents must be
classified as CONTEXT (never as analytics input), and shared column names must
surface as *candidate* relationships rather than automatic joins.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordino import ingestion as ing  # noqa: E402


class FakeUpload:
    """Mimics Streamlit's UploadedFile (name + getvalue)."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


SALES_CSV = b"order_id,customer_id,amount\n1,C1,100\n2,C2,250\n3,C1,75\n"
CUSTOMERS_CSV = b"customer_id,name,segment\nC1,Ada,Retail\nC2,Bola,Wholesale\n"


def test_csv_is_ingested_as_data():
    files = ing.ingest_files([FakeUpload("sales.csv", SALES_CSV)])
    assert len(files) == 1
    f = files[0]
    assert f.kind == "data"
    assert f.status == "ready"
    assert f.rows == 3
    assert f.columns == 3


def test_json_array_is_ingested_as_data():
    payload = json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}]).encode()
    files = ing.ingest_files([FakeUpload("records.json", payload)])
    assert files[0].kind == "data"
    assert files[0].rows == 2


def test_tsv_is_ingested_as_data():
    files = ing.ingest_files([FakeUpload("data.tsv", b"a\tb\n1\t2\n3\t4\n")])
    assert files[0].kind == "data"
    assert files[0].rows == 2


def test_txt_is_ingested_as_context_not_data():
    """A document must never become analytics input -- this is the DATA vs
    CONTEXT separation that stops a PDF's "revenue target: 10m" being counted
    as actual revenue.
    """
    files = ing.ingest_files([FakeUpload("notes.txt", b"Our revenue target is 10,000,000 this year.")])
    f = files[0]
    assert f.kind == "context"
    assert f.frame is None
    assert "revenue target" in f.text.lower()
    assert f not in ing.data_files(files)
    assert f in ing.context_files(files)


def test_markdown_is_ingested_as_context():
    files = ing.ingest_files([FakeUpload("brief.md", b"# Goals\n\nImprove margin.")])
    assert files[0].kind == "context"


def test_image_is_declined_with_explanation():
    files = ing.ingest_files([FakeUpload("chart.png", b"\x89PNG\r\n\x1a\n fake")])
    f = files[0]
    assert f.kind == "unsupported"
    assert f.status == "declined"
    assert "OCR" in f.detail


def test_video_is_declined_with_explanation():
    files = ing.ingest_files([FakeUpload("demo.mp4", b"\x00\x00\x00 ftypmp42")])
    f = files[0]
    assert f.kind == "unsupported"
    assert f.status == "declined"
    assert "video" in f.detail.lower()


def test_unknown_extension_is_declined():
    files = ing.ingest_files([FakeUpload("thing.xyz", b"whatever")])
    assert files[0].kind == "unsupported"
    assert files[0].status == "declined"


def test_empty_csv_is_reported_as_error_not_silently_accepted():
    files = ing.ingest_files([FakeUpload("empty.csv", b"a,b\n")])
    f = files[0]
    assert f.kind == "unsupported"
    assert f.status == "error"


def test_malformed_json_is_reported_as_error():
    files = ing.ingest_files([FakeUpload("bad.json", b"{not valid json")])
    assert files[0].status == "error"


def test_multiple_files_are_all_processed():
    files = ing.ingest_files([
        FakeUpload("sales.csv", SALES_CSV),
        FakeUpload("customers.csv", CUSTOMERS_CSV),
        FakeUpload("notes.txt", b"Context here."),
        FakeUpload("logo.png", b"fake"),
    ])
    assert len(files) == 4
    assert len(ing.data_files(files)) == 2
    assert len(ing.context_files(files)) == 1


def test_detect_relationships_finds_shared_identifier():
    files = ing.ingest_files([
        FakeUpload("sales.csv", SALES_CSV),
        FakeUpload("customers.csv", CUSTOMERS_CSV),
    ])
    rels = ing.detect_relationships(files)
    columns = {r["column"] for r in rels}
    assert "customer_id" in columns


def test_detect_relationships_does_not_join_automatically():
    """Relationships are surfaced as candidates only; no combined frame is
    produced. Auto-joining on a coincidental shared column name would
    fabricate figures the user never had.
    """
    files = ing.ingest_files([
        FakeUpload("sales.csv", SALES_CSV),
        FakeUpload("customers.csv", CUSTOMERS_CSV),
    ])
    rels = ing.detect_relationships(files)
    assert all(isinstance(r["note"], str) and "may be related" in r["note"] for r in rels)
    # Each file's frame is untouched and separate.
    frames = ing.data_files(files)
    assert frames[0].frame is not frames[1].frame
    assert len(frames[0].frame.columns) == 3


def test_detect_relationships_ignores_non_identifier_columns():
    a = b"name,amount\nx,1\n"
    b = b"name,cost\ny,2\n"
    files = ing.ingest_files([FakeUpload("a.csv", a), FakeUpload("b.csv", b)])
    rels = ing.detect_relationships(files)
    assert "name" not in {r["column"] for r in rels}


def test_choose_primary_frame_prefers_analysable_table_over_larger_one():
    """Regression: uploading a whole business folder used to select the file
    with the most rows -- e.g. a 130k-row daily inventory snapshot with no
    money column -- over the far smaller sales table that actually answers
    business questions. A money column now outranks raw size.
    """
    big = b"a\n" + b"\n".join(str(i).encode() for i in range(50)) + b"\n"
    files = ing.ingest_files([
        FakeUpload("sales.csv", SALES_CSV),   # small, but has `amount`
        FakeUpload("big.csv", big),            # larger, no money column
    ])
    primary = ing.choose_primary_frame(files)
    assert primary is not None
    assert primary.name == "sales.csv"


def test_choose_primary_frame_prefers_sales_over_inventory_snapshot():
    inventory = (b"snapshot_date,store_id,product_id,opening_stock,closing_stock\n"
                  + b"\n".join(b"2026-01-01,S1,P1,10,9" for _ in range(200)) + b"\n")
    files = ing.ingest_files([
        FakeUpload("inventory_daily.csv", inventory),
        FakeUpload("sales.csv", SALES_CSV),
    ])
    assert ing.choose_primary_frame(files).name == "sales.csv"


def test_choose_primary_frame_falls_back_to_size_when_tied():
    a = b"amount\n1\n2\n"
    b = b"amount\n" + b"\n".join(str(i).encode() for i in range(30)) + b"\n"
    files = ing.ingest_files([FakeUpload("a.csv", a), FakeUpload("b.csv", b)])
    assert ing.choose_primary_frame(files).name == "b.csv"


def test_choose_primary_frame_returns_none_when_no_data_files():
    files = ing.ingest_files([FakeUpload("notes.txt", b"just context")])
    assert ing.choose_primary_frame(files) is None


def test_xlsx_roundtrip_is_ingested_as_data():
    openpyxl = pytest.importorskip("openpyxl")
    buf = io.BytesIO()
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_excel(buf, index=False)
    files = ing.ingest_files([FakeUpload("book.xlsx", buf.getvalue())])
    assert files[0].kind == "data"
    assert files[0].rows == 2


def test_docx_is_ingested_as_context():
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("Our goal is to improve profitability.")
    buf = io.BytesIO()
    document.save(buf)
    files = ing.ingest_files([FakeUpload("plan.docx", buf.getvalue())])
    assert files[0].kind == "context"
    assert "profitability" in files[0].text.lower()
