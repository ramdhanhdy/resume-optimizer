import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  fullScreen?: boolean;
  message?: string;
}

export default function LoadingSpinner({ fullScreen = false, message }: LoadingSpinnerProps) {
  if (fullScreen) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#FAF9F6] via-[#F5F3EE] to-[#EEF2F1]">
        <Loader2 className="w-8 h-8 animate-spin text-accent mb-4" />
        {message && <p className="text-text-main/60">{message}</p>}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <Loader2 className="w-6 h-6 animate-spin text-accent mb-2" />
      {message && <p className="text-sm text-text-main/60">{message}</p>}
    </div>
  );
}
