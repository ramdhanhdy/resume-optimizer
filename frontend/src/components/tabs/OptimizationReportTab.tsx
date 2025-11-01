import { motion } from 'framer-motion';
import { Badge } from '../shared';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface OptimizationStrategy {
  executive_summary: string;
  gap_analysis: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
  };
  section_recommendations: Array<{
    section: string;
    recommendations: string[];
  }>;
  keyword_strategy: string[];
  structural_changes: string[];
}

interface OptimizationReportTabProps {
  optimizationStrategy: OptimizationStrategy;
}

export default function OptimizationReportTab({ optimizationStrategy }: OptimizationReportTabProps) {
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
      {/* Executive Summary */}
      {optimizationStrategy.executive_summary && (
        <motion.section variants={itemVariants} className="bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Executive Summary</h2>
          <div className="text-gray-700 leading-relaxed prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {optimizationStrategy.executive_summary}
            </ReactMarkdown>
          </div>
        </motion.section>
      )}

      {/* Section-by-Section Recommendations */}
      {optimizationStrategy.section_recommendations.length > 0 && (
        <motion.section variants={itemVariants}>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Section-by-Section Recommendations</h2>
          <div className="space-y-4">
            {optimizationStrategy.section_recommendations.map((section, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white border border-gray-200 rounded-lg p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="primary" size="sm">{section.section}</Badge>
                </div>
                <ul className="space-y-2">
                  {section.recommendations.map((rec, recIndex) => (
                    <li key={recIndex} className="text-sm text-gray-700 leading-relaxed flex items-start gap-2">
                      <span className="text-blue-600 font-bold">→</span>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{rec}</ReactMarkdown>
                      </div>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Keyword Integration Strategy */}
      {optimizationStrategy.keyword_strategy.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">Keyword Integration Strategy</h2>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-5">
            <ul className="space-y-2">
              {optimizationStrategy.keyword_strategy.map((strategy, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-purple-900"
                >
                  <svg className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{strategy}</ReactMarkdown>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}

      {/* Structural Changes */}
      {optimizationStrategy.structural_changes.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">Structural & Formatting Changes</h2>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
            <ul className="space-y-2">
              {optimizationStrategy.structural_changes.map((change, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-gray-800"
                >
                  <svg className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{change}</ReactMarkdown>
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
