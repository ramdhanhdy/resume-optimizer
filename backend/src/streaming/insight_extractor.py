"""Parallel insight extraction using lightweight LLM."""

import asyncio
from typing import List, Dict, Optional
from src.api.client_factory import create_client
from src.utils.prompt_loader import load_prompt


class BaseInsightExtractor:
    """Base class for insight extraction."""
    
    def __init__(self, model: str = None):
        import os
        from src.server import INSIGHT_MODEL
        
        self.client = create_client()
        self.model = model or INSIGHT_MODEL
    
    def get_prompt(self, agent_type: str) -> str:
        """Override in subclasses to provide specific prompts."""
        raise NotImplementedError


class ContentInsightExtractor(BaseInsightExtractor):
    """Extract insights from content-generating agents (analyzer, optimizer, implementer)."""
    
    def get_prompt(self, agent_type: str) -> str:
        """Get prompt for content-generating agents."""
        file_map = {
            "analyzer": "content_analyzer.md",
            "optimizer": "content_optimizer.md",
            "implementer": "content_implementer.md",
        }
        filename = file_map.get(agent_type, file_map["analyzer"])
        return load_prompt("insights", filename)


class QualityInsightExtractor(BaseInsightExtractor):
    """Extract insights from quality-checking agents (validator, polish)."""
    
    def get_prompt(self, agent_type: str) -> str:
        """Get prompt for quality-checking agents."""
        file_map = {
            "validator": "quality_validator.md",
            "polish": "quality_polish.md",
        }
        filename = file_map.get(agent_type, file_map["validator"])
        return load_prompt("insights", filename)


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
