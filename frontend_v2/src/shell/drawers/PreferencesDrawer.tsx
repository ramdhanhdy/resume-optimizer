import { useState, useEffect } from 'react';
import { Loader2, AlertCircle, Save, Trash2, Link as LinkIcon, FileText } from 'lucide-react';
import { Drawer } from './Drawer';
import { getUserPreferences, updateUserPreferences, listSavedResumes, deleteSavedResume } from '@/lib/api';
import type { SavedResume } from '@/types/api';
import { cn } from '@/lib/cn';

interface PreferencesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PreferencesDrawer({ isOpen, onClose }: PreferencesDrawerProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [linkedin, setLinkedin] = useState('');
  const [github, setGithub] = useState('');
  const [resumes, setResumes] = useState<SavedResume[]>([]);

  useEffect(() => {
    if (!isOpen) return;
    
    let cancelled = false;
    setLoading(true);
    setError(null);
    
    Promise.all([
      getUserPreferences(),
      listSavedResumes()
    ])
      .then(([prefsRes, resumesRes]) => {
        if (cancelled) return;
        setLinkedin(prefsRes.preferences?.default_linkedin_url || '');
        setGithub(prefsRes.preferences?.default_github_username || '');
        setResumes(resumesRes.resumes || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load preferences');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
      
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await updateUserPreferences({
        default_linkedin_url: linkedin || undefined,
        default_github_username: github || undefined
      });
      // Give a little visual feedback on save
      setSaving(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preferences');
      setSaving(false);
    }
  };

  const handleDeleteResume = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return;
    try {
      await deleteSavedResume(id);
      setResumes(r => r.filter(x => x.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete resume');
    }
  };

  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="Settings">
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-600">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-ink-400" />
        </div>
      ) : (
        <div className="space-y-8">
          <section>
            <h3 className="mb-4 text-sm font-semibold text-ink-900 flex items-center gap-2">
              <LinkIcon className="h-4 w-4 text-ink-400" /> Defaults
            </h3>
            <form onSubmit={handleSavePreferences} className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-ink-600">LinkedIn URL</label>
                <input
                  type="url"
                  value={linkedin}
                  onChange={e => setLinkedin(e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className={cn(
                    'w-full rounded-xl bg-white/50 px-3 py-2 text-sm text-ink-900',
                    'ring-1 ring-ink-200/50 focus:outline-none focus:ring-2 focus:ring-sky-300'
                  )}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-ink-600">GitHub Username</label>
                <input
                  type="text"
                  value={github}
                  onChange={e => setGithub(e.target.value)}
                  placeholder="e.g. octocat"
                  className={cn(
                    'w-full rounded-xl bg-white/50 px-3 py-2 text-sm text-ink-900',
                    'ring-1 ring-ink-200/50 focus:outline-none focus:ring-2 focus:ring-sky-300'
                  )}
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className={cn(
                  'flex w-full items-center justify-center gap-2 rounded-xl bg-ink-900 px-4 py-2',
                  'text-sm font-medium text-white transition hover:bg-ink-700 disabled:opacity-50'
                )}
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Defaults
              </button>
            </form>
          </section>

          <section>
            <h3 className="mb-4 text-sm font-semibold text-ink-900 flex items-center gap-2">
              <FileText className="h-4 w-4 text-ink-400" /> Base Resumes
            </h3>
            {resumes.length === 0 ? (
              <p className="text-sm text-ink-500">No base resumes saved yet.</p>
            ) : (
              <ul className="space-y-3">
                {resumes.map(r => (
                  <li key={r.id} className="flex items-center justify-between rounded-xl bg-white/50 p-3 ring-1 ring-ink-200/50">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-ink-900 line-clamp-1">{r.label}</span>
                      <span className="text-xs text-ink-400 line-clamp-1">{r.filename || 'Pasted text'}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteResume(r.id)}
                      className="rounded p-1.5 text-red-400 transition hover:bg-red-50 hover:text-red-600"
                      title="Delete resume"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </Drawer>
  );
}
