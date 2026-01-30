import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CLICommandProps {
  command: string;
}

export function CLICommand({ command }: CLICommandProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto font-mono text-sm">
        <code>{command}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 text-gray-400 hover:text-white bg-gray-800 rounded-md transition-colors"
        title={copied ? 'Copied!' : 'Copy to clipboard'}
      >
        {copied ? (
          <Check className="w-4 h-4 text-green-400" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
