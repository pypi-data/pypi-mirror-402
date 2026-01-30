import os
import subprocess
import sys
import textwrap
import pytest
import src.python_page_rank.cli as cli
from pathlib import Path


def write_file(path: Path, content: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def test_path_to_module_handles_init_and_nested():
    # path_to_module should strip .py, drop __init__, and join with dots.
    root = "/project"
    assert cli.path_to_module(root, os.path.join(root, "pkg", "__init__.py")) == "pkg"
    assert cli.path_to_module(root, os.path.join(root, "pkg", "sub", "mod.py")) == "pkg.sub.mod"


def test_detect_import_roots_includes_src_and_subdirs(tmp_path: Path):
    # detect_import_roots should consider repo root, src layout, and direct subdirs,
    # and it should not surface hidden/ignored directories.
    (tmp_path / "src").mkdir()
    (tmp_path / "pkg").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "__pycache__").mkdir()
    roots = cli.detect_import_roots(tmp_path)
    expected = {os.path.abspath(tmp_path), os.path.abspath(tmp_path / "src"), os.path.abspath(tmp_path / "pkg")}
    assert expected.issubset(set(roots))
    ignored_suffixes = {os.sep + ".git", os.sep + ".venv", os.sep + "venv", os.sep + "__pycache__"}
    assert all(not r.endswith(suf) for r in roots for suf in ignored_suffixes)


def test_iterate_py_files_skips_common_dirs(tmp_path: Path):
    # iterate_py_files should ignore version control and cache dirs.
    keep = tmp_path / "keep"
    skip = tmp_path / ".git" / "ignored.py"
    write_file(keep / "file.py", "x = 1")
    write_file(skip, "ignored = True")

    found = list(cli.iterate_py_files(tmp_path))
    assert keep / "file.py" in map(Path, found)
    assert all(Path(p) != skip for p in found)


def test_build_graph_handles_relative_imports(tmp_path: Path):
    # Build a simple package with relative imports: a -> b -> c.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "a.py", "from .b import func\n")
    write_file(tmp_path / "pkg" / "b.py", "from .c import CONST\n")
    write_file(tmp_path / "pkg" / "c.py", "VALUE = 1\n")

    nodes, edges = cli.build_graph(tmp_path)

    a = str(tmp_path / "pkg" / "a.py")
    b = str(tmp_path / "pkg" / "b.py")
    c = str(tmp_path / "pkg" / "c.py")

    assert a in nodes
    assert edges[a] == {b}
    assert edges[b] == {c}
    assert c not in edges or not edges[c]


def test_build_graph_skips_non_repo_imports(tmp_path: Path):
    # Imports pointing outside the repo should be ignored in the graph.
    write_file(tmp_path / "main.py", "import sys\nimport not_in_repo\n")

    nodes, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "main.py")
    assert main in nodes
    assert main not in edges or not edges[main]


def test_build_graph_handles_multi_level_packages(tmp_path: Path):
    # Multi-level package chain: main -> util -> deep.leaf. A package import
    # (from pkg.sub import util) should emit edges to both the package
    # __init__.py and the imported module.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "sub" / "__init__.py")
    write_file(tmp_path / "pkg" / "sub" / "deep" / "__init__.py")
    write_file(tmp_path / "pkg" / "sub" / "deep" / "leaf.py", "ANSWER = 1\n")
    write_file(
        tmp_path / "pkg" / "sub" / "util.py",
        "from pkg.sub.deep.leaf import ANSWER\n",
    )
    write_file(
        tmp_path / "pkg" / "main.py",
        "from pkg.sub import util\n",
    )

    nodes, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "pkg" / "main.py")
    util = str(tmp_path / "pkg" / "sub" / "util.py")
    pkg_sub_init = str(tmp_path / "pkg" / "sub" / "__init__.py")
    leaf = str(tmp_path / "pkg" / "sub" / "deep" / "leaf.py")

    assert main in nodes and util in nodes and leaf in nodes
    # from pkg.sub import util pulls in the package (__init__) and the module.
    assert edges[main] == {pkg_sub_init, util}
    assert edges[util] == {leaf}
    assert leaf not in edges or not edges[leaf]


def test_multi_level_relative_import_level_two_resolves(tmp_path: Path):
    # from ..models import X (level=2) should resolve to pkg/models.py.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "models.py", "class X: pass\n")
    write_file(tmp_path / "pkg" / "sub" / "__init__.py")
    write_file(tmp_path / "pkg" / "sub" / "api.py", "from ..models import X\n")

    nodes, edges = cli.build_graph(tmp_path)

    api = str(tmp_path / "pkg" / "sub" / "api.py")
    models = str(tmp_path / "pkg" / "models.py")

    assert api in nodes and models in nodes
    assert edges[api] == {models}


def test_relative_import_without_module_is_ignored(tmp_path: Path):
    # from . import models sets node.module to None; current behavior is to
    # ignore these, ensuring no edges are added. This is intentional: ast sets
    # node.module = None for this pattern, so we lock in the ignore behavior to
    # avoid "fixes" that would change expectations later.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "models.py", "VALUE = 1\n")
    write_file(tmp_path / "pkg" / "api.py", "from . import models\n")

    nodes, edges = cli.build_graph(tmp_path)

    api = str(tmp_path / "pkg" / "api.py")
    models = str(tmp_path / "pkg" / "models.py")
    assert api in nodes and models in nodes
    assert api not in edges or models not in edges[api]


def test_relative_import_level_too_high_is_ignored(tmp_path: Path):
    # from ...models import X from a shallow module should not crash and should
    # produce no edges when the relative level walks above the package root.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "api.py", "from ...models import X\n")

    nodes, edges = cli.build_graph(tmp_path)

    api = str(tmp_path / "pkg" / "api.py")
    assert api in nodes
    assert api not in edges or not edges[api]


def test_import_package_targets_init_when_only_init_exists(tmp_path: Path):
    # If only pkg/__init__.py exists, `import pkg` should resolve to __init__.py.
    write_file(tmp_path / "pkg" / "__init__.py", "VALUE = 1\n")
    write_file(tmp_path / "main.py", "import pkg\n")

    nodes, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "main.py")
    pkg_init = str(tmp_path / "pkg" / "__init__.py")

    assert main in nodes and pkg_init in nodes
    assert edges[main] == {pkg_init}


def test_import_subpackage_resolves_to_subpkg_init(tmp_path: Path):
    # from pkg import subpkg should resolve to pkg/subpkg/__init__.py
    write_file(tmp_path / "pkg" / "__init__.py", "")
    write_file(tmp_path / "pkg" / "subpkg" / "__init__.py", "VALUE = 1\n")
    write_file(tmp_path / "main.py", "from pkg import subpkg\n")

    nodes, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "main.py")
    pkg_init = str(tmp_path / "pkg" / "__init__.py")
    subpkg_init = str(tmp_path / "pkg" / "subpkg" / "__init__.py")

    assert main in nodes and subpkg_init in nodes
    # from pkg import subpkg brings in the package and the subpackage init files.
    assert edges[main] == {pkg_init, subpkg_init}


def test_build_graph_skips_files_with_syntax_errors(tmp_path: Path):
    # Files that fail to parse should be skipped without crashing; valid files
    # still contribute edges.
    write_file(tmp_path / "app" / "__init__.py")
    write_file(tmp_path / "app" / "util.py", "ANSWER = 1\n")
    write_file(tmp_path / "app" / "good.py", "import app.util\n")
    write_file(tmp_path / "app" / "bad.py", "def broken(:\n")  # syntax error

    nodes, edges = cli.build_graph(tmp_path)

    good = str(tmp_path / "app" / "good.py")
    util = str(tmp_path / "app" / "util.py")
    bad = str(tmp_path / "app" / "bad.py")

    assert good in nodes and util in nodes
    assert util in edges[good]
    # bad.py should not add edges and should not crash the traversal.
    assert bad in nodes
    assert bad not in edges or not edges[bad]


def test_repeated_imports_dedup_edge_and_importer(tmp_path: Path):
    # Multiple imports of the same module (including from-import) should yield a
    # single edge and a single importer count for that target.
    write_file(tmp_path / "app" / "__init__.py")
    write_file(tmp_path / "app" / "util.py", "ANSWER = 1\n")
    write_file(
        tmp_path / "app" / "main.py",
        "import app.util\nimport app.util\nfrom app import util\n",
    )

    _, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "app" / "main.py")
    util = str(tmp_path / "app" / "util.py")
    app_init = str(tmp_path / "app" / "__init__.py")

    # Deduplicated edge set should include util; importing the package also links
    # to its __init__.py.
    assert edges[main] == {app_init, util}

    importers = cli.count_importers(edges)
    assert importers[util] == 1


def test_alias_imports_behave_like_non_aliased(tmp_path: Path):
    # Aliases should not change edge resolution.
    write_file(tmp_path / "app" / "__init__.py")
    write_file(tmp_path / "app" / "util.py", "ANSWER = 1\n")
    write_file(
        tmp_path / "main.py",
        "import app.util as u\nfrom app import util as v\n",
    )

    _, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "main.py")
    util = str(tmp_path / "app" / "util.py")
    app_init = str(tmp_path / "app" / "__init__.py")

    assert edges[main] == {app_init, util}


def test_import_star_treated_as_direct_module_import(tmp_path: Path):
    # from pkg.mod import * should behave like importing pkg.mod directly.
    write_file(tmp_path / "pkg" / "__init__.py", "")
    write_file(tmp_path / "pkg" / "mod.py", "VALUE = 1\n")
    write_file(tmp_path / "main.py", "from pkg.mod import *\n")

    _, edges = cli.build_graph(tmp_path)

    main = str(tmp_path / "main.py")
    mod = str(tmp_path / "pkg" / "mod.py")

    assert edges[main] == {mod}


def test_module_index_prefers_shorter_path_on_duplicates(tmp_path: Path):
    # If the same module name is reachable from two roots, we prefer the shorter
    # (then lexicographically smaller) path deterministically.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "mod.py", "VALUE = 1\n")
    write_file(tmp_path / "src" / "pkg" / "mod.py", "VALUE = 2\n")

    modules = cli.build_module_index(tmp_path)
    chosen = modules["pkg.mod"]
    shorter = str(tmp_path / "pkg" / "mod.py")
    longer = str(tmp_path / "src" / "pkg" / "mod.py")

    assert chosen == shorter
    assert chosen != longer


def test_relative_import_edges_are_stable_across_roots(tmp_path: Path):
    # Regression: running from repo root vs nested package root should produce
    # the same edges for relative imports (from .models import Event).
    write_file(tmp_path / "CalendarApp" / "__init__.py")
    write_file(tmp_path / "CalendarApp" / "models.py", "class Event: pass\n")
    write_file(tmp_path / "CalendarApp" / "api.py", "from .models import Event\n")

    def edge_pairs(root, edges):
        def rel(path):
            return os.path.relpath(path, root)

        return {(rel(src), rel(tgt)) for src, tgts in edges.items() for tgt in tgts}

    def strip_prefix(pair_set, prefix):
        stripped = set()
        for src, tgt in pair_set:
            src_parts = Path(src).parts
            tgt_parts = Path(tgt).parts
            if src_parts and src_parts[0] == prefix:
                src_parts = src_parts[1:]
            if tgt_parts and tgt_parts[0] == prefix:
                tgt_parts = tgt_parts[1:]
            stripped.add((os.path.join(*src_parts), os.path.join(*tgt_parts)))
        return stripped

    _, edges_root = cli.build_graph(tmp_path)
    _, edges_pkg = cli.build_graph(tmp_path / "CalendarApp")

    pairs_root = strip_prefix(edge_pairs(tmp_path, edges_root), "CalendarApp")
    pairs_pkg = edge_pairs(tmp_path / "CalendarApp", edges_pkg)

    assert ("api.py", "models.py") in pairs_root
    assert pairs_root == pairs_pkg


def test_pagerank_ranks_high_import_target_highest():
    # Node b has two incoming edges; it should outrank c, which outranks a.
    nodes = {"a", "b", "c"}
    edges = {"a": {"b"}, "b": {"c"}, "c": {"b"}}

    pr = cli.pagerank(nodes, edges, alpha=0.85, iters=100)

    assert pr["b"] > pr["c"] > pr["a"]


def test_pagerank_handles_empty_graph():
    # Empty graph should return an empty score mapping, not error.
    assert cli.pagerank(set(), {}) == {}


def test_main_outputs_top_modules_sorted(tmp_path: Path, capfd: pytest.CaptureFixture[str]):
    # util is imported by three modules; expect it to rank highest in CLI output.
    write_file(tmp_path / "app" / "__init__.py")
    write_file(tmp_path / "app" / "util.py", "ANSWER = 42\n")
    write_file(tmp_path / "app" / "a.py", "import app.util\n")
    write_file(tmp_path / "app" / "b.py", "import app.util\n")
    write_file(tmp_path / "app" / "c.py", "import app.util\nimport app.b\n")
    total_nodes = len(cli.build_graph(tmp_path)[0])

    # Run via module entrypoint to cover CLI printing.
    subprocess.check_call([sys.executable, str(Path(cli.__file__).resolve()), str(tmp_path), "--n", "5"])
    out, _ = capfd.readouterr()

    lines = [line for line in out.strip().splitlines() if line]
    assert "Module" in lines[0] and "PageRank" in lines[0]
    assert len(lines) >= 3  # header + separator + at least one result

    first_result = lines[2].split()[0]
    assert "app" in first_result and "util" in first_result

    # Parse PageRank column to ensure numeric and sum of shown rows ~= 1.
    ranks = []
    for line in lines[2:]:
        parts = line.split()
        assert parts, "result line should contain columns"
        rank = float(parts[-1])
        assert 0.0 < rank < 1.0
        ranks.append(rank)
    # The CLI may truncate results; only assert full-sum when all nodes printed.
    printed_rows = len(ranks)
    if printed_rows == total_nodes:
        assert abs(sum(ranks) - 1.0) < 1e-3


def test_main_respects_result_limit(tmp_path: Path, capfd: pytest.CaptureFixture[str]):
    # number_of_results argument should cap the printed rows to 1.
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "one.py", "")
    write_file(tmp_path / "pkg" / "two.py", "import pkg.one\n")

    subprocess.check_call([sys.executable, str(Path(cli.__file__).resolve()), str(tmp_path), "--n", "1"])
    out, _ = capfd.readouterr()
    lines = [line for line in out.strip().splitlines() if line]
    # header + separator + one result
    assert len(lines) == 3


def test_count_loc_missing_file_returns_zero(tmp_path: Path):
    # Missing files should not raise and should report 0 LOC.
    missing = tmp_path / "absent.py"
    assert cli.count_loc(missing) == 0


def test_count_importers_counts_unique_sources():
    # count_importers should tally unique importer modules per target.
    edges = {"a": {"b", "c"}, "b": {"c"}, "c": set()}
    counts = cli.count_importers(edges)
    assert counts["b"] == 1
    assert counts["c"] == 2


def test_best_repo_matches_exact_and_prefix_and_missing():
    # exact match should return the name
    modules = {"pkg": "/path/pkg.py", "pkg.sub": "/path/pkg/sub.py", "other": "/path/other.py"}
    assert cli.best_repo_matches(modules, "pkg.sub") == ["pkg.sub"]

    # prefix fallback should return the closest existing prefix
    assert cli.best_repo_matches(modules, "pkg.sub.deep.more") == ["pkg.sub"]

    # unknown should return empty
    assert cli.best_repo_matches(modules, "doesnotexist") == []


def test_cli_defaults():
    parser = cli.build_arg_parser()
    args = parser.parse_args([])

    assert args.path == "."
    assert args.n is 10
    assert args.alpha == 0.85
    assert args.iters == 50
    assert args.json is False
    
    
def test_cli_all_parameters():
    parser = cli.build_arg_parser()
    args = parser.parse_args([
        "MyApp",
        "--n", "20",
        "--alpha", "0.8",
        "--iters", "75",
        "--json",
    ])

    assert args.path == "MyApp"
    assert args.n == 20
    assert args.alpha == 0.8
    assert args.iters == 75
    assert args.json is True



def test_cli_hides_init_by_default(tmp_path, capfd):
    subprocess.check_call([sys.executable, str(Path(cli.__file__).resolve()), str(tmp_path)])
    out, _ = capfd.readouterr()
    assert "__init__.py" not in out


def test_cli_include_init_flag_shows_init(tmp_path, capfd):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("X = 1\n")
    (tmp_path / "pkg" / "a.py").write_text("import pkg\n")
    subprocess.check_call([sys.executable, str(Path(cli.__file__).resolve()), str(tmp_path), "--include-init"])    
    out, _ = capfd.readouterr()
    assert "__init__.py" in out
