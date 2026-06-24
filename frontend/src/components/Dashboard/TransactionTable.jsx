import React, { useState } from 'react';
import { Search, ChevronLeft, ChevronRight, AlertTriangle, ArrowUpDown } from 'lucide-react';

const CATEGORIES = [
  "Housing & Rent",
  "Groceries",
  "Food & Dining",
  "Utilities",
  "Transportation",
  "Entertainment",
  "Shopping",
  "Salary & Income",
  "Investment",
  "Insurance & Medical",
  "Uncategorized"
];

const TransactionTable = ({ transactions, token, onCategoryUpdated }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc' | 'desc'
  const [updatingId, setUpdatingId] = useState(null);

  const itemsPerPage = 10;

  // Handle category change in backend
  const handleCategoryChange = async (id, newCategory) => {
    setUpdatingId(id);
    try {
      const res = await fetch(`/api/transactions/${id}/category`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ category: newCategory })
      });

      if (res.ok) {
        onCategoryUpdated();
      } else {
        console.error('Failed to update category');
      }
    } catch (err) {
      console.error('Error updating category:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  // Toggle sorting
  const requestSort = (field) => {
    let order = 'asc';
    if (sortField === field && sortOrder === 'asc') {
      order = 'desc';
    }
    setSortField(field);
    setSortOrder(order);
    setCurrentPage(1);
  };

  // Filter transactions
  const filteredTransactions = transactions.filter(tx => {
    const matchesSearch = tx.description.toLowerCase().includes(search.toLowerCase()) || 
                          tx.category.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || tx.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Sort transactions
  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];

    if (sortField === 'date') {
      aVal = new Date(a.date).getTime();
      bVal = new Date(b.date).getTime();
    } else if (sortField === 'amount') {
      aVal = a.amount;
      bVal = b.amount;
    } else {
      aVal = String(aVal).toLowerCase();
      bVal = String(bVal).toLowerCase();
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  // Pagination bounds
  const totalPages = Math.ceil(sortedTransactions.length / itemsPerPage) || 1;
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = sortedTransactions.slice(indexOfFirstItem, indexOfLastItem);

  const paginate = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  return (
    <div className="bg-slateDark-card border border-slateDark-border rounded-none p-6 shadow-none space-y-5">
      
      {/* Header and filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-white text-base uppercase tracking-bmw-display">Transaction History</h3>
          <p className="text-[11px] text-slateDark-muted mt-1 uppercase tracking-wider font-light">
            View, search, and override categories of your transactions.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slateDark-muted">
              <Search className="w-3.5 h-3.5" />
            </span>
            <input
              type="text"
              placeholder="Search description..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
              className="bg-black border border-slateDark-border focus:border-white rounded-none py-2 pl-9 pr-4 text-white placeholder-slateDark-muted focus:outline-none focus:ring-0 transition duration-200 text-xs font-light w-full md:w-56"
            />
          </div>

          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
            className="bg-black border border-slateDark-border focus:border-white rounded-none py-2 px-3 text-white focus:outline-none focus:ring-0 transition text-xs font-bold uppercase tracking-bmw-machined cursor-pointer"
          >
            <option value="All">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat} value={cat}>{cat.toUpperCase()}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slateDark-border text-slateDark-muted font-bold text-xs uppercase tracking-bmw-machined">
              <th className="py-3 px-4 cursor-pointer hover:text-white transition" onClick={() => requestSort('date')}>
                <div className="flex items-center gap-1.5">
                  Date
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Description</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4 text-right cursor-pointer hover:text-white transition" onClick={() => requestSort('amount')}>
                <div className="flex items-center justify-end gap-1.5">
                  Amount
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slateDark-border/60 text-xs uppercase tracking-wider font-light">
            {currentItems.length === 0 ? (
              <tr>
                <td colSpan="4" className="py-8 text-center text-slateDark-muted">
                  No transactions found matching the filters.
                </td>
              </tr>
            ) : (
              currentItems.map((tx) => (
                <tr key={tx.id} className="hover:bg-slateDark-cardHover/40 group transition duration-150">
                  {/* Date */}
                  <td className="py-3.5 px-4 font-light text-slate-300">
                    {new Date(tx.date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                  </td>
                  
                  {/* Description & Anomalies */}
                  <td className="py-3.5 px-4 font-bold text-white">
                    <div className="flex items-center gap-2.5">
                      <span className="truncate max-w-[180px] md:max-w-xs uppercase" title={tx.description}>
                        {tx.description}
                      </span>
                      {tx.is_anomaly && (
                        <div 
                          className="flex items-center gap-1 px-2 py-0.5 bg-black border border-bmw-red text-bmw-red text-[9px] font-bold rounded-none cursor-help"
                          title={tx.anomaly_reason || "Flagged Anomaly"}
                        >
                          <AlertTriangle className="w-3 h-3" />
                          <span>Anomaly</span>
                        </div>
                      )}
                    </div>
                  </td>
                  
                  {/* Category Dropdown Selection */}
                  <td className="py-3.5 px-4">
                    <select
                      value={tx.category}
                      onChange={(e) => handleCategoryChange(tx.id, e.target.value)}
                      disabled={updatingId === tx.id}
                      className="bg-black border border-slateDark-border rounded-none py-1.5 px-2 text-[10px] font-bold uppercase tracking-bmw-machined text-white focus:outline-none focus:ring-0 focus:border-white cursor-pointer disabled:opacity-40 transition"
                    >
                      {CATEGORIES.map(cat => (
                        <option key={cat} value={cat}>{cat.toUpperCase()}</option>
                      ))}
                    </select>
                  </td>
                  
                  {/* Amount */}
                  <td className={`py-3.5 px-4 text-right font-bold tracking-wider ${
                    tx.amount >= 0 ? 'text-emerald-400' : 'text-slate-300'
                  }`}>
                    {tx.amount >= 0 ? '+' : '-'}${Math.abs(tx.amount).toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slateDark-border/60">
          <p className="text-[11px] text-slateDark-muted font-light uppercase tracking-wider">
            Showing <span className="font-bold text-white">{indexOfFirstItem + 1}</span> to{' '}
            <span className="font-bold text-white">
              {Math.min(indexOfLastItem, sortedTransactions.length)}
            </span>{' '}
            of <span className="font-bold text-white">{sortedTransactions.length}</span> transactions
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => paginate(currentPage - 1)}
              disabled={currentPage === 1}
              className="p-1.5 border border-slateDark-border bg-black text-slateDark-muted hover:text-black hover:bg-white disabled:opacity-40 transition rounded-none"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-slateDark-muted uppercase tracking-wider font-light">
              Page <span className="font-bold text-white">{currentPage}</span> of{' '}
              <span className="font-bold text-white">{totalPages}</span>
            </span>
            <button
              onClick={() => paginate(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="p-1.5 border border-slateDark-border bg-black text-slateDark-muted hover:text-black hover:bg-white disabled:opacity-40 transition rounded-none"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default TransactionTable;
