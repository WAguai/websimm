"use client";

import { useState, useEffect } from 'react';
import { checkBackendHealth } from '../lib/aiClient';

export default function BackendHealthCheck() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await checkBackendHealth();
      setHealth(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
          <span className="text-yellow-800">检查后端服务状态...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-red-800 font-medium">❌ 后端服务不可用</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <p className="text-red-600 text-sm mt-1">
              请确保Python后端服务已启动 (http://localhost:8000)
            </p>
          </div>
          <button
            onClick={checkHealth}
            className="px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 text-sm"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-green-800 font-medium">✅ 后端服务正常</h3>
          <p className="text-green-600 text-sm mt-1">
            服务: {health?.service} | 状态: {health?.status}
          </p>
        </div>
        <button
          onClick={checkHealth}
          className="px-3 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200 text-sm"
        >
          刷新
        </button>
      </div>
    </div>
  );
}