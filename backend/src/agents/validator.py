"""Agent 3: Validation Agent."""

from .base import BaseAgent


class ValidatorAgent(BaseAgent):
    """Agent for validating and scoring optimized resumes."""

    def __init__(self, client):
        """Initialize Validator agent.

        Args:
            client: OpenRouter API client instance
        """
        super().__init__(
            prompt_file="prompts/agent3_validator.md",
            agent_name="Validator",
            client=client,
        )

    def validate_resume(
        self,
        optimized_resume: str,
        job_posting: str,
        job_analysis: str,
        model: str,
        profile_index: str | None = None,
        **kwargs,
    ):
        """Validate optimized resume against job requirements.

        Args:
            optimized_resume: Optimized resume text
            job_posting: Original job posting
            job_analysis: Output from Agent 1
            model: Model identifier
            **kwargs: Additional arguments for API call

        Yields:
            Response chunks

        Returns:
            Validation results with scores and metadata
        """
        sections = [
            "JOB POSTING:\n" + job_posting,
            "JOB ANALYSIS:\n" + job_analysis,
        ]
        if profile_index and profile_index.strip():
            sections.append("PROFILE INDEX (evidence-aware):\n" + profile_index)
        sections.append("OPTIMIZED RESUME:\n" + optimized_resume)
        combined_input = "\n\n---\n\n".join(sections)

        return self.run(model=model, text_content=combined_input, **kwargs)
