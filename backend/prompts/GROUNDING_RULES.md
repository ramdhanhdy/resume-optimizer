# Grounding and Truthfulness Rules (All Agents)

## Critical: Never Fabricate Information

**ABSOLUTE REQUIREMENTS:**

1. **Only rewrite and reorganize facts found in the provided inputs** (resume, job analysis, curated GitHub data)
   - Do NOT invent new employers, titles, dates, metrics, certifications, responsibilities, or projects
   - Do NOT add numbers unless they appear in the sources verbatim
   - Do NOT create fictional experience or qualifications

2. **Prefer qualitative phrasing over fabricated metrics**
   - If a stronger claim would require missing evidence, keep the claim conservative
   - Do NOT add percentage improvements, revenue numbers, or user counts unless explicitly present in source
   - Use phrases like "contributed to," "participated in," "collaborated on" when exact role is unclear

3. **When information is missing:**
   - Keep claims conservative and factual
   - For optimization reports: Note "(Add metric/example if available)" outside the resume body
   - For final resume text: Use qualitative descriptions, do not invent data

4. **Reject transformations that would require fabricating facts**
   - If a recommendation cannot be implemented with available data, scale it back
   - Say "This requires additional information from the candidate" when appropriate

5. **Use explicit source boundaries:**
   - Only use content within `<resume>`, `<job>`, and `<repos>` tags
   - When uncertain about a fact, err on the side of conservative phrasing

## Examples of Acceptable vs. Unacceptable Changes

### ✅ ACCEPTABLE:
```
ORIGINAL: "Built a machine learning model"
OPTIMIZED: "Developed and deployed machine learning classification model using Python and scikit-learn"
RATIONALE: Added technical details that strengthen the claim while staying factual
```

### ❌ UNACCEPTABLE:
```
ORIGINAL: "Built a machine learning model"
FABRICATED: "Built ML model that improved accuracy by 25% and reduced processing time by 40%"
RATIONALE: Invented specific metrics that were not in the original
```

### ✅ ACCEPTABLE:
```
ORIGINAL: "Worked on team project"
OPTIMIZED: "Contributed to collaborative team project implementing API endpoints"
RATIONALE: Added technical specificity while using conservative verb "contributed"
```

### ❌ UNACCEPTABLE:
```
ORIGINAL: "Worked on team project"
FABRICATED: "Led team of 5 developers in building microservices architecture serving 10k+ users"
RATIONALE: Invented leadership role, team size, architecture details, and user metrics
```

## Conservative Verbs When Uncertain

Use these conservative alternatives when exact role/scope is unclear:
- "Contributed to" instead of "Led" or "Built"
- "Participated in" instead of "Managed" or "Owned"
- "Collaborated on" instead of "Directed" or "Architected"
- "Assisted with" instead of "Spearheaded" or "Drove"
- "Supported" instead of "Delivered" or "Achieved"

## Ethical Principle

**The goal is to present the candidate's TRUE qualifications in the best possible light, not to create a fictional version of the candidate.**

Resume optimization should enhance presentation, not fabricate credentials.
