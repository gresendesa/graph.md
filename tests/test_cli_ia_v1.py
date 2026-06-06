"""
Tests for CLI commands: context (B-016), backlinks (B-017), search (B-018), impact (B-019).
"""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mdgraph.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"
runner = CliRunner()


def _uri(repo_file: str, section_id: str) -> str:
    return str((REPO / repo_file).resolve()) + "#" + section_id


# ---------------------------------------------------------------------------
# B-016: context
# ---------------------------------------------------------------------------

class TestContext:
    def test_context_exits_zero(self):
        result = runner.invoke(app, ["context", _uri("intro.md", "intro"), "--root", str(REPO)])
        assert result.exit_code == 0

    def test_context_json_schema(self):
        result = runner.invoke(app, ["context", _uri("intro.md", "intro"), "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "uri" in data
        assert "metadata" in data
        assert "outgoing" in data
        assert "incoming" in data

    def test_context_json_uri_matches(self):
        uri = _uri("intro.md", "intro")
        result = runner.invoke(app, ["context", uri, "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["uri"] == uri

    def test_context_outgoing_contains_ref(self):
        # intro --ref--> conceito-a
        result = runner.invoke(app, ["context", _uri("intro.md", "intro"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        outgoing_uris = [e["uri"] for e in data["outgoing"]]
        assert any("conceito-a" in u for u in outgoing_uris)

    def test_context_incoming_for_conceito_a(self):
        # intro -> conceito-a, so conceito-a has intro as incoming
        result = runner.invoke(app, ["context", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        incoming_uris = [e["uri"] for e in data["incoming"]]
        assert any("intro" in u for u in incoming_uris)

    def test_context_metadata_contains_id(self):
        result = runner.invoke(app, ["context", _uri("conceitos.md", "conceito-b"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["metadata"].get("id") == "conceito-b"

    def test_context_no_outgoing_for_leaf(self):
        result = runner.invoke(app, ["context", _uri("conceitos.md", "conceito-b"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["outgoing"] == []

    def test_context_uri_not_found_exits_1(self):
        result = runner.invoke(app, ["context", _uri("intro.md", "ghost"), "--root", str(REPO)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# B-017: backlinks
# ---------------------------------------------------------------------------

class TestBacklinks:
    def test_backlinks_exits_zero(self):
        result = runner.invoke(app, ["backlinks", _uri("conceitos.md", "conceito-a"), "--root", str(REPO)])
        assert result.exit_code == 0

    def test_backlinks_json_schema(self):
        result = runner.invoke(app, ["backlinks", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "uri" in data
        assert "backlinks" in data
        assert isinstance(data["backlinks"], list)

    def test_backlinks_returns_intro_for_conceito_a(self):
        result = runner.invoke(app, ["backlinks", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        uris = [e["uri"] for e in data["backlinks"]]
        assert any("intro" in u for u in uris)

    def test_backlinks_empty_for_leaf(self):
        result = runner.invoke(app, ["backlinks", _uri("conceitos.md", "conceito-b"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["backlinks"] == []

    def test_backlinks_uri_not_found_exits_1(self):
        result = runner.invoke(app, ["backlinks", _uri("intro.md", "ghost"), "--root", str(REPO)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# B-018: search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_exact_match(self):
        result = runner.invoke(app, ["search", "id=intro", "--root", str(REPO)])
        assert result.exit_code == 0
        assert "intro" in result.output

    def test_search_exact_no_results(self):
        result = runner.invoke(app, ["search", "id=ghost-section", "--root", str(REPO)])
        assert result.exit_code == 0
        assert "No sections found" in result.output

    def test_search_json_schema(self):
        result = runner.invoke(app, ["search", "id=intro", "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "predicate" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_json_exact_finds_section(self):
        result = runner.invoke(app, ["search", "id=intro", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["predicate"] == "id=intro"
        assert any("intro" in r["uri"] for r in data["results"])

    def test_search_substring_match(self):
        result = runner.invoke(app, ["search", "title~=Conceito", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        # conceito-a and conceito-b both have "Conceito" in title
        assert len(data["results"]) >= 2

    def test_search_predicate_in_json_output(self):
        result = runner.invoke(app, ["search", "id=conceito-a", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["predicate"] == "id=conceito-a"

    def test_search_results_have_metadata(self):
        result = runner.invoke(app, ["search", "id=conceito-a", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert len(data["results"]) == 1
        assert "metadata" in data["results"][0]


# ---------------------------------------------------------------------------
# B-019: impact
# ---------------------------------------------------------------------------

class TestImpact:
    def test_impact_exits_zero(self):
        result = runner.invoke(app, ["impact", _uri("conceitos.md", "conceito-a"), "--root", str(REPO)])
        assert result.exit_code == 0

    def test_impact_json_schema(self):
        result = runner.invoke(app, ["impact", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "uri" in data
        assert "direct" in data
        assert "indirect" in data

    def test_impact_direct_contains_intro(self):
        # intro refs conceito-a, so conceito-a's direct impact = intro
        result = runner.invoke(app, ["impact", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        direct_uris = [e["uri"] for e in data["direct"]]
        assert any("intro" in u for u in direct_uris)

    def test_impact_no_dependents_for_root(self):
        # intro has no incoming edges
        result = runner.invoke(app, ["impact", _uri("intro.md", "intro"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["direct"] == []
        assert data["indirect"] == []

    def test_impact_uri_not_found_exits_1(self):
        result = runner.invoke(app, ["impact", _uri("intro.md", "ghost"), "--root", str(REPO)])
        assert result.exit_code == 1

    def test_impact_detalhe_propagates_to_intro(self):
        # detalhe is included by conceito-a, which is ref'd by intro
        # so detalhe's direct = conceito-a, indirect = intro
        result = runner.invoke(app, ["impact", _uri("sub/detalhe.md", "detalhe"), "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        direct_uris = [e["uri"] for e in data["direct"]]
        indirect_uris = [e["uri"] for e in data["indirect"]]
        assert any("conceito-a" in u for u in direct_uris)
        assert any("intro" in u for u in indirect_uris)
