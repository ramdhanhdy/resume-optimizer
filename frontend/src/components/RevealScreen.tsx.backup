
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BackArrowIcon, DownloadIcon, InfoIcon, WarningIcon } from './icons';
import ExportModal from './ExportModal';

interface RevealScreenProps {
  onRestart: () => void;
  applicationId: number;
  scores?: {
    overall: number;
    requirements_match: number;
    ats_optimization: number;
    cultural_fit: number;
  };
}

interface ResumeSection {
  id: string;
  title: string;
  original: string;
  optimized: string;
  changes: SectionChange[];
}

interface SectionChange {
  id: number;
  type: 'added' | 'modified' | 'removed';
  original?: string;
  optimized?: string;
  reason?: string;
  validation?: {
    level: 'warning';
    message: string;
    suggestion: string;
  };
}

interface PopoverProps {
  change: SectionChange;
  onClose: () => void;
}

const ChangePopover: React.FC<PopoverProps> = ({ change, onClose }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute z-50 w-80 max-w-[calc(100vw-4rem)] bg-white rounded-lg shadow-lg border border-border-subtle p-4 top-full mt-2 right-0 text-sm"
            onClick={(e) => e.stopPropagation()}
        >
            <h3 className="font-semibold mb-2 text-text-main">Why this changed</h3>
            <p className="text-text-main/90">{change.reason}</p>
        </motion.div>
    );
};

const ValidationPopover: React.FC<PopoverProps> = ({ change, onClose }) => {
    if (!change.validation) return null;
    return (
        <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute z-50 w-80 max-w-[calc(100vw-4rem)] bg-white rounded-lg shadow-lg border border-border-subtle p-4 top-full mt-2 right-0 text-sm"
            onClick={(e) => e.stopPropagation()}
        >
            <div className="flex items-start">
                <WarningIcon className="w-5 h-5 text-warning mr-2 flex-shrink-0 mt-0.5" />
                <div>
                    <h3 className="font-semibold text-warning mb-2">Needs Evidence</h3>
                    <p className="text-text-main/90 mb-3">{change.validation.message}</p>
                    <div className="bg-surface-dark p-2 rounded-md">
                        <p className="text-xs text-text-main/70 mb-1">Suggested revision:</p>
                        <p className="font-mono text-xs">"{change.validation.suggestion}"</p>
                    </div>
                    <div className="flex justify-end space-x-2 mt-3">
                         <button className="text-xs font-medium text-text-main/70 px-2 py-1 rounded hover:bg-surface-dark">Dismiss</button>
                         <button className="text-xs font-medium bg-primary text-white px-2 py-1 rounded">Accept</button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};


const RevealScreen: React.FC<RevealScreenProps> = ({ onRestart, applicationId, scores }) => {
    const [isExportModalOpen, setExportModalOpen] = useState(false);
    const [activePopover, setActivePopover] = useState<number | null>(null);
    const [sections, setSections] = useState<ResumeSection[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [actualScores, setActualScores] = useState(scores);
    const overallScore = actualScores?.overall || scores?.overall || 0;

    const togglePopover = (id: number) => {
        setActivePopover(prev => (prev === id ? null : id));
    };

    useEffect(() => {
        const handleClickOutside = () => setActivePopover(null);
        window.addEventListener('click', handleClickOutside);
        return () => window.removeEventListener('click', handleClickOutside);
    }, []);

    // Parse resume sections from text
    const parseResumeSections = (text: string): Map<string, string> => {
        const sections = new Map<string, string>();
        const lines = text.split('\n');
        let currentSection = 'Header';
        let currentContent: string[] = [];
        
        // Common section headers (case-insensitive)
        const sectionHeaders = [
            'professional summary', 'summary', 'objective',
            'work experience', 'experience', 'employment history',
            'education', 'academic background',
            'skills', 'technical skills', 'core competencies',
            'projects', 'key projects',
            'certifications', 'licenses',
            'awards', 'achievements',
            'publications', 'research'
        ];
        
        for (const line of lines) {
            const trimmed = line.trim();
            const lowerLine = trimmed.toLowerCase();
            
            // Check if this line is a section header
            const isHeader = sectionHeaders.some(header => {
                // Match if line is exactly the header or starts with it
                return lowerLine === header || 
                       (lowerLine.startsWith(header) && trimmed.length < 50);
            });
            
            if (isHeader && trimmed.length > 0) {
                // Save previous section
                if (currentContent.length > 0) {
                    sections.set(currentSection, currentContent.join('\n').trim());
                }
                // Start new section
                currentSection = trimmed;
                currentContent = [];
            } else if (trimmed.length > 0) {
                currentContent.push(line);
            }
        }
        
        // Save last section
        if (currentContent.length > 0) {
            sections.set(currentSection, currentContent.join('\n').trim());
        }
        
        return sections;
    };

    // Group changes by matching them to sections
    const groupChangesBySection = (changes: any[], originalText: string, optimizedText: string): ResumeSection[] => {
        const originalSections = parseResumeSections(originalText);
        const optimizedSections = parseResumeSections(optimizedText);
        
        const sections: ResumeSection[] = [];
        const usedChanges = new Set<number>();
        
        // Match sections between original and optimized
        for (const [sectionTitle, optimizedContent] of optimizedSections.entries()) {
            const originalContent = originalSections.get(sectionTitle) || '';
            
            // Find changes that belong to this section
            const sectionChanges: SectionChange[] = [];
            
            for (const change of changes) {
                if (usedChanges.has(change.id)) continue;
                
                // Check if this change belongs to this section
                const changeText = change.optimized || change.original || '';
                if (optimizedContent.includes(changeText.trim())) {
                    sectionChanges.push({
                        id: change.id,
                        type: !change.original ? 'added' : !change.optimized ? 'removed' : 'modified',
                        original: change.original,
                        optimized: change.optimized,
                        reason: change.reason,
                        validation: change.validation,
                    });
                    usedChanges.add(change.id);
                }
            }
            
            sections.push({
                id: `section-${sections.length}`,
                title: sectionTitle,
                original: originalContent,
                optimized: optimizedContent,
                changes: sectionChanges,
            });
        }
        
        return sections;
    };

    useEffect(() => {
        const loadApplicationData = async () => {
            try {
                const { apiClient } = await import('../services/api');
                const [diffResponse, appData] = await Promise.all([
                    apiClient.getApplicationDiff(applicationId),
                    apiClient.getApplication(applicationId)
                ]);
                
                if (diffResponse.success && appData) {
                    // Get original and optimized resume texts
                    const originalText = appData.original_resume_text || '';
                    const optimizedText = appData.optimized_resume_text || '';
                    
                    if (diffResponse.changes && originalText && optimizedText) {
                        const groupedSections = groupChangesBySection(
                            diffResponse.changes,
                            originalText,
                            optimizedText
                        );
                        setSections(groupedSections);
                    }
                    
                    if (diffResponse.scores) {
                        setActualScores(diffResponse.scores);
                    }
                }
                
                setIsLoading(false);
            } catch (error) {
                console.error('Failed to load application data:', error);
                setIsLoading(false);
            }
        };

        if (applicationId) {
            loadApplicationData();
        }
    }, [applicationId]);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
            className="min-h-screen flex flex-col"
        >
            {/* Header with Score */}
            <header className="fixed top-0 left-0 right-0 bg-background-main/95 backdrop-blur-md border-b border-border-subtle z-10">
                <div className="px-8 py-4">
                    <div className="flex items-center justify-between mb-4">
                        <button onClick={onRestart} className="flex items-center text-sm font-medium text-text-main/80 hover:text-text-main transition-colors">
                            <BackArrowIcon className="w-5 h-5 mr-1" /> Back
                        </button>
                        <button onClick={() => setExportModalOpen(true)} className="flex items-center bg-accent text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-accent/90 transition-all shadow-sm hover:shadow-md">
                            Download <DownloadIcon className="w-4 h-4 ml-2" />
                        </button>
                    </div>
                    
                    {/* Score Cards */}
                    <div className="grid grid-cols-4 gap-4">
                        <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-xl p-4 border border-accent/20">
                            <div className="flex items-baseline gap-2 mb-1">
                                <span className="text-4xl font-bold text-accent">{overallScore}</span>
                                <span className="text-lg text-text-main/60">/ 100</span>
                            </div>
                            <p className="text-xs font-medium text-text-main/70 uppercase tracking-wide">Overall Match</p>
                        </div>
                        
                        <div className="bg-surface-light rounded-xl p-4 border border-border-subtle">
                            <div className="text-2xl font-bold text-text-main mb-1">{actualScores?.requirements_match || 0}%</div>
                            <p className="text-xs font-medium text-text-main/70 uppercase tracking-wide">Requirements</p>
                        </div>
                        
                        <div className="bg-surface-light rounded-xl p-4 border border-border-subtle">
                            <div className="text-2xl font-bold text-text-main mb-1">{actualScores?.ats_optimization || 0}%</div>
                            <p className="text-xs font-medium text-text-main/70 uppercase tracking-wide">ATS Score</p>
                        </div>
                        
                        <div className="bg-surface-light rounded-xl p-4 border border-border-subtle">
                            <div className="text-2xl font-bold text-text-main mb-1">{actualScores?.cultural_fit || 0}%</div>
                            <p className="text-xs font-medium text-text-main/70 uppercase tracking-wide">Cultural Fit</p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-grow pt-44 px-8 pb-8">
                {/* Before/After Comparison */}
                <div className="grid grid-cols-2 gap-6">
                    {/* Original Column */}
                    <div className="relative">
                        <div className="sticky top-44 z-20 bg-surface-dark border-b border-border-subtle px-6 py-4 rounded-t-xl">
                            <h2 className="text-sm font-semibold uppercase tracking-wide text-text-main/60">Original</h2>
                        </div>
                        <div className="bg-surface-dark rounded-b-xl border border-border-subtle border-t-0">
                            <div className="p-6 max-h-[calc(100vh-240px)] overflow-y-auto">
                                {isLoading ? (
                                    <div className="text-text-main/70">Loading...</div>
                                ) : (
                                    <div className="space-y-8">
                                        {sections.map(section => (
                                            <div key={section.id} className="space-y-3">
                                                <h3 className="text-xs font-bold uppercase tracking-wider text-text-main/50 mb-3">
                                                    {section.title}
                                                </h3>
                                                <div className="bg-surface-light/5 rounded-lg p-5 border border-border-subtle/30">
                                                    <p className="text-sm text-text-main/80 leading-relaxed whitespace-pre-wrap">
                                                        {section.original || <span className="italic text-text-main/40">Not in original</span>}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Optimized Column */}
                    <div className="relative">
                        <div className="sticky top-44 z-20 bg-white border-b border-border-subtle px-6 py-4 rounded-t-xl">
                            <h2 className="text-sm font-semibold uppercase tracking-wide text-text-main/80">Optimized</h2>
                        </div>
                        <div className="bg-surface-light rounded-b-xl border border-border-subtle border-t-0 shadow-sm">
                            <div className="p-6 max-h-[calc(100vh-240px)] overflow-y-auto">
                                {isLoading ? (
                                    <div className="text-text-main/70">Loading...</div>
                                ) : (
                                    <div className="space-y-8">
                                        {sections.map(section => (
                                            <div key={section.id} className="space-y-3">
                                                <div className="flex items-center justify-between mb-3">
                                                    <h3 className="text-xs font-bold uppercase tracking-wider text-text-main/70">
                                                        {section.title}
                                                    </h3>
                                                    <span className="text-xs text-accent font-medium">
                                                        {section.changes.length} {section.changes.length === 1 ? 'change' : 'changes'}
                                                    </span>
                                                </div>
                                                <div className="bg-white rounded-lg border border-border-subtle hover:border-accent/20 transition-all">
                                                    {/* Show individual changes inline */}
                                                    {section.changes.length > 0 ? (
                                                        <div className="divide-y divide-border-subtle/30">
                                                            {section.changes.map((change, idx) => (
                                                                <div key={change.id} className="relative p-5">
                                                                    <div className="text-sm text-text-main leading-relaxed">
                                                                        <span className="whitespace-pre-wrap">
                                                                            {change.optimized || <span className="italic text-text-main/40">Removed</span>}
                                                                        </span>
                                                                        {change.reason && (
                                                                            <span className="relative inline-block ml-1 align-middle">
                                                                                <button
                                                                                    onClick={(e) => {e.stopPropagation(); togglePopover(change.id)}}
                                                                                    className="text-text-main/40 hover:text-accent transition-colors"
                                                                                    title="Why this changed"
                                                                                >
                                                                                    <InfoIcon className="w-3.5 h-3.5" />
                                                                                </button>
                                                                                
                                                                                <AnimatePresence>
                                                                                    {activePopover === change.id && (
                                                                                        change.validation ? 
                                                                                            <ValidationPopover change={change} onClose={() => setActivePopover(null)} /> : 
                                                                                            <ChangePopover change={change} onClose={() => setActivePopover(null)} />
                                                                                    )}
                                                                                </AnimatePresence>
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    ) : (
                                                        <div className="p-5">
                                                            <p className="text-sm text-text-main leading-relaxed whitespace-pre-wrap">
                                                                {section.optimized || <span className="italic text-text-main/40">Removed</span>}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <AnimatePresence>
                {isExportModalOpen && (
                    <ExportModal 
                        onRestart={onRestart} 
                        onClose={() => setExportModalOpen(false)} 
                        applicationId={applicationId}
                    />
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default RevealScreen;
