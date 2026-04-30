"""Post-generation resume refinement agent."""

from .base import BaseAgent


class ResumeRefinementAgent(BaseAgent):
    """Agent for applying user feedback to an existing polished resume."""

    def __init__(self, client):
        super().__init__(
            prompt_file="prompts/agent_refine_resume.md",
            agent_name="Resume Refinement Agent",
            client=client,
        )

    def refine_resume(
        self,
        *,
        current_resume: str,
        instruction: str,
        job_context: str,
        validation_report: str,
        model: str,
        **kwargs,
    ):
        combined_input = f"""USER INSTRUCTION:
{instruction}

---

CURRENT RESUME:
{current_resume}

---

JOB CONTEXT:
{job_context}

---

VALIDATION CONTEXT:
{validation_report}
"""

        return self.run(
            model=model,
            text_content=combined_input,
            **kwargs,
        )
