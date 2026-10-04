'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, Activity, Terminal, RefreshCw, Sliders, Layers } from 'lucide-react';
import { api } from '@/lib/api';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function Navbar({ activeTab, setActiveTab }: NavbarProps) {
  const [healthStatus, setHealthStatus] = useState<string>('checking');

  useEffect(() => {
    async function checkBackend() {
      try {
        const res = await api.getHealth();
        setHealthStatus(res?.status === 'healthy' ? 'operational' : 'degraded');
      } catch {
        setHealthStatus('offline');
      }
    }
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: Activity },
    { id: 'transactions', label: 'Transactions', icon: Layers },
    { id: 'simulator', label: 'Risk Simulator', icon: Terminal },
    { id: 'reconciliation', label: 'Razorpay Recon', icon: RefreshCw },
    { id: 'rules', label: 'Rule Engine', icon: Sliders },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-white border-b border-slate-200/90 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Product Name */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => setActiveTab('overview')}
          >
            <div className="w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center shadow-xs">
              <ShieldCheck className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-base font-bold tracking-tight text-slate-900 group-hover:text-slate-800 transition-colors">
                  RazorGuard
                </span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                  Risk Console
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-sans">
                Payment Risk & Reconciliation Operations
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex space-x-1 sm:space-x-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-slate-100 text-slate-900 border border-slate-200 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                  <span className="hidden md:inline">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Engine Status indicator */}
          <div className="flex items-center space-x-2">
            <div
              className={`flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-medium border ${
                healthStatus === 'operational'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : healthStatus === 'degraded'
                  ? 'bg-amber-50 border-amber-200 text-amber-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus === 'operational'
                    ? 'bg-emerald-600 animate-pulse'
                    : healthStatus === 'degraded'
                    ? 'bg-amber-500'
                    : 'bg-red-500'
                }`}
              />
              <span className="font-mono text-[11px]">
                {healthStatus === 'operational'
                  ? 'Engine Active'
                  : healthStatus === 'degraded'
                  ? 'Engine Degraded'
                  : 'Engine Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
