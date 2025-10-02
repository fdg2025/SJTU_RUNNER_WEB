'use client';

interface ProgressBarProps {
  current: number;
  total: number;
  message?: string;
  className?: string;
}

export default function ProgressBar({ current, total, message, className = '' }: ProgressBarProps) {
  const percentage = total > 0 ? Math.min((current / total) * 100, 100) : 0;

  return (
    <div className={`space-y-2 ${className}`}>
      {message && (
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">{message}</span>
          <span className="text-gray-500 font-mono">
            {current}/{total} ({Math.round(percentage)}%)
          </span>
        </div>
      )}
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
