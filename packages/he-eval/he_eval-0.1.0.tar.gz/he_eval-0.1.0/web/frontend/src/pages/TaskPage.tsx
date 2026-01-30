import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { assignments } from '../api/assignments';
import { sessions } from '../api/sessions';
import { CLICommand } from '../components/CLICommand';
import { SessionStatus } from '../components/SessionStatus';
import type { Assignment, Session } from '../types';
import clsx from 'clsx';

const statusConfig = {
  pending: { label: 'Pending', icon: Clock, color: 'text-gray-600 bg-gray-100' },
  in_progress: { label: 'In Progress', icon: AlertCircle, color: 'text-blue-600 bg-blue-100' },
  completed: { label: 'Completed', icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  cancelled: { label: 'Cancelled', icon: AlertCircle, color: 'text-red-600 bg-red-100' },
};

const settingColors: Record<string, string> = {
  bashbench2: 'bg-purple-100 text-purple-700',
  bash: 'bg-blue-100 text-blue-700',
  iac: 'bg-orange-100 text-orange-700',
};

export function TaskPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [sessionList, setSessionList] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    if (!assignmentId) return;

    try {
      const [assignmentData, sessionsData] = await Promise.all([
        assignments.get(assignmentId),
        sessions.byAssignment(assignmentId),
      ]);
      setAssignment(assignmentData);
      setSessionList(sessionsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [assignmentId]);

  // Poll for updates when session is in progress
  useEffect(() => {
    const latestSession = sessionList[0];
    if (!latestSession) return;

    // Only poll if session is active (not submitted or cancelled)
    if (latestSession.status === 'submitted' || latestSession.status === 'cancelled') {
      return;
    }

    const interval = setInterval(fetchData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, [sessionList]);

  if (loading) {
    return <div className="text-center text-gray-500">Loading task...</div>;
  }

  if (error || !assignment) {
    return (
      <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md">
        {error || 'Assignment not found'}
      </div>
    );
  }

  const status = statusConfig[assignment.status];
  const StatusIcon = status.icon;
  const cliCommand = `he-cli run --assignment ${assignment.id}`;
  const latestSession = sessionList[0];

  return (
    <div className="max-w-3xl">
      <Link
        to="/dashboard"
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Dashboard
      </Link>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span
              className={clsx(
                'px-3 py-1 text-sm font-medium rounded',
                settingColors[assignment.setting] || 'bg-gray-100 text-gray-700'
              )}
            >
              {assignment.setting}
            </span>
            <span
              className={clsx(
                'flex items-center gap-1 px-3 py-1 text-sm font-medium rounded',
                status.color
              )}
            >
              <StatusIcon className="w-4 h-4" />
              {status.label}
            </span>
          </div>
          <button
            onClick={fetchData}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <dl className="space-y-3">
          <div>
            <dt className="text-sm text-gray-500">Task ID</dt>
            <dd className="font-mono text-gray-900">{assignment.task_id}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Side Task</dt>
            <dd className="font-mono text-gray-900">{assignment.side_task}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Priority</dt>
            <dd className="text-gray-900">{assignment.priority}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Assigned</dt>
            <dd className="text-gray-900">
              {new Date(assignment.assigned_at).toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>

      {latestSession && (
        <div className="mb-6">
          <SessionStatus session={latestSession} />
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Run this task
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Copy and run the following command in your terminal to start the task:
        </p>
        <CLICommand command={cliCommand} />

        {assignment.status === 'pending' && !latestSession && (
          <p className="mt-4 text-sm text-gray-500">
            The task status will update to "In Progress" once you start the CLI.
          </p>
        )}

        {assignment.status === 'completed' && (
          <div className="mt-4 p-3 bg-green-50 text-green-700 rounded-md text-sm">
            This task has been completed.
          </div>
        )}
      </div>
    </div>
  );
}
