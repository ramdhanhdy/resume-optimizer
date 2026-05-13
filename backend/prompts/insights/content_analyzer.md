Analyze the job analysis provided by the user and extract 3-4 KEY INSIGHTS about the target role.

Focus ONLY on real requirements observed in the text:
- Core technical or hard skills required
- Required years of experience or seniority level
- Key soft skills or cultural traits desired
- Priority keywords or tools mentioned

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

CRITICAL: DO NOT output generic placeholder examples. Read the provided text and extract the ACTUAL requirements of the job.

Example format (do NOT copy these exact strings, write your own based on the text):
[
  {"category": "skill", "message": "Heavy emphasis on distributed systems and Go"},
  {"category": "requirement", "message": "Requires 5+ years of backend engineering"}
]
