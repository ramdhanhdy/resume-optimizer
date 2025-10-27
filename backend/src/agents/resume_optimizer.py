"""Agent 2: Resume Optimization Agent."""

from .base import BaseAgent


class ResumeOptimizerAgent(BaseAgent):
    """Agent for optimizing resumes based on job analysis."""

    def __init__(self, client):
        """Initialize Resume Optimizer agent.

        Args:
            client: OpenRouter API client instance
        """
        super().__init__(
            prompt_file="prompts/agent2_resume_optimizer.md",
            agent_name="Resume Optimizer",
            client=client,
        )

    def optimize_resume(
        self,
        resume_text: str,
        job_analysis: str,
        model: str,
        profile_index: str | None = None,
        **kwargs,
    ):
        """Optimize a resume based on job analysis.

        Args:
            resume_text: Original resume text
            job_analysis: Output from Agent 1
            model: Model identifier
            **kwargs: Additional arguments for API call

        Yields:
            Response chunks

        Returns:
            Optimized resume with metadata
        """
        sections = [
            "JOB ANALYSIS:\n" + job_analysis,
        ]

        if profile_index and profile_index.strip():
            sections.append(
                "PROFILE INDEX (evidence-aware, conservative):\n" + profile_index
            )

        sections.append("ORIGINAL RESUME:\n" + resume_text)

        combined_input = "\n\n---\n\n".join(sections)

        return self.run(model=model, text_content=combined_input, **kwargs)
