# Methodology

## 1. Objective

This document describes the methodology used to evaluate a multi-agent **AI Resume Optimizer** system in which multiple large language models (LLMs) can be plugged into each stage of a sequential pipeline.

The primary goals are to:

1. Compare alternative LLM configurations at each pipeline stage based on **human preferences**.
2. Assess the system's ability to produce **useful, tailored, and truthful** resumes aligned with job postings.
3. Build a reusable evaluation dataset **incrementally** from real usage, without requiring a pre-defined static test set.

---

## 2. System Under Evaluation

### 2.1 Pipeline Overview

The system consists of a sequential pipeline of five LLM-based agents:

1. **Profile Agent**
   Parses and structures the job seeker's profile (e.g., CV, career history, skills).

2. **Job Posting Agent**
   Analyzes the target job description, extracting requirements, responsibilities, and key qualifications.

3. **Resume Optimizer Agent**
   Generates a draft of an optimized resume tailored to the job posting and grounded in the user's profile.

4. **QA Agent (Quality & Integrity Check)**
   Acts as a gatekeeper. It checks the optimized resume for **fabricated or exaggerated claims**, inconsistencies, and misalignment with the original profile.

5. **Polish & Export Agent**
   Applies stylistic polish, enforces formatting, and produces the final resume in DOCX format, possibly via generated Python code that creates the document.

Each stage can be implemented by one of several LLM configurations (different models and/or prompts), which we refer to as **candidates** for that stage.

---

## 3. Evaluation Design

### 3.1 Live, Within-Subject Design

Evaluation is performed **live**, during normal usage of the system:

* A user provides:

  * A **job seeker profile** (textual CV, work experience, etc.).
  * A **job posting** (copy-pasted from real listings).
* The system runs the pipeline end-to-end for this input, but at selected stages it generates outputs from **multiple LLM candidates** in parallel.
* A human evaluator (often the developer or a domain-knowledgeable rater) is shown all candidate outputs for that stage and selects the best one.

This constitutes a **within-subject, repeated-measures** design:

* For a given scenario (profile + job posting), **all candidate models** for a stage are evaluated on **the same context**, and the evaluator compares them directly.
* This reduces variance due to scenario difficulty and increases statistical power.

### 3.2 Scenarios (Implicit Test Cases)

Each real run of the system is treated as a **scenario**:

* A scenario ( i ) consists of:

  * User profile ( P_i )
  * Job posting ( J_i )
  * The pipeline state (outputs of previous stages) at the time a stage is evaluated.

No static test set is defined up front. Instead:

* Scenarios are collected **organically** over time from real usage.
* All inputs, intermediate states, and human choices are logged.
* At analysis time, a snapshot of these logs is treated as the evaluation dataset.

### 3.3 Stages Evaluated

The evaluation framework is designed to be applicable to any stage, but in practice we focus on:

* **Resume Optimizer Stage**
  Where different LLMs generate alternative optimized resumes.

* **QA Stage**
  Where different LLMs generate alternative QA reports or judgments about the integrity and faithfulness of the resume.

Other stages (profile parsing, job analysis, polishing) can be included following the same procedure if desired.

---

## 4. Human Evaluation Protocol

### 4.1 Candidate Generation

For a chosen stage ( s ) in scenario ( i ):

1. The pipeline is run up to stage ( s ) using fixed configurations for earlier stages to produce standard **context**:

   * Parsed profile, parsed job requirements, and any other relevant intermediate outputs.

2. For stage ( s ), we define a set of **K LLM candidates**:

   * Each candidate corresponds to a distinct `model_id` (different model and/or prompt template).

3. Given the same context, all K candidates are queried in parallel, producing K alternative outputs:

   * For optimizer stage: K different resume drafts.
   * For QA stage: K different QA analyses / fabrication checks.

### 4.2 Randomization and Blinding

To reduce bias during human judgment:

* Candidate outputs are presented in **random order** for each scenario and stage.
* Model identities (`model_id`) are **hidden** from the evaluator; candidates are labeled only as "Option A / B / C…".
* The evaluator is instructed to judge only based on predefined criteria, not on assumed model quality.

### 4.3 Evaluation Criteria

The evaluator uses qualitative criteria specific to each stage:

* **Optimizer Stage Criteria (example)**

  * **Relevance & alignment:** How well the resume highlights skills and experience relevant to the job posting.
  * **Faithfulness:** No invented roles, skills, or credentials beyond the user's profile.
  * **Clarity & structure:** Readability, logical organization, professional tone.

* **QA Stage Criteria (example)**

  * **Detection of fabricated claims:** Correctly flags unsupported or exaggerated statements.
  * **Precision:** Avoids incorrectly flagging legitimate experience as false.
  * **Actionability:** Provides clear suggestions for fixing issues.

The exact criteria are documented and kept **constant** across scenarios to maintain construct validity.

### 4.4 Preference Collection

For each ( (scenario, stage) ):

* The evaluator:

  * Selects **one winner** among the K candidates (top choice).
  * Optionally provides a **full ranking** (1st, 2nd, 3rd, …).
  * Optionally annotates outputs with **tags** (e.g., "fabrication", "off-target", "too generic", "excellent structure").

The winning candidate output is adopted as the actual pipeline output for subsequent stages.

---

## 5. Data Logging

To enable rigorous analysis, the system logs all relevant data for each scenario.

### 5.1 Scenario-Level Logging

For each scenario ( i ):

* Unique `scenario_id`
* Timestamp of creation
* Raw or anonymized:

  * `user_profile`
  * `job_posting`

### 5.2 Stage-Level Logging

For each ( (scenario_id, stage_id) ):

* `stage_id` (e.g., `"profile_agent"`, `"job_agent"`, `"optimizer"`, `"qa"`, `"polish"`)
* `context` passed into that stage (serialized summary of prior outputs)

### 5.3 Candidate-Level Logging

For each candidate output:

* `candidate_id` (local label for UI, e.g., "A/B/C")
* `model_id` (actual LLM configuration: model name + prompt version)
* `output_text`
* Optional metadata (e.g., latency, token count, decoding parameters)

### 5.4 Human Judgment Logging

For each evaluated ( (scenario_id, stage_id) ):

* `chosen_candidate_id` (winner)
* Optional `ranking` (ordered list of candidate_ids)
* Optional numerical scores, e.g.:

  * `alignment_score` (1–5)
  * `faithfulness_score` (1–5)
  * `clarity_score` (1–5)
* Optional tags / comments (free text)

Over time, these logs constitute a **growing evaluation dataset** derived from real usage.

---

## 6. Metrics

### 6.1 Win Rate per Model and Stage

For each model ( m ) at stage ( s ):

* Let ( N_{m,s} ) be the number of scenarios where ( m ) was included as a candidate.
* Let ( W_{m,s} ) be the number of scenarios where ( m ) was selected as the winner.

The **win rate** is:

$$
\text{WinRate}_{m,s} = \frac{W_{m,s}}{N_{m,s}}
$$

This measures how often a model's output is preferred when it participates.

### 6.2 Pairwise Preference Probability

For any pair of models ( m ) and ( n ) at stage ( s ):

* Consider only scenarios where both ( m ) and ( n ) were present as candidates.
* Let ( W_{m \succ n} ) be the number of such scenarios where ( m ) is preferred to ( n ) (wins or higher rank).
* Let ( N_{m,n} ) be the total number of these shared scenarios.

The estimated probability that ( m ) is preferred over ( n ) is:

$$
\hat{P}(m \succ n) = \frac{W_{m \succ n}}{N_{m,n}}
$$

This supports detailed head-to-head comparisons.

### 6.3 Rating-Based Metrics (Optional)

If numerical ratings (e.g., 1–5 scales) are collected:

* Compute **mean scores** per model, per stage, per criterion, for example:

$$
\overline{S}_{m,s} = \frac{1}{N_{m,s}} \sum_{i=1}^{N_{m,s}} S_{m,s}^{(i)}
$$

where ( S_{m,s}^{(i)} ) is the score given to model ( m ) at stage ( s ) in scenario ( i ).

---

## 7. Statistical Analysis

### 7.1 Hypotheses

For each stage ( s ) and comparison between models ( m ) and ( n ):

* **Null hypothesis (H_0):**
  The two models are equally likely to be preferred:
  $$
  P(m \succ n) = 0.5
  $$

* **Alternative hypothesis (H_1):**
  Model ( m ) is preferred more often than ( n ):
  $$
  P(m \succ n) > 0.5
  $$

### 7.2 Sign / Binomial Tests for Pairwise Comparison

For pairwise comparisons:

* Use a **sign test** or **binomial test** on ( W_{m \succ n} ) successes out of ( N_{m,n} ) trials, assuming ( p = 0.5 ) under ( H_0 ).
* Report:

  * ( \hat{P}(m \succ n) )
  * p-value for the test
  * 95% confidence interval for ( \hat{P}(m \succ n) )

If the 95% CI lies entirely above 0.5 and p-value is below the chosen significance level (e.g., 0.05), we conclude that ( m ) is significantly preferred to ( n ).

### 7.3 Multi-Model Ranking (3+ Models)

When comparing three or more models simultaneously:

* Compute all pairwise preference probabilities ( \hat{P}(m \succ n) ).
* Optionally fit a **Bradley–Terry** model to obtain a latent **strength parameter** ( \theta_m ) for each model, where:

$$
P(m \succ n) = \frac{\exp(\theta_m)}{\exp(\theta_m) + \exp(\theta_n)}
$$

* Rank models by ( \theta_m ) and report estimated pairwise win probabilities.

### 7.4 Analysis of Rating Data (If Available)

If numerical scores are collected, additional analyses can include:

* **Paired t-tests** or **Wilcoxon signed-rank tests** on scores per scenario for two models.
* **Linear mixed-effects models** with:

  * Fixed effect: model
  * Random effects: scenario (and rater, if multiple raters are involved)

These models account for scenario-level difficulty and rater-level differences.

---

## 8. Validity and Limitations

### 8.1 Construct Validity

* Evaluation criteria are defined explicitly for each stage and remain consistent across scenarios.
* The focus on truthfulness (no fabricated claims) is aligned with the system's design goal of avoiding false advertising of job seekers.

### 8.2 Internal Validity

* Candidate order randomization and model identity blinding reduce common biases.
* Within-subject design (same scenario, multiple candidates) controls for scenario difficulty.

### 8.3 External Validity

* Scenarios are drawn from **real-world usage**, enhancing ecological validity.
* However, the dataset may be biased toward the types of job postings and profiles most frequently used by the system's initial users.

### 8.4 Reliability

* In early stages, a single evaluator may provide judgments; this can introduce subjectivity.
* For higher reliability, multiple evaluators can be used for a subset of scenarios and **inter-rater agreement** (e.g., Cohen's kappa) can be measured.

---

## 9. Ethical Considerations

* User profiles and resumes may contain sensitive personal information. All logged data should be:

  * Stored securely.
  * Anonymized or pseudonymized where possible.
  * Used only for evaluation and model improvement under appropriate consent.
* Particular care is taken to avoid encouraging or amplifying fabricated qualifications; the QA stage and evaluation criteria explicitly penalize such behavior.

---

This methodology supports both **pragmatic product iteration** (choosing which LLM configuration to deploy at each stage) and **research-grade analysis** (win rates, statistical tests, and documented validity considerations), even though the evaluation data is collected from live, organic usage rather than a pre-defined static benchmark.
