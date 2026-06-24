import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import AuthScreen from './components/Auth/AuthScreen';
import UploadSection from './components/Upload/UploadSection';
import ChartsPanel from './components/Dashboard/ChartsPanel';
import TransactionTable from './components/Dashboard/TransactionTable';
import ChatAdvisor from './components/Chat/ChatAdvisor';
import { TrendingUp, LogOut, User as UserIcon, Loader2, Sparkles, RefreshCw } from 'lucide-react';

const DashboardContent = () => {
  const { user, token, logout } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [analytics, setAnalytics] = useState({
    total_income: 0.0,
    total_spending: 0.0,
    net_savings: 0.0,
    anomalies_count: 0,
    spend_by_category: [],
    monthly_trends: [],
    forecast: []
  });
  const [loading, setLoading] = useState(true);

  const refreshData = async () => {
    setLoading(true);
    try {
      // 1. Fetch transactions list
      const txRes = await fetch('/api/transactions/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      let txs = [];
      if (txRes.ok) {
        txs = await txRes.json();
        setTransactions(txs);
      }

      // 2. Fetch dashboard analytics aggregates
      const analyticRes = await fetch('/api/analytics/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (analyticRes.ok) {
        const anaData = await analyticRes.json();
        setAnalytics(anaData);
      }
    } catch (err) {
      console.error('Error reloading financial data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [token]);

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to delete ALL statement histories, transaction records, and vector search mappings? This cannot be undone.')) {
      return;
    }
    try {
      const res = await fetch('/api/transactions/clear', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        refreshData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-slateDark-bg flex flex-col">
      
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-black/90 backdrop-blur-md border-b border-slateDark-border px-6 py-4 flex items-center justify-between shadow-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-none bg-black text-white border border-slateDark-border">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-bmw-display uppercase">FinSight AI</h1>
            <p className="text-[9px] text-slateDark-muted font-bold uppercase tracking-bmw-machined">Intelligent Financial Health Analyzer</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-black border border-slateDark-border rounded-none text-xs text-slate-300">
            <UserIcon className="w-3.5 h-3.5 text-brand-500" />
            <span className="font-light truncate max-w-[150px]">{user?.email}</span>
          </div>

          <button
            onClick={refreshData}
            title="Refresh Dashboard Data"
            className="p-2 bg-black hover:bg-white border border-slateDark-border rounded-none text-slateDark-muted hover:text-black transition duration-200"
          >
            <RefreshCw className="w-4 h-4 animate-spin-hover" />
          </button>

          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-2 bg-transparent hover:bg-bmw-red/10 border border-bmw-red/30 hover:border-bmw-red/60 text-bmw-red rounded-none text-xs font-bold uppercase tracking-bmw-machined transition duration-200 active:scale-[0.98]"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Signature M Tricolor Stripe Divider */}
      <div className="h-1 flex w-full">
        <div className="h-full bg-bmw-blueLight" style={{ width: '33.33%' }}></div>
        <div className="h-full bg-bmw-blueDark" style={{ width: '33.33%' }}></div>
        <div className="h-full bg-bmw-red" style={{ width: '33.34%' }}></div>
      </div>

      {/* Main Workspace Layout */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-[1600px] w-full mx-auto min-h-0">
        
        {/* Left column (Analytics & Data tables) */}
        <div className="lg:col-span-2 space-y-6 overflow-y-auto pr-0 lg:pr-2">
          
          {/* Charts Panel */}
          <ChartsPanel analytics={analytics} />
          
          {/* File Upload Manager */}
          <UploadSection token={token} onUploadSuccess={refreshData} />

          {/* Transaction Grid */}
          <TransactionTable 
            transactions={transactions} 
            token={token} 
            onCategoryUpdated={refreshData} 
          />

          {/* Clear Workspace button */}
          {transactions.length > 0 && (
            <div className="flex justify-end">
              <button
                onClick={handleClearAll}
                className="text-[11px] uppercase tracking-bmw-machined text-bmw-red hover:text-white font-bold px-4 py-2.5 border border-bmw-red/20 hover:border-bmw-red/60 hover:bg-bmw-red/10 rounded-none transition duration-200"
              >
                Reset Financial Workspace
              </button>
            </div>
          )}
        </div>

        {/* Right column (RAG Sidebar Chat Advisor) */}
        <div className="lg:col-span-1 h-[calc(100vh-120px)] lg:sticky lg:top-[92px]">
          <ChatAdvisor token={token} transactions={transactions} />
        </div>

      </main>
    </div>
  );
};

const App = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center gap-6">
        <div className="relative">
          <div className="w-14 h-14 border-2 border-slateDark-border border-t-brand-500 rounded-full animate-spin"></div>
          <TrendingUp className="w-6 h-6 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse-slow" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-bold text-white uppercase tracking-bmw-display">FinSight AI</h2>
          <p className="text-[11px] text-slateDark-muted mt-2 flex items-center justify-center gap-1.5 uppercase tracking-bmw-machined font-bold">
            <Sparkles className="w-3.5 h-3.5 text-brand-500 animate-spin" style={{ animationDuration: '3s' }} />
            Assembling financial layers...
          </p>
        </div>
      </div>
    );
  }

  return user ? <DashboardContent /> : <AuthScreen />;
};

const RootApp = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default RootApp;
