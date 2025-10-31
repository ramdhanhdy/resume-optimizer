#!/usr/bin/env python3
"""Test script for page estimation functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.page_controller import PageEstimator

def test_page_estimation():
    """Test the page estimation with sample resume data."""
    
    # Sample resume data for testing
    sample_resume = {
        'sections': [
            {
                'title': 'EDUCATION',
                'items': [
                    {
                        'title': 'Bachelor of Science in Computer Science',
                        'location': 'University Name, City',
                        'subtitle': 'GPA: 3.8/4.0',
                        'dates': 'Aug 2020 - May 2024',
                        'bullets': [
                            'Relevant coursework: Data Structures, Algorithms, Machine Learning',
                            'Dean\'s List for 6 semesters',
                            'Teaching Assistant for Computer Science courses'
                        ]
                    }
                ]
            },
            {
                'title': 'EXPERIENCE',
                'items': [
                    {
                        'title': 'Software Engineer Intern',
                        'location': 'Tech Company, City',
                        'subtitle': 'Software Engineering Team',
                        'dates': 'Jun 2023 - Aug 2023',
                        'bullets': [
                            'Developed and maintained web applications using React and Node.js',
                            'Collaborated with cross-functional teams to deliver features on time',
                            'Improved application performance by 30% through optimization',
                            'Participated in code reviews and agile development processes'
                        ]
                    },
                    {
                        'title': 'Research Assistant',
                        'location': 'University Lab, City',
                        'subtitle': 'Machine Learning Research',
                        'dates': 'Jan 2023 - May 2023',
                        'bullets': [
                            'Conducted research on natural language processing techniques',
                            'Implemented and evaluated machine learning models',
                            'Co-authored research paper submitted to international conference'
                        ]
                    }
                ]
            },
            {
                'title': 'SKILLS',
                'items': [
                    {
                        'title': 'Technical Skills',
                        'bullets': [
                            'Programming Languages: Python, JavaScript, Java, C++',
                            'Technologies: React, Node.js, TensorFlow, Git',
                            'Languages: English (Native), Spanish (Basic)'
                        ]
                    }
                ]
            }
        ]
    }
    
    # Test page estimation
    estimated_pages = PageEstimator.estimate_resume_pages(sample_resume)
    print(f"Estimated pages for sample resume: {estimated_pages:.1f}")
    
    # Based on your feedback, actual pages are 1.3-1.5, let's use 1.4 as average
    actual_pages = 1.4
    calibration_factor = PageEstimator.calibrate_estimation(estimated_pages, actual_pages)
    print(f"Actual pages (from your testing): {actual_pages:.1f}")
    print(f"Calibration factor needed: {calibration_factor:.2f}")
    
    # Test spacing adjustment calculation
    if actual_pages > 2.0:
        adjustment = PageEstimator.calculate_spacing_adjustment(actual_pages, 2.0)
        print("\nRecommended spacing adjustments (to fit 2 pages):")
        for key, value in adjustment.items():
            print(f"  {key}: {value}")
    elif actual_pages < 2.0:
        adjustment = PageEstimator.calculate_spacing_adjustment(actual_pages, 2.0)
        print("\nRecommended spacing adjustments (to fill 2 pages):")
        for key, value in adjustment.items():
            print(f"  {key}: {value}")
    else:
        print("\nResume is already estimated to fit 2 pages perfectly!")
    
    # Test text line estimation
    sample_text = "This is a sample bullet point that demonstrates how the line estimation works for longer text content that might wrap to multiple lines."
    estimated_lines = PageEstimator.estimate_text_lines(sample_text)
    print(f"\nSample text: '{sample_text}'")
    print(f"Estimated lines: {estimated_lines:.1f}")

if __name__ == "__main__":
    test_page_estimation()
