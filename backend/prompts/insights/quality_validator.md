Analyze the validation output provided by the user and extract 2-3 KEY METRICS or SCORES about resume quality.

IGNORE any artifact references like "original version", "modified version", "document content".

Focus ONLY on real observations from the text:
- Numerical scores or percentages (ATS score, match %, compatibility) if present
- Specific strengths found based on the job match
- Critical gaps or recommendations based on the actual analysis
- Overall assessment

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

CRITICAL: DO NOT output generic placeholder examples. Read the provided text and extract the ACTUAL metrics and scores found.

Example format (do NOT copy these exact strings, write your own based on the text):
[
  {"category": "score", "message": "ATS compatibility: 92%"},
  {"category": "strength", "message": "Strong technical skills alignment"},
  {"category": "recommendation", "message": "Consider adding more metrics to achievements"}
]
