"""Parallel insight extraction using lightweight LLM."""

import asyncio
from typing import List, Dict, Optional
from src.api.client_factory import create_client


class BaseInsightExtractor:
    """Base class for insight extraction."""
    
    def __init__(self, model: str = "cerebras::gpt-oss-120b"):
        self.client = create_client()
        self.model = model
    
    def get_prompt(self, agent_type: str) -> str:
        """Override in subclasses to provide specific prompts."""
        raise NotImplementedError


class ContentInsightExtractor(BaseInsightExtractor):
    """Extract insights from content-generating agents (analyzer, optimizer, implementer)."""
    
    def get_prompt(self, agent_type: str) -> str:
        """Get prompt for content-generating agents."""
        prompts = {
            "analyzer": """
Analyze the job analysis output provided by the user and extract 3-4 KEY INSIGHTS that would be most valuable to show a user in real-time.

Focus on:
- Critical requirements or qualifications
- Technical skills needed
- Experience level required
- Unique aspects of the role

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "requirements", "message": "5+ years Python experience required"},
  {"category": "technical", "message": "Must know AWS, Docker, Kubernetes"}
]
""",
            "optimizer": """
Analyze the optimization strategy provided by the user and extract 3-4 KEY INSIGHTS about what changes will be made.

Focus on:
- Keywords being added
- Gaps being addressed
- Strengths being emphasized
- ATS improvements

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "keywords", "message": "Adding 'machine learning' and 'data pipeline' keywords"},
  {"category": "gaps", "message": "Addressing missing cloud architecture experience"}
]
""",
            "implementer": """
Analyze the implementation output provided by the user and extract 3-4 KEY INSIGHTS about what was changed.

Focus on:
- Sections modified
- Content added
- Formatting improvements
- Quantifiable changes

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "changes", "message": "Updated Experience and Skills sections"},
  {"category": "metrics", "message": "Added 5 technical keywords"}
]
"""
        }
        return prompts.get(agent_type, prompts["analyzer"])


class QualityInsightExtractor(BaseInsightExtractor):
    """Extract insights from quality-checking agents (validator, polish)."""
    
    def get_prompt(self, agent_type: str) -> str:
        """Get prompt for quality-checking agents."""
        prompts = {
            "validator": """
Analyze the validation output provided by the user and extract 2-3 KEY METRICS or SCORES about resume quality.

IGNORE any artifact references like "original version", "modified version", "document content".

Focus ONLY on:
- Numerical scores or percentages (ATS score, match %, compatibility)
- Specific strengths found (e.g., "Strong Python experience match")
- Critical gaps or recommendations (e.g., "Add more leadership examples")
- Overall assessment (e.g., "Excellent fit for senior role")

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "score", "message": "ATS compatibility: 92%"},
  {"category": "strength", "message": "Strong technical skills alignment"},
  {"category": "recommendation", "message": "Consider adding more metrics to achievements"}
]
""",
            "polish": """
Analyze the polish output provided by the user and extract 1-2 KEY IMPROVEMENTS made to the resume.

IGNORE any artifact references like "original version", "modified version", "document content".

Focus ONLY on:
- Specific formatting improvements (e.g., "Improved bullet point consistency")
- Readability enhancements (e.g., "Simplified technical jargon")
- Professional polish (e.g., "Enhanced action verbs throughout")
- Final quality assessment (e.g., "Resume now ATS-optimized and polished")

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "formatting", "message": "Standardized section headers and spacing"},
  {"category": "quality", "message": "Resume ready for submission"}
]
"""
        }
        return prompts.get(agent_type, prompts["validator"])


class InsightExtractor:
    """Main insight extractor that routes to specialized extractors."""
    
    def __init__(self):
        self.content_extractor = ContentInsightExtractor()
        self.quality_extractor = QualityInsightExtractor()
    
    async def extract_insights_async(self, agent_output: str, agent_type: str, max_insights: int = 4) -> List[Dict[str, str]]:
        """Extract key insights from agent output asynchronously."""
        
        # Route to appropriate extractor
        if agent_type in ["analyzer", "optimizer"]:
            extractor = self.content_extractor
        elif agent_type in ["implementer", "validator", "polish"]:
            extractor = self.quality_extractor
        else:
            extractor = self.content_extractor  # Default
        
        # Separate instruction (system prompt) from data (text_content)
        instruction = extractor.get_prompt(agent_type)
        content = agent_output[:3000]  # Limit to 3000 chars to keep it fast
        
        try:
            # Run in executor since the client is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._extract_sync,
                instruction,
                content,
                extractor.model
            )
            
            # Parse JSON response
            import json
            import re
            
            # Try to extract JSON array from response
            json_match = re.search(r'\[\s*\{.*?\}\s*\]', result, re.DOTALL)
            if json_match:
                insights_data = json.loads(json_match.group(0))
                return insights_data[:max_insights]
            else:
                # Fallback: parse as plain text
                return self._parse_fallback(result, max_insights)
                
        except Exception as e:
            print(f"⚠️ Insight extraction failed: {e}")
            return []
    
    def _extract_sync(self, instruction: str, content: str, model: str) -> str:
        """Synchronous extraction for executor."""
        result = ""
        try:
            # Use stream_completion: instruction goes to system, content goes to user
            for chunk in self.content_extractor.client.stream_completion(
                prompt=instruction,
                text_content=content,
                model=model,
                temperature=0.3,
                max_tokens=500,
            ):
                if isinstance(chunk, str):
                    result += chunk
        except StopIteration:
            pass
        return result
    
    def _parse_fallback(self, text: str, max_insights: int) -> List[Dict[str, str]]:
        """Fallback parser if JSON extraction fails."""
        import re
        
        insights = []
        # Look for bullet points or numbered items
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                clean_line = re.sub(r'^[-•*\d.]+\s*', '', line).strip()
                if len(clean_line) > 10 and len(clean_line) < 100:
                    insights.append({
                        "category": "insight",
                        "message": clean_line[:80]
                    })
                    if len(insights) >= max_insights:
                        break
        
        return insights


# Global instance
insight_extractor = InsightExtractor()
