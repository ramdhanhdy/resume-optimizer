"""Utility for parsing resume differences and generating structured diffs."""

import re
import difflib
from typing import List, Dict, Tuple, Optional, Any


def extract_bullets(text: str) -> List[str]:
    """Extract bullet points and sentences from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        List of bullet points/sentences
    """
    bullets = []
    
    # Split by newlines and process each line
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines, section headers, and contact info
        if not line:
            continue
        if line.isupper() and len(line) < 50:  # Section headers
            continue
        if '@' in line or 'linkedin.com' in line.lower():  # Contact info
            continue
        if re.match(r'^[A-Z][a-z]+ \d{4}', line):  # Date lines
            continue
            
        # Remove bullet point markers
        line = re.sub(r'^[•\-\*]\s*', '', line)
        
        # Skip very short lines (likely headers or labels)
        if len(line) < 20:
            continue
            
        bullets.append(line)
    
    return bullets


def match_bullets(original_bullets: List[str], optimized_bullets: List[str]) -> List[Tuple[Optional[str], Optional[str], float]]:
    """Match corresponding bullets between original and optimized versions.
    
    Uses fuzzy string matching to pair related bullets.
    
    Args:
        original_bullets: List of original bullet points
        optimized_bullets: List of optimized bullet points
        
    Returns:
        List of (original, optimized, similarity_score) tuples
    """
    matches = []
    used_optimized = set()
    
    for orig in original_bullets:
        best_match = None
        best_score = 0.0
        best_idx = -1
        
        for idx, opt in enumerate(optimized_bullets):
            if idx in used_optimized:
                continue
                
            # Calculate similarity using SequenceMatcher
            similarity = difflib.SequenceMatcher(None, orig.lower(), opt.lower()).ratio()
            
            # Also check for common keywords
            orig_words = set(re.findall(r'\b\w+\b', orig.lower()))
            opt_words = set(re.findall(r'\b\w+\b', opt.lower()))
            keyword_overlap = len(orig_words & opt_words) / max(len(orig_words), 1)
            
            # Combined score
            combined_score = (similarity * 0.7) + (keyword_overlap * 0.3)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = opt
                best_idx = idx
        
        # Only match if similarity is above threshold
        if best_score > 0.3:
            matches.append((orig, best_match, best_score))
            used_optimized.add(best_idx)
        else:
            # Original bullet was removed or heavily changed
            matches.append((orig, None, 0.0))
    
    # Add any optimized bullets that weren't matched (new additions)
    for idx, opt in enumerate(optimized_bullets):
        if idx not in used_optimized:
            matches.append((None, opt, 0.0))
    
    return matches


def extract_change_reasons(optimization_report: str) -> Dict[str, str]:
    """Extract reasons for changes from the optimization report.
    
    Looks for patterns like:
    - "CURRENT: ... → OPTIMIZED: ... (REASON: ...)"
    - Bullet point changes with explanations
    
    Args:
        optimization_report: The optimization strategy/report text
        
    Returns:
        Dictionary mapping (snippet of) optimized text to reason
    """
    reasons = {}
    
    if not optimization_report:
        return reasons
    
    # Pattern 1: CURRENT → OPTIMIZED format with reason
    pattern1 = r'CURRENT:?\s*["\']?(.+?)["\']?\s*(?:→|->|OPTIMIZED:)\s*["\']?(.+?)["\']?\s*(?:REASON:|because|to)\s*(.+?)(?:\n|$)'
    matches1 = re.finditer(pattern1, optimization_report, re.IGNORECASE | re.DOTALL)
    
    for match in matches1:
        optimized = match.group(2).strip()
        reason = match.group(3).strip()
        # Use first 50 chars as key
        key = optimized[:50].lower()
        reasons[key] = reason[:200]  # Limit reason length
    
    # Pattern 2: Bullet points with explanations
    pattern2 = r'[-•]\s*(.{20,200}?)\s*[-–—]\s*(.{20,200}?)(?:\n|$)'
    matches2 = re.finditer(pattern2, optimization_report)
    
    for match in matches2:
        text = match.group(1).strip()
        explanation = match.group(2).strip()
        if len(explanation) > 15 and not explanation.startswith('http'):
            key = text[:50].lower()
            if key not in reasons:
                reasons[key] = explanation[:200]
    
    return reasons


def find_reason_for_change(original: str, optimized: str, reasons: Dict[str, str]) -> str:
    """Find the most relevant reason for a specific change.
    
    Args:
        original: Original bullet text
        optimized: Optimized bullet text
        reasons: Dictionary of extracted reasons
        
    Returns:
        Reason string or generic fallback
    """
    # Try to match optimized text to reasons
    for key, reason in reasons.items():
        if key in optimized.lower()[:50]:
            return reason
    
    # Generic reasons based on common patterns
    if any(word in optimized.lower() for word in ['quantified', 'increased', 'improved', '%']):
        return "Added quantifiable metrics to demonstrate measurable impact and results."
    
    if any(word in optimized.lower() for word in ['led', 'managed', 'orchestrated', 'spearheaded']):
        return "Used stronger action verbs to emphasize leadership and initiative."
    
    if len(optimized) > len(original) * 1.3:
        return "Expanded with specific details and business context to strengthen the accomplishment."
    
    if any(word in optimized.lower() for word in ['cross-functional', 'collaboration', 'stakeholder']):
        return "Highlighted collaboration and teamwork to align with job requirements."
    
    return "Optimized phrasing to better align with job requirements and improve ATS compatibility."


def extract_validation_warnings(validation_report: str, optimized_text: str) -> Dict[str, Dict[str, str]]:
    """Extract validation warnings for specific bullets.
    
    Args:
        validation_report: The validator agent output
        optimized_text: The full optimized resume text
        
    Returns:
        Dictionary mapping bullet snippets to validation warnings
    """
    warnings = {}
    
    if not validation_report:
        return warnings
    
    # Look for warning patterns in validation report
    # Pattern: mentions of "needs evidence", "requires verification", "claim unsupported"
    warning_patterns = [
        r'(?:warning|concern|flag).*?["\'](.{20,150}?)["\'].*?(?:needs|requires|lacks)\s+(.{20,200}?)(?:\n|$)',
        r'["\'](.{20,150}?)["\'].*?(?:unsupported|unverified|needs evidence).*?(?:suggestion:|recommend:)\s*(.{20,200}?)(?:\n|$)',
    ]
    
    for pattern in warning_patterns:
        matches = re.finditer(pattern, validation_report, re.IGNORECASE | re.DOTALL)
        for match in matches:
            bullet_text = match.group(1).strip()
            issue = match.group(2).strip()
            
            key = bullet_text[:50].lower()
            warnings[key] = {
                'message': issue[:200],
                'suggestion': f'Consider providing specific evidence or metrics to support this claim.'
            }
    
    return warnings


def generate_resume_diff(
    original_text: str,
    optimized_text: str,
    optimization_report: str = "",
    validation_report: str = ""
) -> List[Dict[str, Any]]:
    """Generate structured diff of resume changes.
    
    Args:
        original_text: Original resume text
        optimized_text: Optimized resume text
        optimization_report: Strategy/reasons from optimizer agent
        validation_report: Warnings from validator agent
        
    Returns:
        List of change objects with original, optimized, reason, and optional validation
    """
    original_bullets = extract_bullets(original_text)
    optimized_bullets = extract_bullets(optimized_text)
    
    matches = match_bullets(original_bullets, optimized_bullets)
    reasons = extract_change_reasons(optimization_report)
    warnings = extract_validation_warnings(validation_report, optimized_text)
    
    changes = []
    change_id = 1
    
    for orig, opt, score in matches:
        # Skip if both are None (shouldn't happen)
        if not orig and not opt:
            continue
        
        # Skip if they're identical
        if orig and opt and orig.strip() == opt.strip():
            continue
        
        # Handle removed bullets (original but no optimized)
        if orig and not opt:
            # Don't show removed bullets in the diff
            continue
        
        # Handle new bullets (optimized but no original)
        if opt and not orig:
            reason = find_reason_for_change("", opt, reasons)
            changes.append({
                'id': change_id,
                'original': '(New addition)',
                'optimized': opt,
                'reason': reason
            })
            change_id += 1
            continue
        
        # Handle modified bullets
        reason = find_reason_for_change(orig, opt, reasons)
        
        change_obj = {
            'id': change_id,
            'original': orig,
            'optimized': opt,
            'reason': reason
        }
        
        # Check for validation warnings
        opt_key = opt[:50].lower()
        if opt_key in warnings or any(key in opt_key for key in warnings.keys()):
            for key, warning in warnings.items():
                if key in opt_key:
                    change_obj['validation'] = {
                        'level': 'warning',
                        'message': warning['message'],
                        'suggestion': warning['suggestion']
                    }
                    break
        
        changes.append(change_obj)
        change_id += 1
    
    return changes
