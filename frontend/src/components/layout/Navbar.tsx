import React, { useEffect, useState } from 'react';
import { Shield, Activity, Sparkles, Key, Check, AlertCircle, X, ExternalLink } from 'lucide-react';
import { healthService } from '../../services';
import type { HealthResponse } from '../../types';
import { StatusIndicator } from '../common/StatusIndicator';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>(() => {
    return localStorage.getItem('medlens_gemini_api_key') || (import.meta as any).env?.VITE_GEMINI_API_KEY || '';
  });
  const [savedKey, setSavedKey] = useState<string>(() => {
    return localStorage.getItem('medlens_gemini_api_key') || (import.meta as any).env?.VITE_GEMINI_API_KEY || '';
  });
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle');
  const [testMessage, setTestMessage] = useState<string>('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await healthService.getHealth();
        setHealth(data);
      } catch (err) {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSaveKey = () => {
    const trimmed = apiKey.trim();
    if (trimmed) {
      localStorage.setItem('medlens_gemini_api_key', trimmed);
      setSavedKey(trimmed);
      setTestStatus('idle');
      setTestMessage('API key saved locally to browser storage.');
    } else {
      localStorage.removeItem('medlens_gemini_api_key');
      setSavedKey('');
      setTestStatus('idle');
      setTestMessage('API key cleared.');
    }
  };

  const handleTestKey = async () => {
    const keyToTest = apiKey.trim() || savedKey;
    if (!keyToTest) {
      setTestStatus('failed');
      setTestMessage('Please enter an API key first.');
      return;
    }

    setTestStatus('testing');
    try {
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${keyToTest}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: 'Respond with OK' }] }],
          }),
        }
      );
      if (resp.ok) {
        setTestStatus('success');
        setTestMessage('Gemini API connected successfully! Live multimodal extraction is active.');
      } else {
        const errData = await resp.json().catch(() => ({}));
        setTestStatus('failed');
        setTestMessage(errData.error?.message || `API error HTTP ${resp.status}`);
      }
    } catch (err: any) {
      setTestStatus('failed');
      setTestMessage(err.message || 'Network error connecting to Gemini');
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-400 p-0.5 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Activity className="h-5 w-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">MEDLENS</span>
              <span className="rounded bg-cyan-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-cyan-400 border border-cyan-500/30">
                PHASE 1 FOUNDATION
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Clinical Information Intelligence</p>
          </div>
        </div>

        {/* Safety Disclaimer Banner */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-amber-500/30 text-[11px] text-amber-300/90 shadow-inner">
          <Shield className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          <span>Non-Diagnostic System • Reference Ranges Derived Exclusively From Source Documents</span>
        </div>

        {/* System Health, Gemini AI Button & Status */}
        <div className="flex items-center gap-3">
          {/* Gemini AI Key Modal Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
              savedKey
                ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300 hover:bg-emerald-900/60'
                : 'bg-cyan-950/60 border-cyan-500/30 text-cyan-300 hover:bg-cyan-900/60'
            }`}
            title="Configure Google Gemini API Key"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>{savedKey ? 'Gemini AI Active' : 'Connect Gemini API'}</span>
          </button>

          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800">
            {loading ? (
              <StatusIndicator status="busy" label="Checking backend..." />
            ) : health && health.status === 'healthy' ? (
              <StatusIndicator status="online" label={`API Online (${health.database})`} />
            ) : (
              <StatusIndicator status="offline" label="Backend Offline" />
            )}
          </div>
        </div>
      </div>

      {/* Gemini API Key Configuration Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/80">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Key className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Google Gemini API Configuration</h3>
                  <p className="text-[11px] text-slate-400">Configure AI extraction for Vercel & local sessions</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5 text-xs text-slate-300">
              {/* Vercel Environment Instructions */}
              <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-cyan-300 text-xs">
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>How to connect in Vercel (Permanent Deployment)</span>
                </div>
                <ol className="list-decimal list-inside space-y-1 text-slate-300 pl-1 leading-relaxed">
                  <li>Open your Vercel Dashboard at <code className="text-cyan-400 font-mono">vercel.com/vineethjarupla44-alt/frontend</code></li>
                  <li>Click <strong>Settings</strong> &gt; <strong>Environment Variables</strong></li>
                  <li>Add Key: <code className="text-emerald-400 font-mono">VITE_GEMINI_API_KEY</code>, Value: <em>your_api_key</em></li>
                  <li>Click Save and redeploy!</li>
                </ol>
              </div>

              {/* Instant Browser Key */}
              <div className="space-y-2">
                <label className="block font-medium text-slate-200">
                  Direct In-Browser API Key (Instant Live Testing)
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="AIzaSy..."
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs"
                  />
                </div>
                <p className="text-[11px] text-slate-500">
                  Keys saved here are stored exclusively in your browser's LocalStorage and are never transmitted to any third-party server.
                </p>
              </div>

              {/* Status Message */}
              {testMessage && (
                <div className={`p-3 rounded-lg flex items-center gap-2 text-xs ${
                  testStatus === 'success' 
                    ? 'bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
                    : testStatus === 'failed'
                    ? 'bg-rose-950/60 border border-rose-500/40 text-rose-300'
                    : 'bg-slate-950 border border-slate-800 text-slate-300'
                }`}>
                  {testStatus === 'success' && <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />}
                  {testStatus === 'failed' && <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />}
                  <span>{testMessage}</span>
                </div>
              )}

              {/* Modal Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={handleTestKey}
                  disabled={testStatus === 'testing'}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors cursor-pointer"
                >
                  {testStatus === 'testing' ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  onClick={() => {
                    handleSaveKey();
                    if (apiKey.trim()) {
                      handleTestKey();
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-colors cursor-pointer"
                >
                  Save & Apply Key
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

