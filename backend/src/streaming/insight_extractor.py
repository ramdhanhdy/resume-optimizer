"""Parallel insight extraction using lightweight LLM."""

import asyncio
from typing import List, Dict, Optional
from src.api.client_factory import create_client


class InsightExtractor:
    """Extract concise insights from agent outputs using Gemini Flash Lite."""
    
    def __init__(self):
        self.client = create_client()
        self.model = "zenmux::inclusionai/ring-mini-2.0"  # Fast and cheap via zenmux
    
    async def extract_insights_async(self, agent_output: str, agent_type: str, max_insights: int = 4) -> List[Dict[str, str]]:
        """Extract key insights from agent output asynchronously."""
        
        # Define prompts per agent type
        prompts = {
            "analyzer": """
Analyze this job analysis output and extract 3-4 KEY INSIGHTS that would be most valuable to show a user in real-time.

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

Job Analysis Output:
""",
            "optimizer": """
Analyze this optimization strategy and extract 3-4 KEY INSIGHTS about what changes will be made.

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

Optimization Strategy:
""",
            "implementer": """
Analyze this implementation output and extract 3-4 KEY INSIGHTS about what was changed.

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

Implementation Output:
""",
            "validator": """
Analyze this validation report and extract 3-4 KEY INSIGHTS about the resume quality.

Focus on:
- Scores and ratings
- Strengths identified
- Areas for improvement
- Match quality

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "score", "message": "ATS compatibility: 92%"},
  {"category": "strength", "message": "Strong technical skills alignment"}
]

Validation Report:
""",
            "polish": """
Analyze this polish output and extract 2-3 KEY INSIGHTS about final improvements.

Focus on:
- Formatting enhancements
- Final touches
- Quality improvements

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "formatting", "message": "Improved section headers and spacing"},
  {"category": "quality", "message": "Enhanced readability and flow"}
]

Polish Output:
"""
        }
        
        prompt = prompts.get(agent_type, prompts["analyzer"])
        full_prompt = prompt + "\n" + agent_output[:3000]  # Limit to 3000 chars to keep it fast
        
        try:
            # Run in executor since the client is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._extract_sync,
                full_prompt
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
    
    def _extract_sync(self, prompt: str) -> str:
        """Synchronous extraction for executor."""
        result = ""
        try:
            # Use stream_completion which is the correct method for MultiProviderClient
            for chunk in self.client.stream_completion(
                prompt=prompt,
                model=self.model,
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
