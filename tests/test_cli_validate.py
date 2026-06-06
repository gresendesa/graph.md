"""
Tests for the CLI 'mdgraph validate' command (B-015).
"""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mdbind.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


def _uri(filename: str, section_id: str) -> str:
    return str((FIXTURES / filename).resolve()) + "#" + section_id


class TestValidateClean:
    def test_validate_clean_repo_exits_zero(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\nContent.\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path)])
        assert result.exit_code == 0
        assert "no issues found" in result.output.lower() or "OK" in result.output

    def test_validate_clean_repo_json(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\nContent.\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["summary"]["errors"] == 0
        assert data["summary"]["warnings"] == 0
        assert data["summary"]["total_sections"] == 1

    def test_validate_json_schema_keys(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# S\n\n```yaml\nsection: s\n```\n", encoding="utf-8")
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert "errors" in data
        assert "warnings" in data
        assert "summary" in data
        assert "total_sections" in data["summary"]
        assert "total_edges" in data["summary"]


class TestValidateBrokenRef:
    def test_broken_include_detected(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            "[@include: label](doc.md#nonexistent)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path)])
        assert result.exit_code == 1

    def test_broken_include_in_json(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            "[@include: label](doc.md#nonexistent)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["summary"]["errors"] >= 1
        types = [e["type"] for e in data["errors"]]
        assert "broken_include" in types

    def test_broken_ref_detected(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            "[@ref: label](doc.md#ghost)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        types = [e["type"] for e in data["errors"]]
        assert "broken_ref" in types


class TestValidateCycle:
    def test_include_cycle_detected(self, tmp_path):
        md = tmp_path / "doc.md"
        # A includes B, B includes A
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            f"[@include: b](doc.md#b)\n\n"
            "# Section B\n\n```yaml\nsection: b\n```\n\n"
            f"[@include: a](doc.md#a)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        types = [e["type"] for e in data["errors"]]
        assert "cycle" in types

    def test_self_cycle_detected(self, tmp_path):
        md = tmp_path / "doc.md"
        abs_path = md.resolve()
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            f"[@include: self]({abs_path}#a)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        types = [e["type"] for e in data["errors"]]
        assert "cycle" in types or data["summary"]["errors"] >= 1


class TestValidateSummary:
    def test_summary_counts_edges(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            "# Section B\n\n```yaml\nsection: b\n```\n\n"
            f"[@ref: a](doc.md#a)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert data["summary"]["total_sections"] == 2
        assert data["summary"]["total_edges"] == 1

    def test_multiple_errors_reported(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Section A\n\n```yaml\nsection: a\n```\n\n"
            "[@include: x](doc.md#x)\n"
            "[@ref: y](doc.md#y)\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert data["summary"]["errors"] >= 2
