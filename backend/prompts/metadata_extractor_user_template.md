Extract the company name and job title from the following job posting. Return ONLY a JSON object with this exact structure:

{
  "company_name": "the company/organization name",
  "job_title": "the job title/position"
}

If you cannot find the company name or job title, use "Unknown Company" or "Unknown Position" respectively.

Job Posting:
{{JOB_POSTING}}
