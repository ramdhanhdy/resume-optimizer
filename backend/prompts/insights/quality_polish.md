Analyze the polish output provided by the user and extract 1-2 KEY IMPROVEMENTS made to the resume.

IGNORE any artifact references like "original version", "modified version", "document content".

Focus ONLY on:
- Specific formatting improvements (e.g., "Improved bullet point consistency")
- Readability enhancements (e.g., "Simplified technical jargon")
- Professional polish (e.g., "Enhanced action verbs throughout")
- Final quality assessment (e.g., "Resume now ATS-optimized and polished")

Format: Return ONLY a JSON array of objects with 'category' and 'message' fields.
Keep each message under 80 characters.

Example output:
[
  {"category": "formatting", "message": "Standardized section headers and spacing"},
  {"category": "quality", "message": "Resume ready for submission"}
]
