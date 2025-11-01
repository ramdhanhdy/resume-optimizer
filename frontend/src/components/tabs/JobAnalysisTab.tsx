import { motion } from 'framer-motion';
import { KeywordChip, Badge } from '../shared';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface JobAnalysis {
  job_overview: string;
  must_have_qualifications: string[];
  preferred_qualifications: string[];
  hidden_requirements: string[];
  ats_keywords: {
    priority_1: string[];
    priority_2: string[];
    priority_3: string[];
  };
  company_culture: string[];
  strategy_recommendations: string[];
}

interface JobAnalysisTabProps {
  jobAnalysis: JobAnalysis;
}

export default function JobAnalysisTab({ jobAnalysis }: JobAnalysisTabProps) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 pb-8"
    >
      {/* Job Overview */}
      {jobAnalysis.job_overview && (
        <motion.section variants={itemVariants} className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Job Overview</h2>
          <div className="text-gray-700 leading-relaxed prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {jobAnalysis.job_overview}
            </ReactMarkdown>
          </div>
        </motion.section>
      )}

      {/* Requirements Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Must-Have Qualifications */}
        {jobAnalysis.must_have_qualifications.length > 0 && (
          <motion.section variants={itemVariants}>
            <div className="flex items-center gap-2 mb-4">
              <Badge variant="danger" size="md">MUST-HAVE</Badge>
              <h3 className="text-lg font-bold text-gray-900">Required Qualifications</h3>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-5">
              <ul className="space-y-3">
                {jobAnalysis.must_have_qualifications.map((qual, index) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3"
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded bg-red-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                      ✓
                    </span>
                    <div className="text-sm text-red-900 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{qual}</ReactMarkdown>
                    </div>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.section>
        )}

        {/* Preferred Qualifications */}
        {jobAnalysis.preferred_qualifications.length > 0 && (
          <motion.section variants={itemVariants}>
            <div className="flex items-center gap-2 mb-4">
              <Badge variant="primary" size="md">PREFERRED</Badge>
              <h3 className="text-lg font-bold text-gray-900">Bonus Qualifications</h3>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
              <ul className="space-y-3">
                {jobAnalysis.preferred_qualifications.map((qual, index) => (
                  <motion.li
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3"
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                      +
                    </span>
                    <div className="text-sm text-blue-900 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{qual}</ReactMarkdown>
                    </div>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.section>
        )}
      </div>

      {/* Hidden Requirements */}
      {jobAnalysis.hidden_requirements.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <Badge variant="info" size="md">HIDDEN</Badge>
            <h3 className="text-lg font-bold text-gray-900">Inferred Requirements</h3>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-5">
            <p className="text-xs text-purple-700 mb-3 font-medium">
              These requirements weren't explicitly stated but are likely expected based on the job description.
            </p>
            <ul className="space-y-3">
              {jobAnalysis.hidden_requirements.map((req, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <svg className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-purple-900 prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{req}</ReactMarkdown>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}

      {/* ATS Keywords */}
      <motion.section variants={itemVariants}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">ATS Keywords by Priority</h2>

        <div className="space-y-4">
          {/* Priority 1 */}
          {jobAnalysis.ats_keywords.priority_1.length > 0 && (
            <div className="bg-gradient-to-r from-red-50 to-white border border-red-200 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="danger" size="sm">PRIORITY 1</Badge>
                <span className="text-xs text-red-700 font-medium">Critical - Must Include</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {jobAnalysis.ats_keywords.priority_1.map((keyword, index) => (
                  <KeywordChip key={index} keyword={keyword} priority={1} covered={true} />
                ))}
              </div>
            </div>
          )}

          {/* Priority 2 */}
          {jobAnalysis.ats_keywords.priority_2.length > 0 && (
            <div className="bg-gradient-to-r from-blue-50 to-white border border-blue-200 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="primary" size="sm">PRIORITY 2</Badge>
                <span className="text-xs text-blue-700 font-medium">Important - Include When Possible</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {jobAnalysis.ats_keywords.priority_2.map((keyword, index) => (
                  <KeywordChip key={index} keyword={keyword} priority={2} covered={true} />
                ))}
              </div>
            </div>
          )}

          {/* Priority 3 */}
          {jobAnalysis.ats_keywords.priority_3.length > 0 && (
            <div className="bg-gradient-to-r from-purple-50 to-white border border-purple-200 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="info" size="sm">PRIORITY 3</Badge>
                <span className="text-xs text-purple-700 font-medium">Nice to Have - Bonus Points</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {jobAnalysis.ats_keywords.priority_3.map((keyword, index) => (
                  <KeywordChip key={index} keyword={keyword} priority={3} covered={true} />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-600">
            <strong>Note:</strong> These keywords were identified by analyzing the job posting and comparing with industry standards.
            Your optimized resume includes relevant keywords where they naturally fit your experience.
          </p>
        </div>
      </motion.section>

      {/* Company Culture */}
      {jobAnalysis.company_culture.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="text-lg font-bold text-gray-900">Company Culture Signals</h3>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-5">
            <ul className="space-y-2">
              {jobAnalysis.company_culture.map((signal, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-green-900"
                >
                  <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-green-900 prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{signal}</ReactMarkdown>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}

      {/* Strategy Recommendations */}
      {jobAnalysis.strategy_recommendations.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <h3 className="text-lg font-bold text-gray-900">Resume Strategy</h3>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
            <ul className="space-y-3">
              {jobAnalysis.strategy_recommendations.map((rec, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                    {index + 1}
                  </span>
                  <div className="text-sm text-blue-900 prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{rec}</ReactMarkdown>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}
    </motion.div>
  );
}
