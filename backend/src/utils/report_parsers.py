"""Report parsers to extract structured data from agent markdown outputs."""

import re
from typing import Dict, List, Optional, Any


def parse_job_analysis(text: str) -> Dict[str, Any]:
    """Parse Agent 1 (Job Analyzer) output into structured data.

    Args:
        text: Raw markdown output from Job Analyzer agent

    Returns:
        Structured dictionary with job analysis data
    """
    result = {
        "job_overview": "",
        "must_have_qualifications": [],
        "preferred_qualifications": [],
        "hidden_requirements": [],
        "ats_keywords": {
            "priority_1": [],
            "priority_2": [],
            "priority_3": []
        },
        "company_culture": [],
        "strategy_recommendations": [],
        "raw_text": text
    }

    # Extract job overview
    overview_match = re.search(
        r'## JOB OVERVIEW\s*(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if overview_match:
        result["job_overview"] = overview_match.group(1).strip()

    # Extract must-have qualifications
    must_have_match = re.search(
        r'## MUST-HAVE QUALIFICATIONS.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if must_have_match:
        items = re.findall(r'\*\s+[✓✗]?\s*(.*?)(?=\n\*|\n##|\Z)', must_have_match.group(1), re.DOTALL)
        result["must_have_qualifications"] = [item.strip() for item in items if item.strip()]

    # Extract preferred qualifications
    preferred_match = re.search(
        r'## PREFERRED QUALIFICATIONS.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if preferred_match:
        items = re.findall(r'\*\s+[✓✗]?\s*(.*?)(?=\n\*|\n##|\Z)', preferred_match.group(1), re.DOTALL)
        result["preferred_qualifications"] = [item.strip() for item in items if item.strip()]

    # Extract hidden requirements
    hidden_match = re.search(
        r'## HIDDEN REQUIREMENTS.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if hidden_match:
        items = re.findall(r'\*\s*(.*?)(?=\n\*|\n##|\Z)', hidden_match.group(1), re.DOTALL)
        result["hidden_requirements"] = [item.strip() for item in items if item.strip()]

    # Extract ATS keywords by priority
    for priority in [1, 2, 3]:
        keyword_match = re.search(
            rf'###? PRIORITY {priority}.*?\n(.*?)(?=###|\n##|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if keyword_match:
            # Extract keywords - they might be in lists or comma-separated
            keyword_text = keyword_match.group(1)
            # Try list format first
            list_items = re.findall(r'(?:^|\n)\s*[-*]\s*`?(.*?)`?(?=\n|$)', keyword_text)
            if list_items:
                result["ats_keywords"][f"priority_{priority}"] = [
                    item.strip() for item in list_items if item.strip()
                ]
            else:
                # Try comma-separated format
                keywords = [k.strip().strip('`') for k in keyword_text.split(',')]
                result["ats_keywords"][f"priority_{priority}"] = [k for k in keywords if k]

    # Extract company culture signals
    culture_match = re.search(
        r'## (?:COMPANY )?CULTURE.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if culture_match:
        items = re.findall(r'\*\s*(.*?)(?=\n\*|\n##|\Z)', culture_match.group(1), re.DOTALL)
        result["company_culture"] = [item.strip() for item in items if item.strip()]

    # Extract strategy recommendations
    strategy_match = re.search(
        r'## (?:RESUME )?STRATEGY.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if strategy_match:
        items = re.findall(r'\*\s*(.*?)(?=\n\*|\n##|\Z)', strategy_match.group(1), re.DOTALL)
        result["strategy_recommendations"] = [item.strip() for item in items if item.strip()]

    return result


def parse_optimization_strategy(text: str) -> Dict[str, Any]:
    """Parse Agent 2 (Resume Optimizer) output into structured data.

    Args:
        text: Raw markdown output from Resume Optimizer agent

    Returns:
        Structured dictionary with optimization strategy data
    """
    result = {
        "executive_summary": "",
        "gap_analysis": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": []
        },
        "section_recommendations": [],
        "keyword_strategy": [],
        "structural_changes": [],
        "raw_text": text
    }

    # Extract executive summary
    exec_match = re.search(
        r'## EXECUTIVE SUMMARY\s*(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if exec_match:
        result["executive_summary"] = exec_match.group(1).strip()

    # Extract gap analysis
    gap_match = re.search(
        r'## (?:PART 1: )?(?:STRATEGIC ASSESSMENT|GAP ANALYSIS)\s*(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if gap_match:
        gap_text = gap_match.group(1)

        # Extract strengths
        strengths_match = re.search(
            r'(?:###|^)\s*(?:Strengths|Strong Points).*?\n(.*?)(?=###|##|\Z)',
            gap_text,
            re.DOTALL | re.IGNORECASE
        )
        if strengths_match:
            items = re.findall(r'\*\s*(.*?)(?=\n\*|\n#|\Z)', strengths_match.group(1), re.DOTALL)
            result["gap_analysis"]["strengths"] = [item.strip() for item in items if item.strip()]

        # Extract weaknesses/gaps
        weakness_match = re.search(
            r'(?:###|^)\s*(?:Weaknesses?|Gaps?|Areas for Improvement).*?\n(.*?)(?=###|##|\Z)',
            gap_text,
            re.DOTALL | re.IGNORECASE
        )
        if weakness_match:
            items = re.findall(r'\*\s*(.*?)(?=\n\*|\n#|\Z)', weakness_match.group(1), re.DOTALL)
            result["gap_analysis"]["weaknesses"] = [item.strip() for item in items if item.strip()]

        # Extract opportunities
        opp_match = re.search(
            r'(?:###|^)\s*(?:Opportunities|Potential).*?\n(.*?)(?=###|##|\Z)',
            gap_text,
            re.DOTALL | re.IGNORECASE
        )
        if opp_match:
            items = re.findall(r'\*\s*(.*?)(?=\n\*|\n#|\Z)', opp_match.group(1), re.DOTALL)
            result["gap_analysis"]["opportunities"] = [item.strip() for item in items if item.strip()]

    # Extract section-by-section recommendations
    section_match = re.search(
        r'## (?:PART 2: )?(?:SECTION-BY-SECTION|DETAILED) RECOMMENDATIONS?\s*(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if section_match:
        # Look for subsections (###)
        sections = re.findall(
            r'###\s*(.*?)\n(.*?)(?=###|##|\Z)',
            section_match.group(1),
            re.DOTALL
        )
        for section_name, section_content in sections:
            recommendations = re.findall(
                r'\*\s*(.*?)(?=\n\*|\n#|\Z)',
                section_content,
                re.DOTALL
            )
            if recommendations:
                result["section_recommendations"].append({
                    "section": section_name.strip(),
                    "recommendations": [r.strip() for r in recommendations if r.strip()]
                })

    # Extract keyword strategy
    keyword_match = re.search(
        r'## (?:KEYWORD|ATS) (?:INTEGRATION|STRATEGY).*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if keyword_match:
        items = re.findall(r'\*\s*(.*?)(?=\n\*|\n##|\Z)', keyword_match.group(1), re.DOTALL)
        result["keyword_strategy"] = [item.strip() for item in items if item.strip()]

    # Extract structural changes
    struct_match = re.search(
        r'## (?:STRUCTURAL|FORMAT|LAYOUT) (?:CHANGES|RECOMMENDATIONS).*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if struct_match:
        items = re.findall(r'\*\s*(.*?)(?=\n\*|\n##|\Z)', struct_match.group(1), re.DOTALL)
        result["structural_changes"] = [item.strip() for item in items if item.strip()]

    return result


def parse_validation_report(text: str) -> Dict[str, Any]:
    """Parse Agent 4 (Validator) output into structured data.

    Args:
        text: Raw markdown output from Validator agent

    Returns:
        Structured dictionary with validation data
    """
    result = {
        "overall_match_score": 0,
        "readiness_score_before": 0,
        "readiness_score_after": 0,
        "submission_recommendation": "",
        "dimensional_scores": {
            "requirements_match": 0,
            "ats_optimization": 0,
            "cultural_fit": 0,
            "presentation_quality": 0,
            "competitive_positioning": 0
        },
        "key_strengths": [],
        "red_flags": [],
        "quick_wins": [],
        "detailed_assessment": [],
        "fabrication_risks": [],
        "raw_text": text
    }

    # Extract overall match score (handle bold markdown)
    score_match = re.search(
        r'Overall Match Score.*?(\d+)/\d+\s*\((\d+)%\)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if score_match:
        result["overall_match_score"] = int(score_match.group(2))

    # Extract readiness scores
    readiness_match = re.search(
        r'Readiness Score[:\s]*(\d+)/\d+.*?(?:\(Before[^\)]*\))?.*?/\s*(\d+)/\d+',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if readiness_match:
        result["readiness_score_before"] = int(readiness_match.group(1))
        result["readiness_score_after"] = int(readiness_match.group(2))

    # Extract submission recommendation
    rec_match = re.search(
        r'Submission Recommendation[:\s]*([^:\n]+)',
        text,
        re.IGNORECASE
    )
    if rec_match:
        result["submission_recommendation"] = rec_match.group(1).strip()

    # Extract dimensional scores
    dimensions = [
        ("requirements_match", r"Requirements Match"),
        ("ats_optimization", r"ATS Optimization"),
        ("cultural_fit", r"Cultural Fit"),
        ("presentation_quality", r"Presentation Quality"),
        ("competitive_positioning", r"Competitive Positioning")
    ]

    for key, pattern in dimensions:
        dim_match = re.search(
            rf'{pattern}[:\s]*(\d+)/\d+',
            text,
            re.IGNORECASE
        )
        if dim_match:
            result["dimensional_scores"][key] = int(dim_match.group(1))

    # Extract key strengths
    strengths_match = re.search(
        r'Key Strengths[:\s]*\n(.*?)(?=\n#|Key Weaknesses|Red Flags|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if strengths_match:
        items = re.findall(
            r'(?:^|\n)\s*\d+\.\s*(.*?)(?=\n\d+\.|\n#|\Z)',
            strengths_match.group(1),
            re.DOTALL
        )
        result["key_strengths"] = [item.strip() for item in items if item.strip()]

    # Extract red flags
    flags_match = re.search(
        r'## RED FLAGS.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if flags_match:
        items = re.findall(
            r'(?:^|\n)\s*(?:\d+\.|[-*])\s*(?:\[([^\]]+)\]\s*)?(.*?)(?=\n(?:\d+\.|-|\*)|##|\Z)',
            flags_match.group(1),
            re.DOTALL
        )
        for severity, content in items:
            if content.strip():
                result["red_flags"].append({
                    "severity": severity.strip() if severity else "medium",
                    "description": content.strip()
                })

    # Extract quick wins
    wins_match = re.search(
        r'## QUICK WINS.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if wins_match:
        items = re.findall(
            r'(?:^|\n)\s*(?:\d+\.|[-*])\s*(.*?)(?=\n(?:\d+\.|-|\*)|##|\Z)',
            wins_match.group(1),
            re.DOTALL
        )
        result["quick_wins"] = [item.strip() for item in items if item.strip()]

    # Extract fabrication risks
    fab_match = re.search(
        r'## FABRICATION RISK.*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if fab_match:
        fab_text = fab_match.group(1).strip()
        if "no fabrications" in fab_text.lower() or "all verified" in fab_text.lower():
            result["fabrication_risks"] = []
        else:
            items = re.findall(
                r'(?:^|\n)\s*(?:\d+\.|[-*])\s*(.*?)(?=\n(?:\d+\.|-|\*)|##|\Z)',
                fab_text,
                re.DOTALL
            )
            result["fabrication_risks"] = [item.strip() for item in items if item.strip()]

    # Extract detailed requirement assessment
    req_match = re.search(
        r'## (?:DETAILED )?REQUIREMENTS? (?:COVERAGE|ASSESSMENT).*?\n(.*?)(?=##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if req_match:
        # Look for requirement entries
        requirements = re.findall(
            r'(?:^|\n)\s*(?:\d+\.|[-*])\s*\*\*([^*]+)\*\*[:\s]*(.*?)(?=\n(?:\d+\.|-|\*\*)|##|\Z)',
            req_match.group(1),
            re.DOTALL
        )
        for req_name, req_content in requirements:
            result["detailed_assessment"].append({
                "requirement": req_name.strip(),
                "assessment": req_content.strip()
            })

    return result


def parse_all_reports(agent_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse all agent outputs into a structured reports object.

    Args:
        agent_outputs: List of agent output records from database

    Returns:
        Dictionary with parsed reports for all agents
    """
    reports = {
        "job_analysis": None,
        "optimization_strategy": None,
        "validation_report": None,
        "optimized_resume_text": None,
        "agent_costs": []
    }

    for output in agent_outputs:
        agent_number = output.get("agent_number")
        agent_name = output.get("agent_name")
        output_data = output.get("output_data", {})
        text = output_data.get("text", "")

        # Track costs
        reports["agent_costs"].append({
            "agent": agent_name,
            "agent_number": agent_number,
            "cost": output.get("cost", 0),
            "input_tokens": output.get("input_tokens", 0),
            "output_tokens": output.get("output_tokens", 0)
        })

        # Parse based on agent number
        if agent_number == 1:
            reports["job_analysis"] = parse_job_analysis(text)
        elif agent_number == 2:
            reports["optimization_strategy"] = parse_optimization_strategy(text)
        elif agent_number == 3:
            reports["optimized_resume_text"] = text
        elif agent_number == 4:
            reports["validation_report"] = parse_validation_report(text)

    return reports
