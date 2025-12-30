#!/usr/bin/env python3
"""Test script for insight deduplication functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.streaming.insight_listener import (
    get_run_insights,
    cache_insight,
    is_novel_insight,
    get_previous_insights_text,
    clear_run_insights
)

def test_deduplication():
    """Test all deduplication functions."""
    print("🧪 Testing Insight Deduplication Functions\n")
    
    run_id = 'test_run_001'
    
    # Clean up any previous test data
    clear_run_insights(run_id)
    
    print("1️⃣ Test 1: Empty cache")
    insights = get_run_insights(run_id)
    print(f"   Cache empty: {len(insights) == 0}\n")
    
    print("2️⃣ Test 2: Cache insights")
    cache_insight(run_id, 'The job description requires 5+ years of Python experience.', 'Job Analyzer')
    cache_insight(run_id, 'Resume should highlight machine learning projects.', 'Resume Optimizer')
    insights = get_run_insights(run_id)
    print(f"   Cached {len(insights)} insights\n")
    
    print("3️⃣ Test 3: Check novelty detection")
    previous = get_run_insights(run_id)
    
    novel_insight = "The applicant has experience with AWS cloud services."
    duplicate_insight = "The job description requires 5+ years of Python experience."
    similar_insight = "Position requires Python programming expertise (5+ years)."
    
    print(f"   Novel insight: {is_novel_insight(novel_insight, previous)}")
    print(f"   Duplicate insight: {is_novel_insight(duplicate_insight, previous)}")
    print(f"   Similar insight (should be flagged): {is_novel_insight(similar_insight, previous)}\n")
    
    print("4️⃣ Test 4: Previous insights text formatting")
    text = get_previous_insights_text(run_id, limit=5)
    print(f"   Formatted text:\n   {text}\n")
    
    print("5️⃣ Test 5: Debug similarity calculation")
    def jaccard_similarity(text1: str, text2: str) -> float:
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    test_pairs = [
        (duplicate_insight, previous[0]["text"]),
        (similar_insight, previous[0]["text"]),
        (novel_insight, previous[0]["text"])
    ]
    
    for t1, t2 in test_pairs:
        similarity = jaccard_similarity(t1, t2)
        print(f"   Similarity '{t1[:30]}...' vs '{t2[:30]}...': {similarity:.2f}")
    
    print("\n✅ All tests completed!")
    
    # Cleanup
    clear_run_insights(run_id)

if __name__ == "__main__":
    test_deduplication()
