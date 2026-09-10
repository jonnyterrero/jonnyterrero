#!/usr/bin/env python3
"""Update the profile README with public LeetCode and NeetCode progress."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LEETCODE_API = "https://leetcode.com/graphql/"
GITHUB_API = "https://api.github.com"
README_PATH = Path("README.md")
START_MARKER = "<!--CODING_STATS_START-->"
END_MARKER = "<!--CODING_STATS_END-->"
SOLUTION_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".kt",
    ".py",
    ".rs",
    ".swift",
    ".ts",
}
NEETCODE_ROOTS = ("Data Structures & Algorithms", "Python For Beginners")

LEETCODE_QUERY = """
query profileProgress($username: String!) {
  matchedUser(username: $username) {
    username
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  recentSubmissionList(username: $username, limit: 20) {
    title
    titleSlug
    statusDisplay
  }
}
"""


class StatsError(RuntimeError):
    """Raised when a public statistics source returns invalid data."""


@dataclass(frozen=True)
class LeetCodeStats:
    total: int
    easy: int
    medium: int
    hard: int
    recent_accepts: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class NeetCodeStats:
    problems: int
    submissions: int
    latest_message: str
    latest_date: str


def request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> dict[str, Any] | list[Any]:
    """Request JSON with a short timeout and useful failure messages."""

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "jonnyterrero-profile-readme-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise StatsError(f"Request failed for {url}: {exc}") from exc


def fetch_leetcode_stats(username: str) -> LeetCodeStats:
    """Fetch solved counts and the five most recent unique accepted problems."""

    response = request_json(
        LEETCODE_API,
        payload={"query": LEETCODE_QUERY, "variables": {"username": username}},
    )
    if not isinstance(response, dict) or response.get("errors"):
        errors = response.get("errors") if isinstance(response, dict) else response
        raise StatsError(f"LeetCode returned errors: {errors}")

    data = response.get("data", {})
    matched_user = data.get("matchedUser")
    if not matched_user:
        raise StatsError(f"LeetCode user {username!r} was not found")

    rows = matched_user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
    counts = {row.get("difficulty"): int(row.get("count", 0)) for row in rows}
    required = {"All", "Easy", "Medium", "Hard"}
    if not required.issubset(counts):
        raise StatsError(f"LeetCode response is missing difficulty counts: {counts}")

    recent: list[tuple[str, str]] = []
    seen_slugs: set[str] = set()
    for submission in data.get("recentSubmissionList") or []:
        slug = str(submission.get("titleSlug", ""))
        title = str(submission.get("title", ""))
        if submission.get("statusDisplay") != "Accepted" or not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        recent.append((title, slug))
        if len(recent) == 5:
            break

    return LeetCodeStats(
        total=counts["All"],
        easy=counts["Easy"],
        medium=counts["Medium"],
        hard=counts["Hard"],
        recent_accepts=tuple(recent),
    )


def fetch_neetcode_stats(user: str, repository: str, token: str | None) -> NeetCodeStats:
    """Count NeetCode-managed problem folders and synchronized submissions."""

    repo_path = f"{user}/{repository}"
    repo = request_json(f"{GITHUB_API}/repos/{repo_path}", token=token)
    if not isinstance(repo, dict) or not repo.get("default_branch"):
        raise StatsError(f"GitHub repository {repo_path!r} was not found")

    branch = repo["default_branch"]
    tree = request_json(
        f"{GITHUB_API}/repos/{repo_path}/git/trees/{branch}?recursive=1",
        token=token,
    )
    if not isinstance(tree, dict) or tree.get("truncated"):
        raise StatsError("GitHub returned an incomplete NeetCode repository tree")

    problems, submissions = count_neetcode_solutions(tree.get("tree", []))

    commits = request_json(f"{GITHUB_API}/repos/{repo_path}/commits?per_page=1", token=token)
    if not isinstance(commits, list) or not commits:
        raise StatsError("GitHub returned no commits for the NeetCode repository")

    latest = commits[0].get("commit", {})
    latest_message = str(latest.get("message", "Unknown update")).splitlines()[0]
    date_value = latest.get("committer", {}).get("date") or latest.get("author", {}).get("date")
    if not date_value:
        raise StatsError("The latest NeetCode commit has no timestamp")
    latest_date = datetime.fromisoformat(str(date_value).replace("Z", "+00:00")).date().isoformat()

    return NeetCodeStats(
        problems=problems,
        submissions=submissions,
        latest_message=latest_message,
        latest_date=latest_date,
    )


def count_neetcode_solutions(tree_items: list[dict[str, Any]]) -> tuple[int, int]:
    """Count unique NeetCode problem folders and managed submission files."""

    problems: set[tuple[str, str]] = set()
    submissions = 0
    for item in tree_items:
        if item.get("type") != "blob":
            continue

        path = PurePosixPath(str(item.get("path", "")))
        if len(path.parts) < 3 or path.parts[0] not in NEETCODE_ROOTS:
            continue
        if not path.name.startswith("submission-") or path.suffix.lower() not in SOLUTION_SUFFIXES:
            continue

        problems.add((path.parts[0], path.parts[1]))
        submissions += 1

    return len(problems), submissions


def escape_markdown(text: str) -> str:
    """Escape table-breaking and link-label characters from external text."""

    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def render_stats(
    leetcode: LeetCodeStats,
    neetcode: NeetCodeStats,
    *,
    leetcode_username: str,
    github_user: str,
    neetcode_repository: str,
) -> str:
    """Render the generated Markdown kept between the README markers."""

    leetcode_url = f"https://leetcode.com/u/{leetcode_username}/"
    neetcode_url = f"https://github.com/{github_user}/{neetcode_repository}"

    lines = [
        "_Updated daily from public profile and repository data._",
        "",
        "| Platform | Progress |",
        "| --- | --- |",
        (
            f"| [**LeetCode**]({leetcode_url}) | **{leetcode.total} solved** · "
            f"{leetcode.easy} Easy · {leetcode.medium} Medium · {leetcode.hard} Hard |"
        ),
        (
            f"| [**NeetCode**]({neetcode_url}) | **{neetcode.problems} problems** · "
            f"{neetcode.submissions} synchronized submissions |"
        ),
    ]

    if leetcode.recent_accepts:
        recent_links = " · ".join(
            f"[{escape_markdown(title)}](https://leetcode.com/problems/{slug}/)"
            for title, slug in leetcode.recent_accepts
        )
        lines.extend(["", f"**Recent LeetCode accepts:** {recent_links}"])

    lines.extend(
        [
            "",
            (
                "**Latest NeetCode sync:** "
                f"{escape_markdown(neetcode.latest_message)} · {neetcode.latest_date}"
            ),
        ]
    )
    return "\n".join(lines)


def update_readme(generated: str) -> bool:
    """Replace exactly one generated block and report whether content changed."""

    original = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(START_MARKER)})\n.*?\n({re.escape(END_MARKER)})",
        flags=re.DOTALL,
    )
    updated, replacements = pattern.subn(
        lambda match: f"{match.group(1)}\n{generated}\n{match.group(2)}",
        original,
    )
    if replacements != 1:
        raise StatsError(
            f"Expected one coding-stats block in {README_PATH}, found {replacements}"
        )

    if updated == original:
        return False

    README_PATH.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    leetcode_username = os.environ.get("LEETCODE_USERNAME", "jterrero16")
    github_user = os.environ.get("GITHUB_USER", "jonnyterrero")
    neetcode_repository = os.environ.get("NEETCODE_REPOSITORY", "Neetcode-Problems")
    github_token = os.environ.get("GITHUB_TOKEN")

    leetcode = fetch_leetcode_stats(leetcode_username)
    neetcode = fetch_neetcode_stats(github_user, neetcode_repository, github_token)
    generated = render_stats(
        leetcode,
        neetcode,
        leetcode_username=leetcode_username,
        github_user=github_user,
        neetcode_repository=neetcode_repository,
    )
    changed = update_readme(generated)
    print("Updated README coding statistics." if changed else "README coding statistics are current.")


if __name__ == "__main__":
    main()
