
import type { Insight, ResumeChange } from './types';

export const PROCESSING_PHASES: string[] = [
  "Analyzing",
  "Planning",
  "Writing",
  "Validating",
  "Finalizing",
];

export const PROCESSING_ACTIVITIES: string[] = [
  "Extracting required qualifications",
  "Identifying technical keywords",
  "Analyzing company culture signals",
  "Deconstructing job description",
  "Mapping skills to requirements",
  "Planning optimization strategy",
  "Rewriting experience bullets",
  "Quantifying achievements",
  "Tailoring professional summary",
  "Validating claim accuracy",
  "Cross-referencing skills",
  "Polishing final output",
];

export const MOCK_INSIGHTS: Insight[] = [
  { id: 1, text: "5+ years Python experience", category: "Required" },
  { id: 2, text: "Cross-functional collaboration", category: "Cultural Emphasis" },
  { id: 3, text: "Strategic planning expertise", category: "Keyword Emphasis" },
  { id: 4, text: "Fast-paced startup environment", category: "Cultural Fit" },
  { id: 5, text: "Leadership of 3+ people", category: "Nice to Have" },
  { id: 6, text: "Experience with cloud platforms (AWS, GCP)", category: "Technical Skill" },
];

export const MOCK_RESUME_DIFF: ResumeChange[] = [
    {
        id: 1,
        original: "Responsible for developing new features for the company's main product.",
        optimized: "Engineered and launched 5 major customer-facing features for a flagship product with 1M+ users, resulting in a 15% increase in user engagement.",
        reason: "Quantified achievements and used stronger action verbs to demonstrate impact, aligning with the job's focus on results-driven development."
    },
    {
        id: 2,
        original: "Worked with other teams to get projects done.",
        optimized: "Led cross-functional collaboration between Product, Design, and QA teams to deliver a complex project 2 weeks ahead of schedule.",
        reason: "Integrated keywords 'cross-functional collaboration' and specified the teams involved to directly address a key requirement in the job description."
    },
    {
        id: 3,
        original: "Fixed bugs and improved application performance.",
        optimized: "Improved application performance by 30% through targeted code refactoring and database query optimization, reducing server response time from 500ms to 350ms.",
        reason: "Provided specific metrics to substantiate claims of performance improvement, making the accomplishment more tangible and impressive."
    },
    {
        id: 4,
        original: "Managed a team of developers.",
        optimized: "Mentored a team of 4 junior developers, fostering a 25% improvement in team velocity and successfully promoting two members to mid-level roles.",
        reason: "This claim requires supporting documentation or context. Suggesting a more verifiable action like 'mentoring' improves authenticity.",
        validation: {
            level: 'warning',
            message: "This claim is strong but lacks specific evidence. Consider rephrasing to focus on verifiable actions unless you can provide specific management metrics.",
            suggestion: "Mentored a team of 4 junior developers, fostering skill growth and improving team velocity."
        }
    }
];
