import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Clock, CheckCircle, AlertCircle, Filter } from 'lucide-react';
import { assignments } from '../api/assignments';
import type { Assignment } from '../types';
import clsx from 'clsx';

const statusConfig = {
  pending: { label: 'Pending', icon: Clock, color: 'text-gray-500 bg-gray-100' },
  in_progress: { label: 'In Progress', icon: AlertCircle, color: 'text-blue-600 bg-blue-100' },
  completed: { label: 'Completed', icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  cancelled: { label: 'Cancelled', icon: AlertCircle, color: 'text-red-600 bg-red-100' },
};

const settingColors: Record<string, string> = {
  bashbench2: 'bg-purple-100 text-purple-700',
  bash: 'bg-blue-100 text-blue-700',
  iac: 'bg-orange-100 text-orange-700',
};

function AssignmentCard({ assignment }: { assignment: Assignment }) {
  const status = statusConfig[assignment.status];
  const StatusIcon = status.icon;

  return (
    <Link
      to={`/task/${assignment.id}`}
      className="block p-4 bg-white rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={clsx(
                'px-2 py-0.5 text-xs font-medium rounded',
                settingColors[assignment.setting] || 'bg-gray-100 text-gray-700'
              )}
            >
              {assignment.setting}
            </span>
            <span className={clsx('flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded', status.color)}>
              <StatusIcon className="w-3 h-3" />
              {status.label}
            </span>
            {assignment.priority > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
                Priority: {assignment.priority}
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-gray-900 truncate">
            Task: {assignment.task_id}
          </p>
          <p className="text-sm text-gray-500 truncate">
            Side task: {assignment.side_task}
          </p>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
      </div>
    </Link>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [settingFilter, setSettingFilter] = useState<string>('all');

  useEffect(() => {
    assignments
      .list()
      .then((list) => {
        // Sort by priority (descending), then by assigned_at (ascending)
        const sorted = list.sort((a, b) => {
          if (b.priority !== a.priority) return b.priority - a.priority;
          return new Date(a.assigned_at).getTime() - new Date(b.assigned_at).getTime();
        });
        setData(sorted);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Get unique settings from data
  const availableSettings = useMemo(() => {
    const settings = new Set(data.map((a) => a.setting));
    return Array.from(settings).sort();
  }, [data]);

  // Get unique statuses from data
  const availableStatuses = useMemo(() => {
    const statuses = new Set(data.map((a) => a.status));
    return Array.from(statuses).sort();
  }, [data]);

  // Filter data
  const filteredData = useMemo(() => {
    return data.filter((a) => {
      if (statusFilter !== 'all' && a.status !== statusFilter) return false;
      if (settingFilter !== 'all' && a.setting !== settingFilter) return false;
      return true;
    });
  }, [data, statusFilter, settingFilter]);

  if (loading) {
    return <div className="text-center text-gray-500">Loading assignments...</div>;
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md">
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-lg font-medium text-gray-900">No pending assignments</h2>
        <p className="mt-2 text-gray-500">
          Check back later or contact your admin for new tasks.
        </p>
      </div>
    );
  }

  const hasFilters = statusFilter !== 'all' || settingFilter !== 'all';

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Your Assignments</h1>
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All statuses</option>
            {availableStatuses.map((status) => (
              <option key={status} value={status}>
                {statusConfig[status as keyof typeof statusConfig]?.label || status}
              </option>
            ))}
          </select>
          <select
            value={settingFilter}
            onChange={(e) => setSettingFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All settings</option>
            {availableSettings.map((setting) => (
              <option key={setting} value={setting}>
                {setting}
              </option>
            ))}
          </select>
        </div>
      </div>

      {hasFilters && filteredData.length !== data.length && (
        <p className="text-sm text-gray-500 mb-4">
          Showing {filteredData.length} of {data.length} assignments
        </p>
      )}

      {filteredData.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500">No assignments match your filters.</p>
          <button
            onClick={() => {
              setStatusFilter('all');
              setSettingFilter('all');
            }}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredData.map((assignment) => (
            <AssignmentCard key={assignment.id} assignment={assignment} />
          ))}
        </div>
      )}
    </div>
  );
}
