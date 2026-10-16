# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Extract comprehensive language metadata from Pygments and generate languages.json.
This script can be executed during build to generate the static language database.
"""

from __future__ import annotations

import json
from pathlib import Path

from pygments.lexers import get_all_lexers

# Categories mapping for popular languages
POPULAR_CATEGORIES: dict[str, str] = {
    "python": "Backend / Data",
    "go": "Systems / Backend",
    "rust": "Systems / WebAssembly",
    "javascript": "Frontend / Fullstack",
    "typescript": "Frontend / Fullstack",
    "bash": "DevOps / Shell",
    "yaml": "Configuration / DevOps",
    "json": "Data Interchange",
    "sql": "Database / Analytics",
    "promql": "Monitoring / Observability",
    "dockerfile": "Containers / Cloud",
    "c": "Systems",
    "cpp": "Systems / Performance",
    "csharp": "Enterprise / Backend",
    "java": "Enterprise / JVM",
    "kotlin": "Mobile / JVM",
    "swift": "Apple / Mobile",
    "html": "Web / Markup",
    "css": "Web / Styling",
    "markdown": "Documentation / Text",
    "terraform": "Infrastructure as Code",
    "graphql": "API / Query",
    "ruby": "Backend / Web",
    "php": "Backend / Web",
    "lua": "Embedded / Scripting",
    "r": "Data / Statistics",
    "julia": "Scientific Computing",
    "scala": "Data / JVM",
    "zig": "Systems",
    "elixir": "Distributed / Web",
    "erlang": "Distributed / Telecom",
    "haskell": "Functional",
    "nix": "Package / DevOps",
    "powershell": "Windows / Automation",
    "solidity": "Smart Contracts / Web3",
    "wat": "WebAssembly",
    "diff": "Version Control",
    "toml": "Configuration",
    "protobuf": "RPC / Serialization",
    "text": "Plain Text",
}

POPULAR_SET = set(POPULAR_CATEGORIES.keys())


def build_languages_registry() -> list[dict]:
    registry: list[dict] = []
    seen_ids: set[str] = set()

    for name, aliases, filenames, mimetypes in get_all_lexers():
        if not aliases:
            continue
        primary_id = aliases[0].lower()
        if primary_id in seen_ids:
            continue
        seen_ids.add(primary_id)

        # Categorize
        category = "Other"
        for alias in aliases:
            if alias.lower() in POPULAR_CATEGORIES:
                category = POPULAR_CATEGORIES[alias.lower()]
                break

        is_pop = any(a.lower() in POPULAR_SET for a in aliases)

        registry.append(
            {
                "id": primary_id,
                "name": name,
                "aliases": list(aliases),
                "filenames": list(filenames),
                "mimetypes": list(mimetypes),
                "category": category,
                "is_popular": is_pop,
            }
        )

    # Add custom PromQL if not present
    if "promql" not in seen_ids:
        registry.append(
            {
                "id": "promql",
                "name": "PromQL (Prometheus)",
                "aliases": ["promql", "prometheus"],
                "filenames": ["*.promql"],
                "mimetypes": ["text/x-promql"],
                "category": "Monitoring / Observability",
                "is_popular": True,
            }
        )

    # Sort popular first, then alphabetically
    registry.sort(key=lambda x: (not x["is_popular"], x["name"].lower()))
    return registry


def main():
    target_dir = Path(__file__).resolve().parent.parent / "code_block_xblock" / "data"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "languages.json"

    data = build_languages_registry()
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {out_file} with {len(data)} language definitions.")


if __name__ == "__main__":
    main()
