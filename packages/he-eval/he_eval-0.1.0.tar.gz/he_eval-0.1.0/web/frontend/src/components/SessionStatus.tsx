import { useState, useEffect } from 'react';
import { Clock, Play, Pause, CheckCircle } from 'lucide-react';
import type { Session } from '../types';
import clsx from 'clsx';

interface SessionStatusProps {
  session: Session;
}

const statusConfig = {
  created: { label: 'Created', icon: Clock, color: 'text-gray-600 bg-gray-100' },
  in_progress: { label: 'In Progress', icon: Play, color: 'text-blue-600 bg-blue-100' },
  paused: { label: 'Paused', icon: Pause, color: 'text-yellow-600 bg-yellow-100' },
  submitted: { label: 'Submitted', icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  cancelled: { label: 'Cancelled', icon: Clock, color: 'text-red-600 bg-red-100' },
};

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}h ${mins}m ${secs}s`;
  }
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

function useLiveTimer(session: Session): number {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Calculate initial elapsed time
    const calculateElapsed = () => {
      if (!session.started_at) return 0;

      const start = new Date(session.started_at).getTime();
      const end = session.submitted_at
        ? new Date(session.submitted_at).getTime()
        : Date.now();

      return Math.max(0, Math.floor((end - start) / 1000) - session.paused_seconds);
    };

    setElapsed(calculateElapsed());

    // Only tick if session is in progress (not submitted, cancelled, or paused)
    if (
      session.status === 'in_progress' ||
      session.status === 'created'
    ) {
      const interval = setInterval(() => {
        setElapsed(calculateElapsed());
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [session]);

  return elapsed;
}

export function SessionStatus({ session }: SessionStatusProps) {
  const status = statusConfig[session.status];
  const StatusIcon = status.icon;
  const elapsedSeconds = useLiveTimer(session);

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Session Status</h3>
        <span
          className={clsx(
            'flex items-center gap-1 px-2 py-1 text-xs font-medium rounded',
            status.color
          )}
        >
          <StatusIcon className="w-3 h-3" />
          {status.label}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Elapsed time:</span>
          <span className={clsx(
            'font-mono',
            session.status === 'in_progress' && 'text-blue-600 font-medium'
          )}>
            {formatDuration(elapsedSeconds)}
          </span>
        </div>

        {session.paused_seconds > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-500">Paused time:</span>
            <span className="font-mono">{formatDuration(session.paused_seconds)}</span>
          </div>
        )}

        {session.status === 'submitted' && (
          <>
            <hr className="my-3" />
            <div className="flex justify-between">
              <span className="text-gray-500">Main task score:</span>
              <span className="font-mono font-medium">
                {session.main_task_score !== null
                  ? `${(session.main_task_score * 100).toFixed(0)}%`
                  : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Side task score:</span>
              <span className="font-mono font-medium">
                {session.side_task_score !== null
                  ? `${(session.side_task_score * 100).toFixed(0)}%`
                  : '-'}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
