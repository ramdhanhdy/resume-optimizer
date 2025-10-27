"""Agent 5: Polish Agent - Applies validator recommendations and finalizes resume."""

from .base import BaseAgent


class PolishAgent(BaseAgent):
    """Agent for applying final polish recommendations from validator."""
    
    def __init__(self, client, output_format="html"):
        """Initialize Polish agent.
        
        Args:
            client: OpenRouter API client instance
            output_format: Either "html" or "docx"
        """
        self.output_format = output_format
        prompt_file = "prompts/agent5_polish.md" if output_format == "html" else "prompts/agent5_polish_docx.md"
        super().__init__(
            prompt_file=prompt_file,
            agent_name="Polish Agent",
            client=client
        )
    
    def polish_resume(
        self, 
        optimized_resume: str, 
        validation_report: str,
        model: str,
        **kwargs
    ):
        """Apply final polish recommendations to produce submission-ready resume.
        
        Args:
            optimized_resume: Optimized resume from Agent 3
            validation_report: Validation report from Agent 4
            model: Model identifier
            **kwargs: Additional arguments for API call
            
        Yields:
            Response chunks
            
        Returns:
            Final polished resume text with metadata
        """
        combined_input = f"""VALIDATION REPORT:
{validation_report}

---

OPTIMIZED RESUME:
{optimized_resume}
"""
        
        return self.run(
            model=model,
            text_content=combined_input,
            **kwargs
        )
