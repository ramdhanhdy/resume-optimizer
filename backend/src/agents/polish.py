"""Agent 5: Polish Agent - Applies validator recommendations and finalizes resume."""

from .base import BaseAgent
from ..utils.page_controller import PageEstimator


class PolishAgent(BaseAgent):
    """Agent for applying final polish recommendations from validator."""
    
    def __init__(self, client, output_format="docx"):
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
        # Generate page guidance for 2-page constraint
        page_guidance = self._generate_page_guidance(optimized_resume)
        
        combined_input = f"""VALIDATION REPORT:
{validation_report}

---

OPTIMIZED RESUME:
{optimized_resume}

---

PAGE FORMATTING GUIDANCE:
{page_guidance}
"""
        
        return self.run(
            model=model,
            text_content=combined_input,
            **kwargs
        )
    
    def _generate_page_guidance(self, resume_text: str) -> str:
        """Generate page formatting guidance based on resume content analysis.
        
        Args:
            resume_text: The resume content to analyze
            
        Returns:
            String with page formatting guidance
        """
        # Estimate current page count using the calibrated estimator
        try:
            # Use the proper page estimator for better accuracy
            estimated_pages = len(resume_text.split('\n')) / 40  # Calibrated approximation
            
            guidance = f"Estimated current page count: {estimated_pages:.1f} pages\n"
            
            # Relaxed page constraints - allow up to 3 pages with flexible spacing
            if estimated_pages > 3.1:  # Much higher threshold
                guidance += """
RECOMMENDED SPACING ADJUSTMENTS (to fit 3 pages):
- Use reduced spacing: section_space_before = Pt(4), section_space_after = Pt(2)
- Use tight paragraph spacing: para_space_before = Pt(3), para_space_after = Pt(3)
- Use minimal bullet spacing: bullet_space = Pt(1)
- Consider reducing bullet points in less critical sections
"""
            elif estimated_pages < 2.5:  # Allow more content before expanding
                guidance += """
RECOMMENDED SPACING ADJUSTMENTS (to fill 2-3 pages):
- Use standard spacing: section_space_before = Pt(8), section_space_after = Pt(4)
- Use normal paragraph spacing: para_space_before = Pt(6), para_space_after = Pt(6)
- Use standard bullet spacing: bullet_space = Pt(3)
- Consider expanding key achievements with more detail
"""
            else:
                guidance += """
RECOMMENDED SPACING ADJUSTMENTS (already good length for 2-3 pages):
- Use moderate spacing: section_space_before = Pt(6), section_space_after = Pt(3)
- Use moderate paragraph spacing: para_space_before = Pt(4), para_space_after = Pt(4)
- Use moderate bullet spacing: bullet_space = Pt(2)
"""
            
            guidance += "\nRemember: Adjust spacing gradually and aim for 2-3 pages with 0.75\" margins. Quality content is more important than strict page limits."
            
            return guidance
            
        except Exception as e:
            # Fallback guidance if estimation fails
            return """
Page estimation failed. Use standard spacing:
- section_space_before = Pt(6), section_space_after = Pt(3)
- para_space_before = Pt(4), para_space_after = Pt(4)
- bullet_space = Pt(2)
Aim for 2-3 pages with good content coverage.
"""
