from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".config" / "ghpeek"
STATE_FILE = CONFIG_DIR / "state.json"


@dataclass
class ReadState:
    issues: set[int] = field(default_factory=set)
    pulls: set[int] = field(default_factory=set)


@dataclass
class RepoFilters:
    show_forks: bool = True
    show_public: bool = True
    show_private: bool = True
    show_orgs: bool = True


@dataclass
class AppState:
    repos: list[str] = field(default_factory=list)
    read: dict[str, ReadState] = field(default_factory=dict)
    filters: RepoFilters = field(default_factory=RepoFilters)
    show_closed: bool = False


def _read_state_payload(payload: dict[str, Any]) -> AppState:
    repos = [str(name) for name in payload.get("repos", [])]
    read_state: dict[str, ReadState] = {}
    for repo, data in payload.get("read", {}).items():
        issues = {int(value) for value in data.get("issues", [])}
        pulls = {int(value) for value in data.get("pulls", [])}
        read_state[str(repo)] = ReadState(issues=issues, pulls=pulls)
    filters_payload = payload.get("filters", {})
    filters = RepoFilters(
        show_forks=bool(filters_payload.get("show_forks", True)),
        show_public=bool(filters_payload.get("show_public", True)),
        show_private=bool(filters_payload.get("show_private", True)),
        show_orgs=bool(filters_payload.get("show_orgs", True)),
    )
    show_closed = bool(payload.get("show_closed", False))
    return AppState(repos=repos, read=read_state, filters=filters, show_closed=show_closed)


def load_state() -> AppState:
    if not STATE_FILE.exists():
        return AppState()
    try:
        payload = json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return AppState()
    if not isinstance(payload, dict):
        return AppState()
    return _read_state_payload(payload)


def save_state(state: AppState) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "repos": sorted(state.repos),
        "read": {
            repo: {
                "issues": sorted(read.issues),
                "pulls": sorted(read.pulls),
            }
            for repo, read in state.read.items()
        },
        "filters": {
            "show_forks": state.filters.show_forks,
            "show_public": state.filters.show_public,
            "show_private": state.filters.show_private,
            "show_orgs": state.filters.show_orgs,
        },
        "show_closed": state.show_closed,
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))
