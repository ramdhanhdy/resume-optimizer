"""ScrapingDog LinkedIn Profile Scraper client.

Handles async 202 responses with polling for LinkedIn profile data.
"""

from __future__ import annotations

import os
import time
import re
from typing import Any, Dict, Optional

import requests


class ScrapingDogError(RuntimeError):
    """Raised when ScrapingDog cannot provide requested profile data."""


def _extract_linkedin_username(url_or_username: str) -> str:
    """Extract LinkedIn username from URL or return as-is if already a username.
    
    Handles formats like:
    - https://www.linkedin.com/in/username
    - https://linkedin.com/in/username/
    - linkedin.com/in/username
    - username (returned as-is)
    """
    url_or_username = url_or_username.strip()
    
    # Pattern to match LinkedIn profile URLs
    pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/([^/?\s]+)"
    match = re.search(pattern, url_or_username, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    # If no URL pattern matched, assume it's already a username
    # Remove any trailing slashes or whitespace
    return url_or_username.rstrip("/").strip()


def fetch_linkedin_profile(
    url_or_username: str,
    *,
    max_retries: int = 8,
    initial_delay: float = 30.0,
    max_delay: float = 60.0,
    use_premium: bool = True,
    use_fresh: bool = False,
) -> Dict[str, Any]:
    """Fetch LinkedIn profile data via ScrapingDog API.
    
    Handles async 202 responses by polling with exponential backoff.
    
    Args:
        url_or_username: LinkedIn profile URL or username (e.g., "ramdhanhdy" or 
                        "https://linkedin.com/in/ramdhanhdy")
        max_retries: Maximum number of retry attempts for 202 responses
        initial_delay: Initial delay in seconds before first retry (default 30s)
        max_delay: Maximum delay between retries (default 60s)
        use_premium: Use premium proxies for better success rate
        use_fresh: Force fresh scrape (slower but more up-to-date)
    
    Returns:
        Dict containing the LinkedIn profile data
        
    Raises:
        RuntimeError: When SCRAPINGDOG_API_KEY is missing
        ScrapingDogError: When API fails or returns unusable data
    """
    api_key = os.getenv("SCRAPINGDOG_API_KEY")
    if not api_key:
        raise RuntimeError(
            "SCRAPINGDOG_API_KEY is not set. Please add your ScrapingDog API key to the environment."
        )
    
    username = _extract_linkedin_username(url_or_username)
    if not username:
        raise ValueError("LinkedIn URL or username must be a non-empty string.")
    
    url = "https://api.scrapingdog.com/profile"
    params = {
        "api_key": api_key,
        "id": username,
        "type": "profile",
        "premium": str(use_premium).lower(),
        "webhook": "false",
        "fresh": str(use_fresh).lower(),
    }
    
    delay = initial_delay
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data:
                        raise ScrapingDogError(
                            "ScrapingDog returned empty data for the LinkedIn profile."
                        )
                    return data
                except ValueError as e:
                    raise ScrapingDogError(
                        f"ScrapingDog returned invalid JSON: {e}"
                    ) from e
            
            elif response.status_code == 202:
                # Job accepted but not ready yet
                if attempt < max_retries:
                    print(f"⏳ LinkedIn profile scraping in progress (attempt {attempt + 1}/{max_retries + 1}), "
                          f"waiting {delay:.0f}s...")
                    time.sleep(delay)
                    # Exponential backoff with cap
                    delay = min(delay * 1.5, max_delay)
                    continue
                else:
                    raise ScrapingDogError(
                        f"LinkedIn profile scraping timed out after {max_retries + 1} attempts. "
                        "The profile may be taking longer than expected to scrape."
                    )
            
            elif response.status_code == 401:
                raise ScrapingDogError(
                    "Invalid ScrapingDog API key. Please check your SCRAPINGDOG_API_KEY."
                )
            
            elif response.status_code == 429:
                raise ScrapingDogError(
                    "ScrapingDog rate limit exceeded. Please try again later or upgrade your plan."
                )
            
            else:
                raise ScrapingDogError(
                    f"ScrapingDog request failed with status code {response.status_code}: "
                    f"{response.text[:500]}"
                )
                
        except requests.RequestException as e:
            if attempt < max_retries:
                print(f"⚠️ Network error (attempt {attempt + 1}), retrying in {delay:.0f}s: {e}")
                time.sleep(delay)
                delay = min(delay * 1.5, max_delay)
                continue
            raise ScrapingDogError(
                f"Failed to connect to ScrapingDog API after {max_retries + 1} attempts: {e}"
            ) from e
    
    # Should not reach here, but just in case
    raise ScrapingDogError("Unexpected error in LinkedIn profile fetch loop.")


def format_profile_as_text(profile_data, max_chars: Optional[int] = 20_000) -> str:
    """Convert ScrapingDog profile JSON to readable text for the ProfileAgent.
    
    Args:
        profile_data: Raw JSON response from ScrapingDog (can be dict or list)
        max_chars: Optional character limit
        
    Returns:
        Formatted text representation of the profile
    """
    # ScrapingDog may return a list with the profile as first element
    if isinstance(profile_data, list):
        if not profile_data:
            return ""
        profile_data = profile_data[0]
    
    if not isinstance(profile_data, dict):
        return str(profile_data)[:max_chars] if max_chars else str(profile_data)
    
    parts = []
    
    # Basic info
    if profile_data.get("name"):
        parts.append(f"Name: {profile_data['name']}")
    if profile_data.get("headline"):
        parts.append(f"Headline: {profile_data['headline']}")
    if profile_data.get("location"):
        parts.append(f"Location: {profile_data['location']}")
    
    # About/Summary
    if profile_data.get("about"):
        parts.append(f"\n## About\n{profile_data['about']}")
    
    # Experience
    experience = profile_data.get("experience", [])
    if experience:
        parts.append("\n## Experience")
        for exp in experience:
            exp_parts = []
            if exp.get("title"):
                exp_parts.append(exp["title"])
            if exp.get("company"):
                exp_parts.append(f"at {exp['company']}")
            if exp.get("duration"):
                exp_parts.append(f"({exp['duration']})")
            if exp_parts:
                parts.append("- " + " ".join(exp_parts))
            if exp.get("description"):
                parts.append(f"  {exp['description']}")
    
    # Education
    education = profile_data.get("education", [])
    if education:
        parts.append("\n## Education")
        for edu in education:
            edu_parts = []
            if edu.get("school"):
                edu_parts.append(edu["school"])
            if edu.get("degree"):
                edu_parts.append(f"- {edu['degree']}")
            if edu.get("field"):
                edu_parts.append(f"in {edu['field']}")
            if edu_parts:
                parts.append("- " + " ".join(edu_parts))
    
    # Skills
    skills = profile_data.get("skills", [])
    if skills:
        parts.append("\n## Skills")
        if isinstance(skills[0], dict):
            skill_names = [s.get("name", str(s)) for s in skills]
        else:
            skill_names = skills
        parts.append(", ".join(skill_names[:50]))  # Limit to 50 skills
    
    # Certifications
    certifications = profile_data.get("certifications", [])
    if certifications:
        parts.append("\n## Certifications")
        for cert in certifications:
            if isinstance(cert, dict):
                cert_name = cert.get("name", str(cert))
                cert_org = cert.get("organization", "")
                parts.append(f"- {cert_name}" + (f" ({cert_org})" if cert_org else ""))
            else:
                parts.append(f"- {cert}")
    
    # Languages
    languages = profile_data.get("languages", [])
    if languages:
        parts.append("\n## Languages")
        if isinstance(languages[0], dict):
            lang_names = [l.get("name", str(l)) for l in languages]
        else:
            lang_names = languages
        parts.append(", ".join(lang_names))
    
    # Projects
    projects = profile_data.get("projects", [])
    if projects:
        parts.append("\n## Projects")
        for proj in projects:
            if isinstance(proj, dict):
                proj_name = proj.get("name", str(proj))
                proj_desc = proj.get("description", "")
                parts.append(f"- {proj_name}")
                if proj_desc:
                    parts.append(f"  {proj_desc}")
            else:
                parts.append(f"- {proj}")
    
    text = "\n".join(parts)
    
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    
    return text


def fetch_linkedin_profile_text(
    url_or_username: str,
    *,
    max_chars: Optional[int] = 20_000,
    max_retries: int = 8,
    initial_delay: float = 30.0,
) -> str:
    """Convenience function to fetch LinkedIn profile and return as formatted text.
    
    This is the main function to use as a drop-in replacement for Exa's fetch_public_page_text
    when fetching LinkedIn profiles.
    
    Args:
        url_or_username: LinkedIn profile URL or username
        max_chars: Optional character limit for output
        max_retries: Maximum retry attempts for 202 responses
        initial_delay: Initial delay before first retry
        
    Returns:
        Formatted text representation of the LinkedIn profile
    """
    profile_data = fetch_linkedin_profile(
        url_or_username,
        max_retries=max_retries,
        initial_delay=initial_delay,
    )
    return format_profile_as_text(profile_data, max_chars=max_chars)


__all__ = [
    "fetch_linkedin_profile",
    "fetch_linkedin_profile_text",
    "format_profile_as_text",
    "ScrapingDogError",
]
