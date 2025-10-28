
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BackArrowIcon, CheckIcon, DownloadIcon, InfoIcon, WarningIcon } from './icons';
import type { ResumeChange } from '../types';
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

interface PopoverProps {
  change: ResumeChange;
  onClose: () => void;
}

const ChangePopover: React.FC<PopoverProps> = ({ change, onClose }) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute z-20 w-80 bg-surface-light rounded-lg shadow-subtle border border-border-subtle p-4 right-full mr-4 text-sm"
            onClick={(e) => e.stopPropagation()}
        >
            <h3 className="font-semibold mb-2">Why this changed</h3>
            <p className="text-text-main/90">{change.reason}</p>
        </motion.div>
    );
};

const ValidationPopover: React.FC<PopoverProps> = ({ change, onClose }) => {
    if (!change.validation) return null;
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute z-20 w-80 bg-surface-light rounded-lg shadow-subtle border border-border-subtle p-4 right-full mr-4 text-sm"
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
    const [resumeChanges, setResumeChanges] = useState<ResumeChange[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [actualScores, setActualScores] = useState(scores);

    const overallScore = actualScores?.overall || scores?.overall || 0;

    const beforeRef = useRef<HTMLDivElement>(null);
    const afterRef = useRef<HTMLDivElement>(null);
    const isSyncing = useRef(true);

    const handleScroll = (source: 'before' | 'after') => {
        if (!isSyncing.current) return;
        isSyncing.current = false;
        const sourceEl = source === 'before' ? beforeRef.current : afterRef.current;
        const targetEl = source === 'before' ? afterRef.current : beforeRef.current;
        if (sourceEl && targetEl) {
            targetEl.scrollTop = sourceEl.scrollTop;
        }
        setTimeout(() => { isSyncing.current = true; }, 50);
    };

    const togglePopover = (id: number) => {
        setActivePopover(prev => (prev === id ? null : id));
    };

    useEffect(() => {
        const handleClickOutside = () => setActivePopover(null);
        window.addEventListener('click', handleClickOutside);
        return () => window.removeEventListener('click', handleClickOutside);
    }, []);

    useEffect(() => {
        const loadApplicationData = async () => {
            try {
                const { apiClient } = await import('../services/api');
                const response = await apiClient.getApplicationDiff(applicationId);
                
                if (response.success) {
                    if (response.changes) {
                        setResumeChanges(response.changes);
                    }
                    // Update scores from API if available
                    if (response.scores) {
                        setActualScores(response.scores);
                    }
                }
                
                setIsLoading(false);
            } catch (error) {
                console.error('Failed to load application data:', error);
                // Fall back to mock data on error
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
            <header className="fixed top-0 left-0 right-0 bg-background-main/80 backdrop-blur-sm border-b border-border-subtle z-10 h-16 flex items-center justify-between px-8">
                <button onClick={onRestart} className="flex items-center text-sm font-medium text-text-main/80 hover:text-text-main">
                    <BackArrowIcon className="w-5 h-5 mr-1" /> Back
                </button>
                <div className="text-center">
                    <div className="flex items-center">
                        {overallScore > 0 ? (
                            <>
                                <span className="text-3xl font-semibold tracking-tight">{overallScore}%</span>
                                <CheckIcon className="w-5 h-5 ml-2 text-green-500" title="All claims verified" />
                            </>
                        ) : (
                            <span className="text-2xl font-medium text-text-main/50">Calculating...</span>
                        )}
                    </div>
                    <p className="text-xs text-text-main/70 -mt-1">Job Match</p>
                </div>
                <button onClick={() => setExportModalOpen(true)} className="flex items-center bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors">
                    Download <DownloadIcon className="w-4 h-4 ml-2" />
                </button>
            </header>

            <main className="flex-grow pt-16 grid grid-cols-2">
                <div className="bg-surface-dark">
                    <div className="p-8 sticky top-16">
                        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-main/60">Before</h2>
                    </div>
                    <div ref={beforeRef} onScroll={() => handleScroll('before')} className="p-8 pt-0 overflow-y-auto h-[calc(100vh-128px)]">
                        {isLoading ? (
                            <div className="text-text-main/70">Loading...</div>
                        ) : (
                            <ul className="space-y-6 list-disc list-inside text-text-main/80 leading-relaxed">
                                {resumeChanges.map(change => <li key={change.id}>{change.original}</li>)}
                            </ul>
                        )}
                    </div>
                </div>

                <div className="bg-surface-light shadow-subtle">
                    <div className="p-8 sticky top-16">
                        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-main/80">After</h2>
                    </div>
                     <div ref={afterRef} onScroll={() => handleScroll('after')} className="p-8 pt-0 overflow-y-auto h-[calc(100vh-128px)]">
                        {isLoading ? (
                            <div className="text-text-main/70">Loading...</div>
                        ) : (
                            <ul className="space-y-6 list-disc list-inside text-text-main leading-relaxed">
                                {resumeChanges.map(change => (
                                <li key={change.id} className="relative">
                                    {change.optimized}
                                    <div className="absolute -left-8 top-1/2 -translate-y-1/2 flex items-center">
                                       {change.validation ? (
                                           <button onClick={(e) => {e.stopPropagation(); togglePopover(change.id)}} className="p-1 rounded-full hover:bg-warning/20">
                                               <div className="w-2 h-2 rounded-full bg-warning"></div>
                                           </button>
                                       ) : (
                                            <button onClick={(e) => {e.stopPropagation(); togglePopover(change.id)}} className="p-1 group">
                                                 <InfoIcon className="w-4 h-4 text-text-main/30 group-hover:text-primary transition-colors" />
                                            </button>
                                       )}
                                    </div>
                                    <AnimatePresence>
                                        {activePopover === change.id && (
                                            change.validation ? <ValidationPopover change={change} onClose={() => setActivePopover(null)} /> : <ChangePopover change={change} onClose={() => setActivePopover(null)} />
                                        )}
                                    </AnimatePresence>
                                </li>
                            ))}
                            </ul>
                        )}
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
