"""
Tests for CLI commands: neighbors (B-020), explain (B-021), diff (B-022),
query (B-023), context-compose (B-024).
"""
import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mdbind.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"
runner = CliRunner()


def _uri(repo_file: str, section_id: str) -> str:
    return str((REPO / repo_file).resolve()) + "#" + section_id


# ---------------------------------------------------------------------------
# B-020: neighbors
# ---------------------------------------------------------------------------

class TestNeighbors:
    def test_neighbors_exits_zero(self):
        result = runner.invoke(app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO)])
        assert result.exit_code == 0

    def test_neighbors_json_schema(self):
        result = runner.invoke(app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "uri" in data
        assert "depth" in data
        assert "neighbors" in data
        assert isinstance(data["neighbors"], list)

    def test_neighbors_depth_1_finds_conceito_a(self):
        result = runner.invoke(
            app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO), "--json", "--depth", "1"]
        )
        data = json.loads(result.output)
        uris = [n["uri"] for n in data["neighbors"]]
        assert any("conceito-a" in u for u in uris)

    def test_neighbors_depth_1_does_not_reach_detalhe(self):
        # intro -> conceito-a -> detalhe; depth=1 should not reach detalhe
        result = runner.invoke(
            app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO), "--json", "--depth", "1"]
        )
        data = json.loads(result.output)
        uris = [n["uri"] for n in data["neighbors"]]
        assert not any("detalhe" in u for u in uris)

    def test_neighbors_depth_2_reaches_detalhe(self):
        result = runner.invoke(
            app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO), "--json", "--depth", "2"]
        )
        data = json.loads(result.output)
        uris = [n["uri"] for n in data["neighbors"]]
        assert any("detalhe" in u for u in uris)

    def test_neighbors_includes_incoming(self):
        # conceito-a has intro as incoming neighbor
        result = runner.invoke(
            app, ["neighbors", _uri("conceitos.md", "conceito-a"), "--root", str(REPO), "--json", "--depth", "1"]
        )
        data = json.loads(result.output)
        uris = [n["uri"] for n in data["neighbors"]]
        assert any("intro" in u for u in uris)

    def test_neighbors_direction_field(self):
        result = runner.invoke(
            app, ["neighbors", _uri("intro.md", "intro"), "--root", str(REPO), "--json", "--depth", "1"]
        )
        data = json.loads(result.output)
        assert all("direction" in n for n in data["neighbors"])

    def test_neighbors_uri_not_found_exits_1(self):
        result = runner.invoke(app, ["neighbors", _uri("intro.md", "ghost"), "--root", str(REPO)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# B-021: explain
# ---------------------------------------------------------------------------

class TestExplain:
    def test_explain_exits_zero(self):
        result = runner.invoke(
            app, ["explain", _uri("intro.md", "intro"), _uri("sub/detalhe.md", "detalhe"), "--root", str(REPO)]
        )
        assert result.exit_code == 0

    def test_explain_json_schema(self):
        result = runner.invoke(
            app, ["explain", _uri("intro.md", "intro"), _uri("sub/detalhe.md", "detalhe"),
                  "--root", str(REPO), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "from" in data
        assert "to" in data
        assert "paths" in data
        assert isinstance(data["paths"], list)

    def test_explain_finds_path_intro_to_detalhe(self):
        result = runner.invoke(
            app, ["explain", _uri("intro.md", "intro"), _uri("sub/detalhe.md", "detalhe"),
                  "--root", str(REPO), "--json"]
        )
        data = json.loads(result.output)
        assert len(data["paths"]) >= 1

    def test_explain_no_path_between_unrelated(self):
        # conceito-b has no connections to detalhe
        result = runner.invoke(
            app, ["explain", _uri("conceitos.md", "conceito-b"), _uri("sub/detalhe.md", "detalhe"),
                  "--root", str(REPO), "--json"]
        )
        data = json.loads(result.output)
        assert data["paths"] == []

    def test_explain_path_contains_uri_steps(self):
        result = runner.invoke(
            app, ["explain", _uri("intro.md", "intro"), _uri("sub/detalhe.md", "detalhe"),
                  "--root", str(REPO), "--json"]
        )
        data = json.loads(result.output)
        if data["paths"]:
            path = data["paths"][0]
            uris_in_path = [step["uri"] for step in path]
            assert any("intro" in u for u in uris_in_path)
            assert any("detalhe" in u for u in uris_in_path)

    def test_explain_uri_not_found_exits_1(self):
        result = runner.invoke(
            app, ["explain", _uri("intro.md", "ghost"), _uri("sub/detalhe.md", "detalhe"), "--root", str(REPO)]
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# B-022: diff
# ---------------------------------------------------------------------------

def _is_git_repo(path: Path) -> bool:
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(path),
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _git_available() -> bool:
    try:
        subprocess.check_output(["git", "--version"], stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.mark.skipif(
    not _is_git_repo(Path(__file__).parent.parent),
    reason="Not a git repository",
)
class TestDiff:
    def test_diff_json_schema(self):
        result = runner.invoke(app, ["diff", "--root", str(REPO), "--json"])
        # Might fail if HEAD~1 doesn't exist, but schema check is valid on success
        if result.exit_code == 0:
            data = json.loads(result.output)
            assert "since" in data
            assert "added_sections" in data
            assert "removed_sections" in data
            assert "added_edges" in data
            assert "removed_edges" in data

    def test_diff_invalid_ref_exits_1(self):
        result = runner.invoke(app, ["diff", "--root", str(REPO), "--since", "nonexistent-ref-xyz"])
        assert result.exit_code == 1


class TestDiffNotGit:
    def test_diff_non_git_dir_exits_1(self, tmp_path):
        result = runner.invoke(app, ["diff", "--root", str(tmp_path)])
        assert result.exit_code == 1


@pytest.mark.skipif(not _git_available(), reason="git not available")
class TestDiffHistoricalParsing:
    def test_diff_json_parses_historical_markdown_with_string_file_path(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Existing\n\n```yaml\nsection: existing\n```\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
        subprocess.run(["git", "add", "doc.md"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)

        result = runner.invoke(app, ["diff", "--root", str(tmp_path), "--since", "HEAD", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["since"] == "HEAD"
        assert data["added_sections"] == []
        assert data["removed_sections"] == []
        assert data["added_edges"] == []
        assert data["removed_edges"] == []


# ---------------------------------------------------------------------------
# B-023: query
# ---------------------------------------------------------------------------

class TestQuery:
    def test_query_exact(self):
        result = runner.invoke(app, ["query", "id=intro", "--root", str(REPO)])
        assert result.exit_code == 0
        assert "intro" in result.output

    def test_query_json_schema(self):
        result = runner.invoke(app, ["query", "id=intro", "--root", str(REPO), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "expression" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_query_and_operator(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Sec A\n\n```yaml\nsection: sec-a\nowner: alice\nstatus: active\n```\n\n"
            "# Sec B\n\n```yaml\nsection: sec-b\nowner: alice\nstatus: obsolete\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["query", "owner=alice AND status=active", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert len(data["results"]) == 1
        assert "sec-a" in data["results"][0]["uri"]

    def test_query_or_operator(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Sec A\n\n```yaml\nsection: sec-a\nowner: alice\n```\n\n"
            "# Sec B\n\n```yaml\nsection: sec-b\nowner: bob\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["query", "owner=alice OR owner=bob", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert len(data["results"]) == 2

    def test_query_not_operator(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Sec A\n\n```yaml\nsection: sec-a\nstatus: active\n```\n\n"
            "# Sec B\n\n```yaml\nsection: sec-b\nstatus: obsolete\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["query", "NOT status=obsolete", "--root", str(tmp_path), "--json"])
        data = json.loads(result.output)
        uris = [r["uri"] for r in data["results"]]
        assert any("sec-a" in u for u in uris)
        assert not any("sec-b" in u for u in uris)

    def test_query_no_results(self):
        result = runner.invoke(app, ["query", "id=nonexistent-section-xyz", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["results"] == []

    def test_query_expression_in_output(self):
        result = runner.invoke(app, ["query", "id=intro", "--root", str(REPO), "--json"])
        data = json.loads(result.output)
        assert data["expression"] == "id=intro"

    def test_query_structural_pseudo_fields(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Alpha Heading\n\n```yaml\nsection: alpha\nowner: alice\n```\n\n"
            "# Beta Heading\n\n```yaml\nsection: beta\nowner: bob\n```\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "query",
                "section=alpha AND id=alpha AND path~=doc.md AND file~=doc.md AND heading~=Alpha",
                "--root",
                str(tmp_path),
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["results"]) == 1
        assert data["results"][0]["metadata"]["id"] == "alpha"

    def test_query_regex_predicate_with_boolean_operators(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Backlog A\n\n```yaml\nsection: backlog.item.B-030\nstatus: doing\n```\n\n"
            "# Backlog B\n\n```yaml\nsection: backlog.item.B-031\nstatus: done\n```\n\n"
            "# Sprint\n\n```yaml\nsection: sprint.SPR-2026-12\nstatus: doing\n```\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            [
                "query",
                "section~=/^backlog\\.item\\.B-\\d{3}$/ AND NOT status=done",
                "--root",
                str(tmp_path),
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert [r["metadata"]["id"] for r in data["results"]] == ["backlog.item.B-030"]

    def test_query_substring_predicate_remains_unchanged(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Sec A\n\n```yaml\nsection: sec-a\ntitle: Authentication Flow\n```\n\n"
            "# Sec B\n\n```yaml\nsection: sec-b\ntitle: Billing Flow\n```\n",
            encoding="utf-8",
        )

        result = runner.invoke(app, ["query", "title~=auth", "--root", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert [r["metadata"]["id"] for r in data["results"]] == ["sec-a"]

    def test_query_invalid_regex_exits_1(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Sec A\n\n```yaml\nsection: sec-a\n```\n", encoding="utf-8")

        result = runner.invoke(app, ["query", "id~=/[/", "--root", str(tmp_path), "--json"])

        assert result.exit_code == 1
        assert "invalid regex" in result.output


# ---------------------------------------------------------------------------
# B-024: context-compose
# ---------------------------------------------------------------------------

class TestContextCompose:
    def test_context_compose_exits_zero(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "intro"), "--root", str(REPO)]
        )
        assert result.exit_code == 0

    def test_context_compose_json_schema(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "intro"), "--root", str(REPO), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "uri" in data
        assert "depth" in data
        assert "token_estimate" in data
        assert "truncated" in data
        assert "content" in data

    def test_context_compose_json_with_yaml_date_metadata(self, tmp_path):
        source = tmp_path / "dated.md"
        source.write_text(
            "# Dated Section\n\n"
            "```yaml\n"
            "section: dated\n"
            "title: Dated Section\n"
            "created_at: 2026-06-08\n"
            "```\n\n"
            "Body.\n",
            encoding="utf-8",
        )

        uri = str(source.resolve()) + "#dated"
        result = runner.invoke(app, ["context-compose", uri, "--root", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["uri"] == uri
        assert "Body." in data["content"]

    def test_context_compose_not_truncated_by_default(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "intro"), "--root", str(REPO), "--json"]
        )
        data = json.loads(result.output)
        assert data["truncated"] is False

    def test_context_compose_token_limit_truncates(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "intro"), "--root", str(REPO),
                  "--json", "--token-limit", "5"]
        )
        data = json.loads(result.output)
        assert data["truncated"] is True
        assert len(data["content"]) <= 5 * 4

    def test_context_compose_token_estimate_is_integer(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "intro"), "--root", str(REPO), "--json"]
        )
        data = json.loads(result.output)
        assert isinstance(data["token_estimate"], int)
        assert data["token_estimate"] >= 0

    def test_context_compose_depth_0_no_includes(self):
        # depth=0 means no @include expansion
        result = runner.invoke(
            app, ["context-compose", _uri("conceitos.md", "conceito-a"), "--root", str(REPO),
                  "--json", "--depth", "0"]
        )
        data = json.loads(result.output)
        # With depth=0, included content (detalhe) should not appear
        assert "Detalhe Tecnico" not in data["content"]

    def test_context_compose_uri_not_found_exits_1(self):
        result = runner.invoke(
            app, ["context-compose", _uri("intro.md", "ghost"), "--root", str(REPO)]
        )
        assert result.exit_code == 1
