"""Agent 1: Job Analysis Agent."""

from typing import Optional

from .base import BaseAgent


class JobAnalyzerAgent(BaseAgent):
    """Agent for analyzing job postings and extracting requirements."""

    def __init__(self, client):
        """Initialize Job Analyzer agent.

        Args:
            client: OpenRouter API client instance
        """
        super().__init__(
            prompt_file="prompts/agent1_job_analyzer.md",
            agent_name="Job Analyzer",
            client=client,
        )

    def analyze_job(
        self,
        job_posting: Optional[str],
        model: str,
        profile_index: Optional[str] = None,
        **kwargs,
    ):
        """Analyze a job posting.

        Args:
            job_posting: Job posting text (if available)
            model: Model identifier
            profile_index: Optional candidate profile index for context
            **kwargs: Additional arguments for API call

        Yields:
            Response chunks

        Returns:
            Final analysis with metadata
        """
        analysis_input = job_posting or ""
        if profile_index:
            analysis_input = (
                (analysis_input + "\n\n" if analysis_input else "")
                + "<candidate_profile_index>\n"
                + profile_index
                + "\n</candidate_profile_index>"
            )
        return self.run(
            model=model,
            text_content=analysis_input,
            **kwargs,
        )
