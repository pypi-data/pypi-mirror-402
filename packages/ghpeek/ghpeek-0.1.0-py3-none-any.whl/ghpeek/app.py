from __future__ import annotations

import asyncio
import os
import re
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Markdown,
    Static,
)

from ghpeek import __version__
from ghpeek.state import AppState, ReadState, RepoFilters, load_state, save_state

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass
class RepoSummary:
    full_name: str
    stars: int
    forks: int
    open_issues: int
    open_pulls: int


@dataclass
class RepoItem:
    item_id: int
    number: int
    title: str
    url: str
    read: bool
    state: str
    author: str
    created_at: str
    updated_at: str
    comments: int
    labels: list[str]
    body: str


@dataclass
class RepoData:
    summary: RepoSummary
    issues: list[RepoItem] = field(default_factory=list)
    pulls: list[RepoItem] = field(default_factory=list)


class RepoListItem(ListItem):
    def __init__(self, full_name: str) -> None:
        super().__init__(Label(full_name))
        self.full_name = full_name


@dataclass
class RepoChoice:
    full_name: str
    is_fork: bool
    is_private: bool
    is_personal: bool


class IssueListItem(ListItem):
    def __init__(self, item: RepoItem) -> None:
        suffix = " (closed)" if item.state == "closed" else ""
        label = Label(f"#{item.number} {item.title}{suffix}")
        super().__init__(label)
        self.item = item
        if not item.read:
            self.add_class("unread")
        if item.state == "closed":
            self.add_class("closed")

    def mark_read(self) -> None:
        if self.has_class("unread"):
            self.remove_class("unread")


class AddRepoScreen(ModalScreen[Optional[str]]):
    def __init__(
        self,
        show_repo_list: bool,
        filters: RepoFilters,
        on_filters_changed,
    ) -> None:
        super().__init__()
        self.show_repo_list = show_repo_list
        self.filters = filters
        self.on_filters_changed = on_filters_changed
        self._repo_choices: list[RepoChoice] = []

    def compose(self) -> ComposeResult:
        with Container(id="add-repo"):
            if self.show_repo_list:
                yield Label("Select from your repositories", id="repo-picker-label")
                with Container(id="repo-filters"):
                    with Horizontal():
                        yield Checkbox("Forks", value=True, id="filter-forks")
                        yield Checkbox("Public", value=True, id="filter-public")
                    with Horizontal():
                        yield Checkbox("Private", value=True, id="filter-private")
                        yield Checkbox("Organizations", value=True, id="filter-orgs")
                yield ListView(id="repo-picker")
                yield LoadingIndicator(id="repo-picker-loading")
            yield Label("Or enter owner/repo", id="repo-input-label")
            yield Input(placeholder="owner/repo", id="repo-input")
            yield Label("Enter: select/add   Esc: cancel", id="repo-hint")

    def on_mount(self) -> None:
        self.query_one("#add-repo", Container).border_title = "Add repository"
        if self.show_repo_list:
            self.query_one("#filter-forks", Checkbox).value = self.filters.show_forks
            self.query_one("#filter-public", Checkbox).value = self.filters.show_public
            self.query_one("#filter-private", Checkbox).value = self.filters.show_private
            self.query_one("#filter-orgs", Checkbox).value = self.filters.show_orgs
        self.query_one(Input).focus()

    @on(Input.Submitted, "#repo-input")
    def submit_repo(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

    def update_repos(self, repos: list[RepoChoice]) -> None:
        if not self.show_repo_list:
            return
        self._repo_choices = repos
        self._apply_filters()
        self.query_one("#repo-picker-loading", LoadingIndicator).add_class("hidden")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "repo-picker" and isinstance(event.item, RepoListItem):
            self.dismiss(event.item.full_name)

    def _apply_filters(self) -> None:
        if not self.show_repo_list:
            return
        show_forks = self.query_one("#filter-forks", Checkbox).value
        show_public = self.query_one("#filter-public", Checkbox).value
        show_private = self.query_one("#filter-private", Checkbox).value
        show_orgs = self.query_one("#filter-orgs", Checkbox).value
        filtered: list[RepoChoice] = []
        for repo in self._repo_choices:
            if not show_forks and repo.is_fork:
                continue
            if repo.is_private and not show_private:
                continue
            if not repo.is_private and not show_public:
                continue
            if not show_orgs and not repo.is_personal:
                continue
            filtered.append(repo)
        repo_list = self.query_one("#repo-picker", ListView)
        repo_list.clear()
        for repo in filtered:
            repo_list.append(RepoListItem(repo.full_name))

    @on(Checkbox.Changed, "#filter-forks")
    @on(Checkbox.Changed, "#filter-public")
    @on(Checkbox.Changed, "#filter-private")
    @on(Checkbox.Changed, "#filter-orgs")
    def _filters_changed(self, event: Checkbox.Changed) -> None:
        self.on_filters_changed(
            RepoFilters(
                show_forks=self.query_one("#filter-forks", Checkbox).value,
                show_public=self.query_one("#filter-public", Checkbox).value,
                show_private=self.query_one("#filter-private", Checkbox).value,
                show_orgs=self.query_one("#filter-orgs", Checkbox).value,
            )
        )
        self._apply_filters()


class PreviewScreen(ModalScreen[None]):
    def __init__(self, item: RepoItem, list_item: "IssueListItem") -> None:
        super().__init__()
        self.item = item
        self.list_item = list_item

    def compose(self) -> ComposeResult:
        with Container(id="preview"):
            yield Label(self.item.title, id="preview-title")
            yield Static(self._build_meta(), id="preview-meta")
            body = self.item.body.strip() if self.item.body else ""
            if not body:
                body = "_No description provided._"
            yield Markdown(body, id="preview-body")
            yield Label("Enter: open in browser   Esc: close", id="preview-hint")

    def _build_meta(self) -> str:
        labels = ", ".join(self.item.labels) if self.item.labels else "none"
        return (
            f"#{self.item.number}  State: {self.item.state}  "
            f"Author: {self.item.author}  "
            f"Comments: {self.item.comments}\n"
            f"Created: {self.item.created_at}  Updated: {self.item.updated_at}\n"
            f"Labels: {labels}"
        )

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        if event.key == "enter":
            app = self.app
            if isinstance(app, GhPeekApp):
                app._open_item_in_browser(self.item, self.list_item)
            self.dismiss(None)


class GhPeekApp(App):
    CSS_PATH = "app.tcss"
    TITLE = f"GHPeek v{__version__} - your friendly github viewer"

    BINDINGS = [
        ("a", "add_repo", "Add repo"),
        ("r", "refresh_repo", "Refresh"),
        ("i", "show_issues", "Issues"),
        ("p", "show_pulls", "Pull requests"),
        ("c", "toggle_closed", "Toggle closed"),
        ("q", "quit", "Quit"),
        ("enter", "open_item", "Open"),
    ]

    def __init__(self) -> None:
        super().__init__()
        load_dotenv()
        self.state: AppState = load_state()
        self.repo_data: dict[str, RepoData] = {}
        self.selected_repo: Optional[str] = None
        self.current_view = "issues"
        self.show_closed = False
        token = os.getenv("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()
        self.has_token = bool(token)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="app-container"):
            with Vertical(id="sidebar"):
                yield ListView(id="repo-list")
            with Vertical(id="main"):
                yield Static("Select a repository to load details.", id="summary")
                with Horizontal(id="view-labels"):
                    yield Label("Issues", id="issues-label", classes="active")
                    yield Label("Pull Requests", id="pulls-label")
                yield ListView(id="issues-list")
                yield ListView(id="pulls-list", classes="hidden")
                with Container(id="status-bar"):
                    yield LoadingIndicator(id="loading", classes="hidden")
                    yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#sidebar", Vertical).border_title = "Repositories"
        repo_list = self.query_one("#repo-list", ListView)
        for repo in sorted(self.state.repos):
            repo_list.append(RepoListItem(repo))
        if self.state.repos:
            repo_list.index = 0
            self._select_repo(repo_list.children[0].full_name)

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _set_loading(self, loading: bool) -> None:
        indicator = self.query_one("#loading", LoadingIndicator)
        status = self.query_one("#status", Static)
        if loading:
            indicator.remove_class("hidden")
            status.add_class("hidden")
        else:
            indicator.add_class("hidden")
            status.remove_class("hidden")

    def _set_view(self, view: str) -> None:
        self.current_view = view
        issues = self.query_one("#issues-list", ListView)
        pulls = self.query_one("#pulls-list", ListView)
        issues_label = self.query_one("#issues-label", Label)
        pulls_label = self.query_one("#pulls-label", Label)
        if view == "issues":
            issues.remove_class("hidden")
            pulls.add_class("hidden")
            issues_label.add_class("active")
            pulls_label.remove_class("active")
            issues.focus()
        else:
            pulls.remove_class("hidden")
            issues.add_class("hidden")
            pulls_label.add_class("active")
            issues_label.remove_class("active")
            pulls.focus()

    def _ensure_read_state(self, repo: str) -> ReadState:
        if repo not in self.state.read:
            self.state.read[repo] = ReadState()
        return self.state.read[repo]

    def _render_summary(self, summary: RepoSummary) -> None:
        text = Text()
        text.append(summary.full_name, style="bold")
        text.append("\n")
        text.append(f"Stars: {summary.stars}   ")
        text.append(f"Forks: {summary.forks}   ")
        text.append(f"Open issues: {summary.open_issues}   ")
        text.append(f"Open PRs: {summary.open_pulls}")
        self.query_one("#summary", Static).update(text)

    def _render_items(self, items: Iterable[RepoItem], list_view: ListView) -> None:
        list_view.clear()
        for item in items:
            list_view.append(IssueListItem(item))

    @staticmethod
    def _format_dt(value: Optional[datetime]) -> str:
        if not value:
            return "unknown"
        return value.strftime("%Y-%m-%d")

    def _select_repo(self, full_name: str) -> None:
        self.selected_repo = full_name
        self._set_status(f"Loading {full_name}...")
        self.run_worker(self._load_repo_data(full_name, include_closed=self.show_closed))

    async def _load_repo_data(
        self,
        full_name: str,
        include_closed: bool = False,
        force: bool = False,
    ) -> None:
        cache_key = (full_name, include_closed)
        if cache_key in self.repo_data and not force:
            self._apply_repo_data(self.repo_data[cache_key])
            return
        self._set_loading(True)
        try:
            data = await asyncio.to_thread(self._fetch_repo_data, full_name, include_closed)
        except GithubException as exc:
            self._set_status(f"GitHub error: {exc.data.get('message', str(exc))}")
            self._set_loading(False)
            return
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Error: {exc}")
            self._set_loading(False)
            return
        self.repo_data[cache_key] = data
        self._apply_repo_data(data)
        self._set_loading(False)
        self._set_status(f"Loaded {full_name}.")

    def _apply_repo_data(self, data: RepoData) -> None:
        self._render_summary(data.summary)
        issues_list = self.query_one("#issues-list", ListView)
        pulls_list = self.query_one("#pulls-list", ListView)
        self._render_items(data.issues, issues_list)
        self._render_items(data.pulls, pulls_list)

    def _fetch_repo_data(self, full_name: str, include_closed: bool) -> RepoData:
        repo = self.github.get_repo(full_name)
        state = "all" if include_closed else "open"
        pulls = list(repo.get_pulls(state=state))
        issues = [issue for issue in repo.get_issues(state=state) if issue.pull_request is None]
        read_state = self._ensure_read_state(full_name)

        issue_items = [
            RepoItem(
                item_id=issue.id,
                number=issue.number,
                title=issue.title,
                url=issue.html_url,
                read=issue.id in read_state.issues,
                state=issue.state,
                author=issue.user.login if issue.user else "unknown",
                created_at=self._format_dt(issue.created_at),
                updated_at=self._format_dt(issue.updated_at),
                comments=issue.comments,
                labels=[label.name for label in issue.labels],
                body=issue.body or "",
            )
            for issue in issues
        ]
        pull_items = [
            RepoItem(
                item_id=pull.id,
                number=pull.number,
                title=pull.title,
                url=pull.html_url,
                read=pull.id in read_state.pulls,
                state=pull.state,
                author=pull.user.login if pull.user else "unknown",
                created_at=self._format_dt(pull.created_at),
                updated_at=self._format_dt(pull.updated_at),
                comments=pull.comments,
                labels=[label.name for label in pull.labels],
                body=pull.body or "",
            )
            for pull in pulls
        ]
        summary = RepoSummary(
            full_name=repo.full_name,
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            open_issues=repo.open_issues_count,
            open_pulls=len([pull for pull in pulls if pull.state == "open"]),
        )
        return RepoData(summary=summary, issues=issue_items, pulls=pull_items)

    def _open_item_in_browser(self, item: RepoItem, list_item: IssueListItem) -> None:
        if not webbrowser.open(item.url):
            self._set_status("Unable to open browser.")
        read_state = self._ensure_read_state(self.selected_repo or "")
        if self.current_view == "issues":
            read_state.issues.add(item.item_id)
        else:
            read_state.pulls.add(item.item_id)
        item.read = True
        list_item.mark_read()
        save_state(self.state)

    def action_show_issues(self) -> None:
        self._set_view("issues")

    def action_show_pulls(self) -> None:
        self._set_view("pulls")

    def action_refresh_repo(self) -> None:
        if not self.selected_repo:
            self._set_status("No repository selected.")
            return
        self._set_status(f"Refreshing {self.selected_repo}...")
        self.run_worker(
            self._load_repo_data(
                self.selected_repo,
                include_closed=self.show_closed,
                force=True,
            )
        )

    def action_add_repo(self) -> None:
        screen = AddRepoScreen(self.has_token, self.state.filters, self._update_repo_filters)
        self.push_screen(screen, self._handle_add_repo)
        if self.has_token:
            self.run_worker(self._load_user_repos(screen))

    def _update_repo_filters(self, filters: RepoFilters) -> None:
        self.state.filters = filters
        save_state(self.state)

    async def _load_user_repos(self, screen: AddRepoScreen) -> None:
        try:
            repos = await asyncio.to_thread(self._fetch_user_repos)
        except GithubException as exc:
            self._set_status(f"GitHub error: {exc.data.get('message', str(exc))}")
            return
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Error: {exc}")
            return
        screen.update_repos(repos)

    def _fetch_user_repos(self) -> list[RepoChoice]:
        user = self.github.get_user()
        user_login = user.login
        choices = [
            RepoChoice(
                full_name=repo.full_name,
                is_fork=repo.fork,
                is_private=repo.private,
                is_personal=(repo.owner and repo.owner.login == user_login),
            )
            for repo in user.get_repos()
        ]
        return sorted(choices, key=lambda choice: choice.full_name)

    def action_toggle_closed(self) -> None:
        self.show_closed = not self.show_closed
        state = "shown" if self.show_closed else "hidden"
        self._set_status(f"Closed items {state}.")
        if self.selected_repo:
            self.run_worker(
                self._load_repo_data(
                    self.selected_repo,
                    include_closed=self.show_closed,
                    force=True,
                )
            )

    def action_open_item(self) -> None:
        list_view_id = "#issues-list" if self.current_view == "issues" else "#pulls-list"
        list_view = self.query_one(list_view_id, ListView)
        if list_view.index is None:
            self._set_status("Nothing selected.")
            return
        list_item = list_view.children[list_view.index]
        if isinstance(list_item, IssueListItem):
            self.push_screen(PreviewScreen(list_item.item, list_item))

    def _handle_add_repo(self, value: Optional[str]) -> None:
        if value is None:
            self._set_status("Add repository canceled.")
            return
        if not REPO_RE.match(value):
            self._set_status("Repository must be in owner/repo format.")
            return
        if value in self.state.repos:
            self._set_status("Repository already added.")
            return
        self.state.repos.append(value)
        save_state(self.state)
        repo_list = self.query_one("#repo-list", ListView)
        repo_list.append(RepoListItem(value))
        repo_list.index = len(repo_list.children) - 1
        self._select_repo(value)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "repo-list" and event.item:
            if isinstance(event.item, RepoListItem):
                self._select_repo(event.item.full_name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id in {"issues-list", "pulls-list"}:
            list_item = event.item
            if isinstance(list_item, IssueListItem):
                self.push_screen(PreviewScreen(list_item.item, list_item))


def main() -> None:
    app = GhPeekApp()
    app.run()


if __name__ == "__main__":
    main()
