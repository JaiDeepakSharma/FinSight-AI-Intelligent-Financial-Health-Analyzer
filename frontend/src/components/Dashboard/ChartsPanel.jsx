import React, { useState } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Legend, LineChart, Line } from 'recharts';
import { PieChart as PieIcon, Activity, Sparkles, TrendingDown, TrendingUp, DollarSign } from 'lucide-react';

const CHART_COLORS = [
  '#1c69d4', // BMW Blue / M Blue Dark
  '#0066b1', // M Blue Light
  '#e22718', // M Red
  '#0653b6', // Electric Blue
  '#ffffff', // White
  '#7e7e7e', // Muted Gray
  '#2b2b2b', // Carbon Gray
  '#3c3c3c', // Hairline Gray
  '#e6e6e6'  // Body Strong
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black border border-slateDark-border p-3.5 rounded-none text-[10px] uppercase tracking-wider shadow-none space-y-1">
        {label && <p className="font-bold text-white mb-2">{label}</p>}
        {payload.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
            <span className="flex items-center gap-1.5 text-slateDark-muted font-light">
              <span className="w-2 h-2 rounded-none" style={{ backgroundColor: item.color || item.payload.fill }} />
              {item.name}:
            </span>
            <span className="font-bold text-white">${item.value.toFixed(2)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const ChartsPanel = ({ analytics }) => {
  const [activeTab, setActiveTab] = useState('allocation');

  const {
    total_income = 0.0,
    total_spending = 0.0,
    net_savings = 0.0,
    anomalies_count = 0,
    spend_by_category = [],
    monthly_trends = [],
    forecast = []
  } = analytics;

  // Format forecast: separate historical vs. forecasted elements
  const hasForecast = forecast && forecast.length > 0;

  return (
    <div className="space-y-6">
      
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Net Savings */}
        <div className="relative overflow-hidden bg-slateDark-card border border-slateDark-border rounded-none p-5 shadow-none flex items-center gap-4 group hover:border-white transition-all duration-200">
          <div className="flex items-center justify-center w-11 h-11 bg-black text-white border border-slateDark-border rounded-none group-hover:scale-105 transition-all">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slateDark-muted uppercase tracking-bmw-machined block mb-1">Net Savings</span>
            <p className={`text-xl font-bold tracking-bmw-display ${net_savings >= 0 ? 'text-emerald-400' : 'text-bmw-red'}`}>
              ${net_savings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {/* Total Income */}
        <div className="relative overflow-hidden bg-slateDark-card border border-slateDark-border rounded-none p-5 shadow-none flex items-center gap-4 group hover:border-white transition-all duration-200">
          <div className="flex items-center justify-center w-11 h-11 bg-black text-white border border-slateDark-border rounded-none group-hover:scale-105 transition-all">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slateDark-muted uppercase tracking-bmw-machined block mb-1">Total Income</span>
            <p className="text-xl font-bold tracking-bmw-display text-white">
              ${total_income.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {/* Total Spending */}
        <div className="relative overflow-hidden bg-slateDark-card border border-slateDark-border rounded-none p-5 shadow-none flex items-center gap-4 group hover:border-white transition-all duration-200">
          <div className="flex items-center justify-center w-11 h-11 bg-black text-white border border-slateDark-border rounded-none group-hover:scale-105 transition-all">
            <TrendingDown className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slateDark-muted uppercase tracking-bmw-machined block mb-1">Total Spending</span>
            <p className="text-xl font-bold tracking-bmw-display text-white">
              ${total_spending.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {/* Anomalies Flagged */}
        <div className="relative overflow-hidden bg-slateDark-card border border-slateDark-border rounded-none p-5 shadow-none flex items-center gap-4 group hover:border-white transition-all duration-200">
          <div className={`flex items-center justify-center w-11 h-11 border rounded-none group-hover:scale-105 transition-all ${
            anomalies_count > 0 
              ? 'bg-black text-bmw-red border-bmw-red' 
              : 'bg-black text-slateDark-muted border-slateDark-border'
          }`}>
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slateDark-muted uppercase tracking-bmw-machined block mb-1">Anomalies Detected</span>
            <p className={`text-xl font-bold tracking-bmw-display ${anomalies_count > 0 ? 'text-bmw-red' : 'text-white'}`}>
              {anomalies_count}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs list */}
      <div className="bg-slateDark-card border border-slateDark-border rounded-none p-6 shadow-none space-y-6">
        <div className="flex border-b border-slateDark-border">
          <button
            onClick={() => setActiveTab('allocation')}
            className={`flex items-center gap-2 pb-3.5 px-4 text-xs font-bold uppercase tracking-bmw-machined transition-all border-b-2 outline-none -mb-[2px] ${
              activeTab === 'allocation'
                ? 'border-white text-white'
                : 'border-transparent text-slateDark-muted hover:text-white'
            }`}
          >
            <PieIcon className="w-4 h-4" />
            Category Allocation
          </button>
          
          <button
            onClick={() => setActiveTab('cashflow')}
            className={`flex items-center gap-2 pb-3.5 px-4 text-xs font-bold uppercase tracking-bmw-machined transition-all border-b-2 outline-none -mb-[2px] ${
              activeTab === 'cashflow'
                ? 'border-white text-white'
                : 'border-transparent text-slateDark-muted hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" />
            Monthly Cashflow
          </button>
          
          <button
            onClick={() => setActiveTab('forecast')}
            className={`flex items-center gap-2 pb-3.5 px-4 text-xs font-bold uppercase tracking-bmw-machined transition-all border-b-2 outline-none -mb-[2px] ${
              activeTab === 'forecast'
                ? 'border-white text-white'
                : 'border-transparent text-slateDark-muted hover:text-white'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Spending Forecast
          </button>
        </div>

        {/* Chart displays */}
        <div className="h-[360px] w-full relative">
          
          {/* TAB 1: Allocation Pie Chart */}
          {activeTab === 'allocation' && (
            spend_by_category.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slateDark-muted text-xs uppercase tracking-wider font-light">
                Upload a statement to view spending allocations.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 items-center h-full">
                <div className="h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={spend_by_category}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={95}
                        paddingAngle={4}
                        dataKey="amount"
                        nameKey="category"
                      >
                        {spend_by_category.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Custom Legend */}
                <div className="max-h-[300px] overflow-y-auto pr-4 space-y-2.5">
                  <h5 className="text-[10px] font-bold uppercase tracking-bmw-machined text-slateDark-muted mb-3">Allocations</h5>
                  {spend_by_category.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs py-1.5 border-b border-slateDark-border/30 last:border-0 uppercase tracking-wider font-light">
                      <span className="flex items-center gap-2 text-slate-300">
                        <span className="w-2.5 h-2.5 rounded-none shrink-0" style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }} />
                        {item.category}
                      </span>
                      <span className="font-bold text-white">
                        ${item.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} ({item.percentage.toFixed(1)}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {/* TAB 2: Cashflow Area Chart */}
          {activeTab === 'cashflow' && (
            monthly_trends.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slateDark-muted text-xs uppercase tracking-wider font-light">
                Upload a statement to view monthly income vs. spending.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthly_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0fa336" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#0fa336" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorSpending" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1c69d4" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#1c69d4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3c3c3c" vertical={false} />
                  <XAxis dataKey="month" stroke="#7e7e7e" fontSize={10} dy={10} className="uppercase tracking-wider font-light" />
                  <YAxis stroke="#7e7e7e" fontSize={10} dx={-5} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} iconType="rect" iconSize={10} className="uppercase tracking-wider text-xs font-bold" />
                  <Area type="monotone" name="Income" dataKey="income" stroke="#0fa336" strokeWidth={2} fillOpacity={1} fill="url(#colorIncome)" />
                  <Area type="monotone" name="Spending" dataKey="spending" stroke="#1c69d4" strokeWidth={2} fillOpacity={1} fill="url(#colorSpending)" />
                </AreaChart>
              </ResponsiveContainer>
            )
          )}

          {/* TAB 3: Forecast Line Chart */}
          {activeTab === 'forecast' && (
            !hasForecast ? (
              <div className="flex items-center justify-center h-full text-slateDark-muted text-xs uppercase tracking-wider font-light">
                Provide spending statement history to run forecasting models.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecast} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3c3c3c" vertical={false} />
                  <XAxis dataKey="date" stroke="#7e7e7e" fontSize={9} dy={10} tickFormatter={(tick) => tick.substring(5)} />
                  <YAxis stroke="#7e7e7e" fontSize={10} dx={-5} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} iconType="rect" iconSize={10} className="uppercase tracking-wider text-xs font-bold" />
                  {/* Historical line */}
                  <Line
                    type="monotone"
                    name="Historical Cumulative"
                    dataKey="amount"
                    data={forecast.filter(f => !f.is_forecast)}
                    stroke="#1c69d4"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                  {/* Forecasted line */}
                  <Line
                    type="monotone"
                    name="AI 30d Forecast projection"
                    dataKey="amount"
                    data={forecast}
                    stroke="#ffffff"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )
          )}

        </div>
      </div>

    </div>
  );
};

export default ChartsPanel;
