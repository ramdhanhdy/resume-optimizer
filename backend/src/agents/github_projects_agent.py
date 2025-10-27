"""GitHub Projects Curator Agent - LLM-only project selection and optimization"""

from __future__ import annotations
import datetime as dt
from typing import List, Dict, Any, Optional
from github import Github
from github.GithubException import GithubException


def _truncate(s: str, max_chars: int) -> str:
    """Truncate string to max length"""
    s = s or ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "..."


def _days_ago(d) -> int:
    """Calculate days since date"""
    if not d:
        return 10_000
    return (dt.datetime.utcnow().date() - d.date()).days


def fetch_github_repos(
    username: str, token: Optional[str] = None, max_repos: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch GitHub repositories with metadata.

    Args:
        username: GitHub username
        token: Optional GitHub token for higher rate limits/private repos
        max_repos: Maximum number of repos to fetch (None = all repos)

    Returns:
        List of repo dictionaries with metadata
    """
    gh = Github(token) if token else Github()

    try:
        auth_user = gh.get_user() if token else None
        if token:
            # Authenticated users can access their private repos via the token
            if auth_user.login.lower() == username.lower():
                repo_iter = auth_user.get_repos(visibility="all")
            else:
                repo_iter = gh.get_user(username).get_repos()
        else:
            repo_iter = gh.get_user(username).get_repos()
        repos = [
            r
            for r in repo_iter
            if r.owner and r.owner.login.lower() == username.lower()
        ]
    except GithubException as exc:
        raise ValueError(
            f"Unable to fetch repositories for user '{username}': {exc}"
        ) from exc

    # Pre-filter: ignore archived and forks; sort by (recent push, then stars)
    repos = [r for r in repos if not r.archived and not r.fork]
    repos.sort(
        key=lambda r: (r.pushed_at or dt.datetime(1970, 1, 1), r.stargazers_count),
        reverse=True,
    )
    if max_repos is not None:
        repos = repos[:max_repos]

    out = []
    for r in repos:
        try:
            readme = r.get_readme().decoded_content.decode("utf-8", errors="ignore")
        except Exception:
            readme = ""

        # Get primary language
        langs = r.get_languages() or {}
        primary_lang = (
            max(langs, key=lambda lang: langs.get(lang, 0)) if langs else None
        )

        out.append(
            {
                "name": r.name,
                "url": r.html_url,
                "description": r.description or "",
                "topics": r.get_topics() or [],
                "primary_lang": primary_lang,
                "stars": r.stargazers_count or 0,
                "last_push_days": _days_ago(r.pushed_at) if r.pushed_at else 10_000,
                "readme": _truncate(readme, 6000),  # Keep prompt lean
            }
        )

    return out


class GitHubProjectsAgent:
    """Agent for curating GitHub projects using LLM"""

    def __init__(self, client):
        """
        Initialize GitHub Projects Agent.

        Args:
            client: OpenRouter API client instance
        """
        self.client = client
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get system prompt for project curation"""
        return """You are a senior résumé editor. Task: choose the best 2–4 GitHub projects for a targeted résumé and write tight bullets.

⚠️ CRITICAL: Grounding and Truthfulness Rules

**Only select from the provided repo list. Each bullet must be supported by README or code.**

1. **Do NOT fabricate project details:**
   - Use ONLY repos in the provided github_candidates list
   - Do NOT invent features, technologies, or metrics not in README/description
   - Do NOT add team sizes, user counts, or performance metrics unless in README

2. **Conservative verbs when unclear:**
   - If README unclear whether candidate 'built' vs 'contributed', use:
     - "Contributed to" or "Implemented" (for features)
     - "Developed" (when clearly solo project)
     - "Collaborated on" (when team indicators present)
   - Do NOT claim "Led" or "Architected" without clear evidence

3. **Include repo URL for each selected project** (for verification)

4. **Evidence-based bullets:**
   - ✅ "Implemented REST API with Express.js and MongoDB" (if in README/code)
   - ❌ "Built API handling 100k requests/day" (fabricated metric)
   - ✅ "Contributed to open-source CLI tool for data processing"
   - ❌ "Led team of 3 building enterprise tool" (invented leadership/team)

Rules:
- Optimize for RELEVANCE to the target role, RECENCY, and EVIDENCE of impact.
- Aim for diversity of stack if possible (but relevance first).
- Each project: 2 bullets, ≤ 22 words each, action→tech→impact; no first-person, no filler.
- Keep résumé within 1 page: do not exceed 8 bullets total in Projects.

Return ONLY valid JSON with this schema:
{
  "chosen_projects": [
    {
      "name": "...",
      "url": "...",
      "why": "1-2 lines explaining relevance",
      "bullets": ["...", "..."]
    }
  ],
  "drop_projects_from_resume": ["ProjectName1", "ProjectName2"],
  "projects_section_html": "<h2>Projects</h2><div class='project-item'>...</div>",
  "notes_for_editor": "any layout notes"
}

The projects_section_html should use the classic Times New Roman template structure:
- Use <h2>Projects</h2> for section header
- Use <div class="project-item"> for each project
- Use <div class="item-header"> with <span class="item-title"> and <span class="item-location">
- Use <div class="item-subtitle"> for technologies
- Use <ul><li> for bullets
"""

    def _build_user_prompt(
        self, resume_text: str, job_analysis: str, repos: List[Dict[str, Any]]
    ) -> str:
        """Build user prompt with resume, job, and GitHub data"""
        import json

        pack = {
            "job_analysis": _truncate(job_analysis, 8000),
            "current_resume_excerpt": _truncate(resume_text, 8000),
            "github_candidates": [
                {
                    "name": r["name"],
                    "url": r["url"],
                    "desc": r["description"],
                    "topics": r["topics"],
                    "primary_lang": r["primary_lang"],
                    "stars": r["stars"],
                    "last_push_days": r["last_push_days"],
                    "readme_excerpt": _truncate(r["readme"], 1500),
                }
                for r in repos
            ],
        }

        return (
            "Use the data below to pick the best projects and produce JSON per schema.\n"
            "Additional rule: Do NOT assume GitHub repos are already present in the resume. The drop_projects_from_resume list MUST ONLY include project names that appear in the current_resume_excerpt; otherwise return an empty list.\n"
            "```\n" + json.dumps(pack, ensure_ascii=False, indent=2) + "\n```"
        )

    def curate_projects(
        self,
        github_username: str,
        resume_text: str,
        job_analysis: str,
        model: str,
        github_token: Optional[str] = None,
        repos: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000,
        **kwargs,
    ):
        """
        Curate GitHub projects for resume.

        Args:
            github_username: GitHub username to scan
            resume_text: Current resume text
            job_analysis: Job analysis from Agent 1
            model: Model identifier
            github_token: Optional GitHub token (only used if repos not provided)
            repos: Optional pre-fetched repos (if None, will fetch from GitHub)
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Response chunks

        Returns:
            Curated projects with metadata
        """
        # Use provided repos or fetch from GitHub
        if repos is None:
            # Fetch GitHub repos (limit to 12 for LLM context window)
            repos = fetch_github_repos(github_username, token=github_token, max_repos=12)
        else:
            # Use provided repos but limit to 12 for LLM context window
            repos = repos[:12]

        if not repos:
            raise ValueError(f"No repositories found for user: {github_username}")

        # Build prompt
        user_prompt = self._build_user_prompt(resume_text, job_analysis, repos)

        # Stream completion
        stream = self.client.stream_completion(
            prompt=self.system_prompt,
            model=model,
            text_content=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            # Ignore any extra kwargs not supported by this provider
        )

        # Yield all chunks and capture return value
        try:
            while True:
                chunk = next(stream)
                yield chunk
        except StopIteration as e:
            # Return the metadata from the generator
            return e.value if e.value else {}
