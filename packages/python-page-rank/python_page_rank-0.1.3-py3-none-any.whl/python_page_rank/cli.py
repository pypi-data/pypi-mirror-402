#!/usr/bin/env python3
import argparse
import ast
import json
import os
import sys
from collections import defaultdict

# directories to skip when scanning the repo
IGNORED_DIRS = {".idea", ".git", ".venv", "venv",
                "__pycache__", "node_modules", "dist", "build"}


def iterate_py_files(root: str):
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname for dirname in dirnames if dirname not in IGNORED_DIRS]
        for filename in filenames:
            if filename.endswith(".py"):
                yield os.path.abspath(os.path.join(dirpath, filename))


def path_to_module(root: str, path: str):
    relative_path = os.path.relpath(path, root)
    if relative_path.endswith(".py"):
        relative_path = relative_path[:-3]
    parts = relative_path.split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([part for part in parts if part])


def detect_import_roots(root: str):
    roots = {os.path.abspath(root)}

    # common "src" layout
    src = os.path.join(root, "src")
    if os.path.isdir(src):
        roots.add(os.path.abspath(src))

    # also consider each top-level directory as a potential package root
    # (covers cases like CalendarApp/ being the import root)
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isdir(p) and not name.startswith(".") and name not in IGNORED_DIRS:
            roots.add(os.path.abspath(p))

    return sorted(roots)


def _prefer_path(existing: str, candidate: str):
    """Choose a deterministic path: prefer shorter, then lexicographically smaller."""
    if existing is None:
        return candidate
    if len(candidate) < len(existing):
        return candidate
    if len(candidate) == len(existing) and candidate < existing:
        return candidate
    return existing


def build_module_index(root: str):
    # map module name -> file path (try multiple plausible import roots)
    modules_to_files = {}

    for import_root in detect_import_roots(root):
        for py_file in iterate_py_files(import_root):
            module = path_to_module(import_root, py_file)
            if not module:
                continue
            existing = modules_to_files.get(module)
            modules_to_files[module] = _prefer_path(existing, py_file)

    return modules_to_files


def resolve_import(modules_to_files, current_module: str, node):
    # returns list of module names that exist in repo (best-effort)
    out = []
    if isinstance(node, ast.Import):
        for node_names in node.names:
            name = node_names.name
            # keep only imports we can map to repo modules (prefix match)
            out.extend(best_repo_matches(modules_to_files, name))
    elif isinstance(node, ast.ImportFrom):
        if node.module is None:
            return out
        base = node.module
        # handle relative imports: from .foo import bar
        if node.level and current_module:
            current_parts = current_module.split(".")
            up = max(0, len(current_parts) - node.level)
            base = ".".join(current_parts[:up] + base.split("."))
        out.extend(best_repo_matches(modules_to_files, base))
        # also try base + imported name (from pkg import sub)
        for node_names in node.names:
            out.extend(best_repo_matches(
                modules_to_files, base + "." + node_names.name))
    return out


def best_repo_matches(modules_to_files, name: str):
    # If exact module exists, return it.
    if name in modules_to_files:
        return [name]
    # If importing a package, accept the closest existing prefix.
    parts = name.split(".")
    for k in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:k])
        if prefix in modules_to_files:
            return [prefix]
    return []


def build_graph(root: str):
    modules_to_files = build_module_index(root)
    files_to_modules = {v: k for k, v in modules_to_files.items()}

    edges = defaultdict(set)  # A -> {B}
    nodes = set()

    for py_file in iterate_py_files(root):
        current_module = files_to_modules.get(py_file, "")
        nodes.add(py_file)
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                src = f.read()
            tree = ast.parse(src, filename=py_file)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for imported_module in resolve_import(modules_to_files, current_module, node):
                    target_file = modules_to_files.get(imported_module)
                    if target_file and target_file != py_file:
                        edges[py_file].add(target_file)
                        nodes.add(target_file)

    return nodes, edges


def pagerank(nodes, edges, alpha=0.85, iters=50):
    nodes = list(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    number_of_nodes = len(nodes)
    if number_of_nodes == 0:
        return {}

    outlinks = [set() for _ in range(number_of_nodes)]
    inlinks = [[] for _ in range(number_of_nodes)]
    for source, targets in edges.items():
        if source not in idx:
            continue
        i = idx[source]
        for target in targets:
            if target in idx:
                j = idx[target]
                outlinks[i].add(j)

    for i in range(number_of_nodes):
        for j in outlinks[i]:
            inlinks[j].append(i)

    r = [1.0 / number_of_nodes] * number_of_nodes
    base = (1.0 - alpha) / number_of_nodes

    for _ in range(iters):
        new = [base] * number_of_nodes
        # distribute rank
        for j in range(number_of_nodes):
            s = 0.0
            for i in inlinks[j]:
                deg = len(outlinks[i])
                if deg:
                    s += r[i] / deg
            new[j] += alpha * s

        # handle dangling nodes (no outlinks)
        dangling_sum = sum(r[i] for i in range(
            number_of_nodes) if len(outlinks[i]) == 0)
        if dangling_sum:
            add = alpha * dangling_sum / number_of_nodes
            new = [v + add for v in new]

        r = new

    return {nodes[i]: r[i] for i in range(number_of_nodes)}


def count_loc(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def count_importers(edges):
    importers = defaultdict(set)
    for source, targets in edges.items():
        for target in targets:
            importers[target].add(source)
    return {k: len(v) for k, v in importers.items()}


def build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-init", action="store_true", 
                        help="Include __init__.py files in output (default: hidden).")
    parser.add_argument("path", nargs="?", default=".",
                        help="Project root to scan (default: current directory).")
    parser.add_argument("--n", type=int, default=10,
                        help="Number of top-ranked files to show (default: 10).")
    parser.add_argument("--alpha", type=float, default=0.85,
                        help="PageRank damping factor (default: 0.85).")
    parser.add_argument("--iters", type=int, default=50,
                        help="Number of PageRank iterations (default: 50).")
    parser.add_argument("--json", action="store_true",
                        help="Emit results as JSON instead of a text table.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    root = args.path
    number_of_results = args.n if args.n is not None else 10

    nodes, edges = build_graph(root)
    pr = pagerank(nodes, edges, alpha=args.alpha, iters=args.iters)
    importers = count_importers(edges)

    rows = []
    for path, score in pr.items():
        rel = os.path.relpath(path, root)        
        if (not args.include_init) and os.path.basename(rel) == "__init__.py":
            continue
        rows.append({
            "path": rel,
            "loc": count_loc(path),
            "importers": importers.get(path, 0),
            "pagerank": score,
        })

    rows.sort(key=lambda r: r["pagerank"], reverse=True)
    rows = rows[:number_of_results]

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'Module':40} {'LOC':>5} {'Importers':>10} {'PageRank':>10}")
        print("-" * 70)
        for r in rows:
            print(
                f"{r['path'][:40]:40} {r['loc']:5d} {r['importers']:10d} {r['pagerank']:10.6f}")


if __name__ == "__main__":
    main()
