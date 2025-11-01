Analyze the job analysis output provided by the user and extract 3-4 KEY INSIGHTS that would be most valuable to show a user in real-time.

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
