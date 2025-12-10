## 1. Research questions & hypotheses

### Research Questions

* **RQ1 – Stage quality:**
  For a given pipeline stage on resume optimizer, which LLM configuration yields better outputs according to human preference?

* **RQ2 – Faithfulness (anti-fabrication):**
  At the QA stage, which LLM best detects or avoids fabricated claims?

* **RQ3 – End-to-end effect (optional later):**
  Do better stage-level preferences correlate with better final resumes?

### Hypotheses

null/alternative for stage s, comparing models A and B:
* **H₀:** $P(A \text{ is preferred over } B) = 0.5$
* **H₁:** $P(A \text{ is preferred over } B) > 0.5$

## 2. Experimental Design

### 2.1 Sampling (Scenario Selection)

Each scenario (single pipeline run) is a job seeker profile + job posting.

For each scenario and stage *s*:
- generate K candidate outputs from different LLMN configs
- developer choose the best (or rank them)

pseudo-code:
for 
---