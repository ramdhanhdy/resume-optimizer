import { motion } from 'framer-motion';
import { ScoreCard, RequirementItem, Badge } from '../shared';

interface ValidationReport {
  overall_match_score: number;
  readiness_score_before: number;
  readiness_score_after: number;
  submission_recommendation: string;
  dimensional_scores: {
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
    presentation_quality: number;
    competitive_positioning: number;
  };
  key_strengths: string[];
  red_flags: Array<{
    severity: string;
    description: string;
  }>;
  quick_wins: string[];
  detailed_assessment: Array<{
    requirement: string;
    assessment: string;
  }>;
  fabrication_risks: string[];
}

interface ValidationDetailsTabProps {
  validationReport: ValidationReport;
}

export default function ValidationDetailsTab({ validationReport }: ValidationDetailsTabProps) {
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
      {/* Dimensional Scores */}
      <motion.section variants={itemVariants}>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Score Breakdown</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <ScoreCard
            title="Requirements Match"
            score={validationReport.dimensional_scores.requirements_match}
            size="medium"
            gradient
          />
          <ScoreCard
            title="ATS Optimization"
            score={validationReport.dimensional_scores.ats_optimization}
            size="medium"
            gradient
          />
          <ScoreCard
            title="Cultural Fit"
            score={validationReport.dimensional_scores.cultural_fit}
            size="medium"
            gradient
          />
          <ScoreCard
            title="Presentation"
            score={validationReport.dimensional_scores.presentation_quality}
            size="medium"
            gradient
          />
          <ScoreCard
            title="Competitive Edge"
            score={validationReport.dimensional_scores.competitive_positioning}
            size="medium"
            gradient
          />
        </div>
      </motion.section>

      {/* Readiness Scores */}
      <motion.section variants={itemVariants} className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4">Readiness Assessment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <div className="text-sm text-gray-600 mb-2">Before Optimization</div>
            <div className="text-3xl font-bold text-gray-400">
              {validationReport.readiness_score_before}/100
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-blue-100">
            <div className="text-sm text-gray-600 mb-2">After Optimization</div>
            <div className="text-3xl font-bold text-green-600">
              {validationReport.readiness_score_after}/100
            </div>
            <div className="text-xs text-green-600 font-medium mt-1">
              +{validationReport.readiness_score_after - validationReport.readiness_score_before} improvement
            </div>
          </div>
        </div>
        {validationReport.submission_recommendation && (
          <div className="mt-4 pt-4 border-t border-blue-200">
            <div className="text-sm font-medium text-blue-900">
              Recommendation: {validationReport.submission_recommendation}
            </div>
          </div>
        )}
      </motion.section>

      {/* Key Strengths */}
      {validationReport.key_strengths.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">Key Strengths</h2>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <ul className="space-y-3">
              {validationReport.key_strengths.map((strength, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                    {index + 1}
                  </span>
                  <span className="text-sm text-green-900">{strength}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}

      {/* Red Flags */}
      {validationReport.red_flags.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">Red Flags</h2>
            <Badge variant="danger" size="sm">{validationReport.red_flags.length}</Badge>
          </div>
          <div className="space-y-3">
            {validationReport.red_flags.map((flag, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-red-50 border border-red-200 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <Badge
                    variant={
                      flag.severity.toLowerCase() === 'high' ? 'danger' :
                      flag.severity.toLowerCase() === 'medium' ? 'warning' :
                      'default'
                    }
                    size="sm"
                  >
                    {flag.severity || 'MEDIUM'}
                  </Badge>
                  <p className="text-sm text-red-900 flex-1">{flag.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Fabrication Risk */}
      <motion.section variants={itemVariants}>
        <div className="flex items-center gap-2 mb-4">
          <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h2 className="text-xl font-bold text-gray-900">Fabrication Risk Check</h2>
        </div>
        {validationReport.fabrication_risks.length === 0 ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <svg className="w-16 h-16 text-green-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <p className="text-lg font-semibold text-green-900 mb-1">All Clear!</p>
            <p className="text-sm text-green-700">
              All claims in your resume are verified and grounded in your original resume.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {validationReport.fabrication_risks.map((risk, index) => (
              <div
                key={index}
                className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
              >
                <p className="text-sm text-yellow-900">{risk}</p>
              </div>
            ))}
          </div>
        )}
      </motion.section>

      {/* Quick Wins */}
      {validationReport.quick_wins.length > 0 && (
        <motion.section variants={itemVariants}>
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">Quick Wins Applied</h2>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <ul className="space-y-2">
              {validationReport.quick_wins.map((win, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-start gap-3 text-sm text-blue-900"
                >
                  <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{win}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        </motion.section>
      )}

      {/* Detailed Requirements Assessment */}
      {validationReport.detailed_assessment.length > 0 && (
        <motion.section variants={itemVariants}>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Detailed Requirements Coverage</h2>
          <div className="space-y-3">
            {validationReport.detailed_assessment.map((item, index) => (
              <RequirementItem
                key={index}
                requirement={item.requirement}
                status="covered"
                assessment={item.assessment}
                isRequired={false}
              />
            ))}
          </div>
        </motion.section>
      )}
    </motion.div>
  );
}
