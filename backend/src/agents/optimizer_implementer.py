"""Agent 3: Optimizer Implementer Agent - Applies recommendations to generate optimized resume."""

from .base import BaseAgent


class OptimizerImplementerAgent(BaseAgent):
    """Agent for implementing optimization recommendations to produce the final optimized resume."""

    def __init__(self, client):
        """Initialize Optimizer Implementer agent.

        Args:
            client: OpenRouter API client instance
        """
        super().__init__(
            prompt_file="prompts/agent3_optimizer_implementer.md",
            agent_name="Optimizer Implementer",
            client=client,
        )

    def implement_optimizations(
        self,
        resume_text: str,
        optimization_report: str,
        model: str,
        profile_index: str | None = None,
        **kwargs,
    ):
        """Apply optimization recommendations to produce final optimized resume.

        Args:
            resume_text: Original resume text
            optimization_report: Full report from Agent 2 (ResumeOptimizerAgent)
            model: Model identifier
            **kwargs: Additional arguments for API call

        Yields:
            Response chunks

        Returns:
            Optimized resume text with metadata
        """
        sections = [
            "OPTIMIZATION REPORT:\n" + optimization_report,
        ]

        if profile_index and profile_index.strip():
            sections.append(
                "PROFILE INDEX (evidence-aware, conservative):\n" + profile_index
            )

        sections.append("ORIGINAL RESUME:\n" + resume_text)

        combined_input = "\n\n---\n\n".join(sections)

        return self.run(model=model, text_content=combined_input, **kwargs)
