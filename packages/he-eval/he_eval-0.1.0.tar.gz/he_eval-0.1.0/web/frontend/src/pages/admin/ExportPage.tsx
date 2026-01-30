import { Download, FileSpreadsheet } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function ExportPage() {
  const token = localStorage.getItem('token');

  const downloadCSV = () => {
    // Open in new tab with auth header via fetch + blob
    fetch(`${API_URL}/api/v1/export/results.csv`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Download failed');
        return res.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'human_eval_results.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      })
      .catch((err) => {
        alert(err.message);
      });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Export Results</h1>

      <div className="grid gap-4 max-w-xl">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FileSpreadsheet className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-medium text-gray-900">Results CSV</h2>
              <p className="mt-1 text-sm text-gray-500">
                Download all session results as a CSV file. Includes user info,
                task details, scores, and timing data.
              </p>
              <button
                onClick={downloadCSV}
                className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download CSV
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Download className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-medium text-gray-900">Eval Files</h2>
              <p className="mt-1 text-sm text-gray-500">
                Individual .eval files can be downloaded from each session.
                Go to Assignments, find a completed session, and download its eval file.
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Bulk download of all eval files coming soon.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
