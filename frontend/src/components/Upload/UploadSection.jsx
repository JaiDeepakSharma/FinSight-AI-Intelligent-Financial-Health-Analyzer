import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const UploadSection = ({ token, onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statements, setStatements] = useState([]);
  const [message, setMessage] = useState(null); // { type: 'success' | 'error', text: string }

  // Load existing uploaded statements
  const fetchStatements = async () => {
    try {
      const res = await fetch('/api/transactions/statements', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setStatements(data);
      }
    } catch (err) {
      console.error('Error fetching statements:', err);
    }
  };

  useEffect(() => {
    fetchStatements();
  }, [token]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'pdf') {
      setMessage({ type: 'error', text: 'Invalid file format. Please upload a CSV or PDF.' });
      return;
    }

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/transactions/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        setMessage({ type: 'success', text: `Successfully parsed and loaded ${data.length} transactions!` });
        fetchStatements();
        onUploadSuccess();
      } else {
        throw new Error(data.detail || 'Upload failed');
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Server error occurred during parsing.' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this statement and its transactions? This will update your analytics and vector search database.')) {
      return;
    }
    
    try {
      const res = await fetch(`/api/transactions/statements/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        setStatements(statements.filter(s => s.id !== id));
        setMessage({ type: 'success', text: 'Statement deleted.' });
        onUploadSuccess();
      } else {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to delete');
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Upload Zone */}
      <div 
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center border border-dashed p-8 transition-all duration-300 min-h-[200px] cursor-pointer text-center rounded-none ${
          dragActive 
            ? 'border-white bg-slateDark-card scale-[1.01]' 
            : 'border-slateDark-border bg-black hover:border-white'
        }`}
      >
        <input 
          type="file" 
          id="statement-upload" 
          className="hidden" 
          accept=".csv,.pdf" 
          onChange={handleFileChange}
          disabled={uploading}
        />
        
        <label htmlFor="statement-upload" className="w-full h-full flex flex-col items-center cursor-pointer">
          {uploading ? (
            <Loader2 className="w-10 h-10 text-white animate-spin mb-4" />
          ) : (
            <Upload className="w-10 h-10 text-slateDark-muted mb-4 group-hover:text-white transition-colors duration-200" />
          )}
          
          <h3 className="font-bold text-base text-white uppercase tracking-bmw-display mb-1.5">
            {uploading ? 'Processing Statement...' : 'Upload Bank Statement'}
          </h3>
          <p className="text-xs text-slateDark-muted max-w-xs mb-5 font-light leading-relaxed">
            Drag & drop your PDF or CSV bank statement file here, or click to browse local files.
          </p>
          
          <div className="flex gap-2.5">
            <span className="px-3 py-1.5 border border-slateDark-border bg-slateDark-card text-white text-[10px] font-bold rounded-none uppercase tracking-bmw-machined">
              PDF
            </span>
            <span className="px-3 py-1.5 border border-slateDark-border bg-slateDark-card text-white text-[10px] font-bold rounded-none uppercase tracking-bmw-machined">
              CSV
            </span>
          </div>
        </label>
      </div>

      {/* Alerts */}
      {message && (
        <div className={`flex items-start gap-3 p-4 border rounded-none text-xs uppercase tracking-wider ${
          message.type === 'success'
            ? 'bg-black border-emerald-500 text-white font-light'
            : 'bg-black border-bmw-red text-white font-light'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 text-bmw-red shrink-0 mt-0.5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Statements List */}
      <div className="bg-slateDark-card border border-slateDark-border rounded-none p-6 shadow-none">
        <h4 className="font-bold text-white mb-4 text-xs uppercase tracking-bmw-machined text-slateDark-muted">
          Uploaded Statements ({statements.length})
        </h4>

        {statements.length === 0 ? (
          <div className="text-center py-6 text-slateDark-muted text-xs font-light uppercase tracking-wider">
            No bank statements uploaded yet.
          </div>
        ) : (
          <div className="divide-y divide-slateDark-border">
            {statements.map((stmt) => (
              <div key={stmt.id} className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0 group">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 bg-black border border-slateDark-border text-slateDark-text rounded-none group-hover:border-white group-hover:text-white transition-all">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white truncate max-w-xs md:max-w-md uppercase tracking-wider">
                      {stmt.filename}
                    </p>
                    <p className="text-[10px] text-slateDark-muted mt-1 uppercase tracking-wider font-light">
                      Uploaded: {new Date(stmt.uploaded_at).toLocaleString()} | Type: {stmt.file_type.toUpperCase()}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDelete(stmt.id)}
                  className="p-2 hover:bg-bmw-red/10 border border-transparent hover:border-bmw-red/30 hover:text-bmw-red text-slateDark-muted rounded-none transition duration-200"
                  title="Delete statement and records"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadSection;
