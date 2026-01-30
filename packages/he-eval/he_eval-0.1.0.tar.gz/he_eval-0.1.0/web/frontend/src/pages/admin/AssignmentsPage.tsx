import { useState, useEffect, type FormEvent } from 'react';
import { Plus, X, Pencil, Trash2, Users } from 'lucide-react';
import { assignments, type AssignmentUpdate, type BulkAssignmentCreate } from '../../api/assignments';
import { users } from '../../api/users';
import { tasks, type SettingInfo, type SideTaskInfo } from '../../api/tasks';
import type { Assignment, User } from '../../types';
import clsx from 'clsx';

interface AssignmentFormProps {
  onClose: () => void;
  onSaved: (assignment: Assignment) => void;
  usersList: User[];
  settingsData: Record<string, SettingInfo>;
  editingAssignment?: Assignment;
}

function AssignmentForm({
  onClose,
  onSaved,
  usersList,
  settingsData,
  editingAssignment,
}: AssignmentFormProps) {
  const isEditing = !!editingAssignment;
  const [userId, setUserId] = useState(editingAssignment?.user_id || '');
  const [setting, setSetting] = useState(editingAssignment?.setting || 'bashbench2');
  const [taskId, setTaskId] = useState(editingAssignment?.task_id || '');
  const [sideTask, setSideTask] = useState(editingAssignment?.side_task || '');
  const [sideTasks, setSideTasks] = useState<SideTaskInfo[]>([]);
  const [priority, setPriority] = useState(editingAssignment?.priority || 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    tasks.getSideTasks(setting).then((st) => {
      setSideTasks(st);
      if (!editingAssignment && st.length > 0) {
        setSideTask(st[0].id);
      }
    });
  }, [setting, editingAssignment]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result: Assignment;
      if (isEditing) {
        const update: AssignmentUpdate = {
          task_id: taskId,
          side_task: sideTask,
          priority,
        };
        result = await assignments.update(editingAssignment.id, update);
      } else {
        result = await assignments.create({
          user_id: userId,
          setting,
          task_id: taskId,
          side_task: sideTask,
          priority,
        });
      }
      onSaved(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save assignment');
    } finally {
      setLoading(false);
    }
  };

  const currentSetting = settingsData[setting];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
          <h2 className="text-lg font-medium">
            {isEditing ? 'Edit Assignment' : 'Create Assignment'}
          </h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-700 bg-red-100 rounded-md">{error}</div>
          )}

          {!isEditing && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Assign to</label>
              <select
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select a user...</option>
                {usersList.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.email})
                  </option>
                ))}
              </select>
            </div>
          )}

          {!isEditing && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Setting</label>
              <select
                value={setting}
                onChange={(e) => setSetting(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.entries(settingsData).map(([key, info]) => (
                  <option key={key} value={key}>
                    {info.name} ({info.task_count} tasks)
                  </option>
                ))}
              </select>
              {currentSetting && (
                <p className="mt-1 text-xs text-gray-500">{currentSetting.description}</p>
              )}
            </div>
          )}

          {isEditing && (
            <div className="p-3 bg-gray-50 rounded-md text-sm">
              <p><strong>User:</strong> {usersList.find(u => u.id === editingAssignment.user_id)?.name || editingAssignment.user_id}</p>
              <p><strong>Setting:</strong> {editingAssignment.setting}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">Task ID</label>
            <input
              type="text"
              value={taskId}
              onChange={(e) => setTaskId(e.target.value)}
              required
              placeholder={currentSetting?.example_tasks?.[0] || 'Enter task ID'}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {currentSetting?.example_tasks && (
              <p className="mt-1 text-xs text-gray-500">
                Examples: {currentSetting.example_tasks.slice(0, 3).join(', ')}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Side Task</label>
            <select
              value={sideTask}
              onChange={(e) => setSideTask(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {sideTasks.map((st) => (
                <option key={st.id} value={st.id}>{st.name}</option>
              ))}
            </select>
            {sideTasks.find((st) => st.id === sideTask)?.description && (
              <p className="mt-1 text-xs text-gray-500">
                {sideTasks.find((st) => st.id === sideTask)?.description}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Priority</label>
            <input
              type="number"
              value={priority}
              onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
              min={0}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">Higher numbers = higher priority</p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Assignment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface BulkAssignmentFormProps {
  onClose: () => void;
  onCreated: (assignments: Assignment[]) => void;
  usersList: User[];
  settingsData: Record<string, SettingInfo>;
}

function BulkAssignmentForm({
  onClose,
  onCreated,
  usersList,
  settingsData,
}: BulkAssignmentFormProps) {
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set());
  const [setting, setSetting] = useState('bashbench2');
  const [taskId, setTaskId] = useState('');
  const [sideTask, setSideTask] = useState('');
  const [sideTasks, setSideTasks] = useState<SideTaskInfo[]>([]);
  const [priority, setPriority] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    tasks.getSideTasks(setting).then((st) => {
      setSideTasks(st);
      if (st.length > 0) {
        setSideTask(st[0].id);
      }
    });
  }, [setting]);

  const toggleUser = (userId: string) => {
    setSelectedUserIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedUserIds(new Set(usersList.map((u) => u.id)));
  };

  const selectNone = () => {
    setSelectedUserIds(new Set());
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (selectedUserIds.size === 0) {
      setError('Select at least one user');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const data: BulkAssignmentCreate = {
        user_ids: Array.from(selectedUserIds),
        setting,
        task_id: taskId,
        side_task: sideTask,
        priority,
      };
      const result = await assignments.createBulk(data);
      onCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create assignments');
    } finally {
      setLoading(false);
    }
  };

  const currentSetting = settingsData[setting];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
          <h2 className="text-lg font-medium">Bulk Create Assignments</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-700 bg-red-100 rounded-md">{error}</div>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Select Users ({selectedUserIds.size} selected)
              </label>
              <div className="space-x-2">
                <button
                  type="button"
                  onClick={selectAll}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={selectNone}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  None
                </button>
              </div>
            </div>
            <div className="border border-gray-300 rounded-md max-h-48 overflow-y-auto">
              {usersList.map((user) => (
                <label
                  key={user.id}
                  className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedUserIds.has(user.id)}
                    onChange={() => toggleUser(user.id)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    {user.name} <span className="text-gray-400">({user.email})</span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Setting</label>
            <select
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {Object.entries(settingsData).map(([key, info]) => (
                <option key={key} value={key}>
                  {info.name} ({info.task_count} tasks)
                </option>
              ))}
            </select>
            {currentSetting && (
              <p className="mt-1 text-xs text-gray-500">{currentSetting.description}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Task ID</label>
            <input
              type="text"
              value={taskId}
              onChange={(e) => setTaskId(e.target.value)}
              required
              placeholder={currentSetting?.example_tasks?.[0] || 'Enter task ID'}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {currentSetting?.example_tasks && (
              <p className="mt-1 text-xs text-gray-500">
                Examples: {currentSetting.example_tasks.slice(0, 3).join(', ')}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Side Task</label>
            <select
              value={sideTask}
              onChange={(e) => setSideTask(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {sideTasks.map((st) => (
                <option key={st.id} value={st.id}>{st.name}</option>
              ))}
            </select>
            {sideTasks.find((st) => st.id === sideTask)?.description && (
              <p className="mt-1 text-xs text-gray-500">
                {sideTasks.find((st) => st.id === sideTask)?.description}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Priority</label>
            <input
              type="number"
              value={priority}
              onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
              min={0}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">Higher numbers = higher priority</p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || selectedUserIds.size === 0}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : `Create ${selectedUserIds.size} Assignment${selectedUserIds.size !== 1 ? 's' : ''}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

const settingColors: Record<string, string> = {
  bashbench2: 'bg-purple-100 text-purple-700',
  bash: 'bg-blue-100 text-blue-700',
  iac: 'bg-orange-100 text-orange-700',
};

export function AssignmentsPage() {
  const [data, setData] = useState<Assignment[]>([]);
  const [usersList, setUsersList] = useState<User[]>([]);
  const [settingsData, setSettingsData] = useState<Record<string, SettingInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      assignments.listAll(),
      users.list(),
      tasks.getSettings(),
    ])
      .then(([assignmentsList, usersListData, settingsInfo]) => {
        setData(assignmentsList);
        setUsersList(usersListData);
        setSettingsData(settingsInfo);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSaved = (assignment: Assignment) => {
    if (editingAssignment) {
      setData((prev) => prev.map((a) => (a.id === assignment.id ? assignment : a)));
    } else {
      setData((prev) => [assignment, ...prev]);
    }
    setShowForm(false);
    setEditingAssignment(null);
  };

  const handleBulkCreated = (newAssignments: Assignment[]) => {
    setData((prev) => [...newAssignments, ...prev]);
    setShowBulkForm(false);
  };

  const handleDelete = async (assignmentId: string) => {
    if (!confirm('Are you sure you want to delete this assignment?')) return;

    setDeleting(assignmentId);
    try {
      await assignments.delete(assignmentId);
      setData((prev) => prev.filter((a) => a.id !== assignmentId));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete assignment');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (assignment: Assignment) => {
    setEditingAssignment(assignment);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingAssignment(null);
  };

  const userNames = new Map(usersList.map((u) => [u.id, u.name]));

  if (loading) {
    return <div className="text-center text-gray-500">Loading assignments...</div>;
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md">{error}</div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">All Assignments</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowBulkForm(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50"
          >
            <Users className="w-4 h-4 mr-2" />
            Bulk Create
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Setting</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side Task</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((assignment) => (
              <tr key={assignment.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {userNames.get(assignment.user_id) || assignment.user_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={clsx('px-2 py-1 text-xs font-medium rounded', settingColors[assignment.setting] || 'bg-gray-100 text-gray-700')}>
                    {assignment.setting}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">{assignment.task_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{assignment.side_task}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={clsx('px-2 py-1 text-xs font-medium rounded', statusColors[assignment.status])}>
                    {assignment.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{assignment.priority}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                  <button
                    onClick={() => handleEdit(assignment)}
                    className="text-blue-600 hover:text-blue-800"
                    title="Edit assignment"
                  >
                    <Pencil className="w-4 h-4 inline" />
                  </button>
                  <button
                    onClick={() => handleDelete(assignment.id)}
                    disabled={deleting === assignment.id}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    title="Delete assignment"
                  >
                    <Trash2 className="w-4 h-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-sm text-gray-500">
                  No assignments yet. Create one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showForm && Object.keys(settingsData).length > 0 && (
        <AssignmentForm
          onClose={handleCloseForm}
          onSaved={handleSaved}
          usersList={usersList}
          settingsData={settingsData}
          editingAssignment={editingAssignment || undefined}
        />
      )}

      {showBulkForm && Object.keys(settingsData).length > 0 && (
        <BulkAssignmentForm
          onClose={() => setShowBulkForm(false)}
          onCreated={handleBulkCreated}
          usersList={usersList}
          settingsData={settingsData}
        />
      )}
    </div>
  );
}
