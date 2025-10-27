
import React from 'react';
import { motion } from 'framer-motion';

interface ExportModalProps {
  onClose: () => void;
  onRestart: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ onClose, onRestart }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.3, ease: [0.4, 0.0, 0.2, 1] }}
        className="bg-surface-light rounded-lg shadow-subtle w-full max-w-sm p-8 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-semibold mb-6">Your Resume is Ready</h2>
        
        <div className="space-y-3">
          <button className="w-full bg-accent text-white h-12 rounded-lg font-medium text-sm hover:bg-accent/90 transition-colors">
            Download as PDF
          </button>
          <button className="w-full bg-surface-light border border-border-subtle h-12 rounded-lg font-medium text-sm hover:bg-surface-dark transition-colors">
            Download as DOCX
          </button>
        </div>

        <button onClick={onRestart} className="text-sm text-primary font-medium mt-6">
          Start new application
        </button>
      </motion.div>
    </motion.div>
  );
};

export default ExportModal;
