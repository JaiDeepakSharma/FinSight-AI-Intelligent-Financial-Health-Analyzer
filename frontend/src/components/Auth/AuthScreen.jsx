import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { TrendingUp, Mail, Lock, ShieldAlert, ArrowRight, Loader2 } from 'lucide-react';

const AuthScreen = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');
  
  const { login, register, loading, error, setError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setError(null);

    if (!email || !password) {
      setLocalError('Please fill in all fields.');
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters long.');
      return;
    }

    if (isLogin) {
      await login(email, password);
    } else {
      await register(email, password);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setLocalError('');
    setError(null);
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-black px-4">
      {/* Main card */}
      <div className="relative w-full max-w-md bg-slateDark-card border border-slateDark-border rounded-none p-8 shadow-none transition-all duration-300">
        {/* M tricolor stripe header decoration */}
        <div className="absolute top-0 left-0 right-0 h-1 flex">
          <div className="h-full bg-bmw-blueLight" style={{ width: '33.33%' }}></div>
          <div className="h-full bg-bmw-blueDark" style={{ width: '33.33%' }}></div>
          <div className="h-full bg-bmw-red" style={{ width: '33.34%' }}></div>
        </div>

        {/* Brand header */}
        <div className="flex flex-col items-center mb-8 mt-2">
          <div className="flex items-center justify-center w-12 h-12 rounded-none bg-black border border-slateDark-border text-white mb-4">
            <TrendingUp className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-bmw-display text-white uppercase">FinSight AI</h1>
          <p className="text-[11px] text-slateDark-muted mt-1.5 text-center uppercase tracking-wider font-light">
            Intelligent Financial Health Analyzer
          </p>
        </div>

        {/* Error message */}
        {(localError || error) && (
          <div className="flex items-start gap-3 p-4 bg-black border border-bmw-red/50 text-white rounded-none mb-6 text-xs uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-bmw-red shrink-0 mt-0.5" />
            <span className="font-light">{localError || error}</span>
          </div>
        )}

        {/* Auth form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-bmw-machined text-slateDark-muted mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slateDark-muted">
                <Mail className="w-4 h-4" />
              </span>
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                className="w-full bg-black border border-slateDark-border focus:border-white rounded-none py-3 pl-10 pr-4 text-white placeholder-slateDark-muted focus:outline-none focus:ring-0 transition duration-200 text-sm font-light"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-bmw-machined text-slateDark-muted mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slateDark-muted">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="w-full bg-black border border-slateDark-border focus:border-white rounded-none py-3 pl-10 pr-4 text-white placeholder-slateDark-muted focus:outline-none focus:ring-0 transition duration-200 text-sm font-light"
              />
            </div>
          </div>

          {!isLogin && (
            <div className="transition-all duration-300">
              <label className="block text-[11px] font-bold uppercase tracking-bmw-machined text-slateDark-muted mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slateDark-muted">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                  className="w-full bg-black border border-slateDark-border focus:border-white rounded-none py-3 pl-10 pr-4 text-white placeholder-slateDark-muted focus:outline-none focus:ring-0 transition duration-200 text-sm font-light"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-transparent hover:bg-white text-white hover:text-black border border-white rounded-none py-3.5 px-4 font-bold uppercase tracking-bmw-machined text-xs transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group active:scale-[0.98]"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <>
                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </>
            )}
          </button>
        </form>

        {/* Toggle mode trigger */}
        <div className="mt-8 pt-6 border-t border-slateDark-border text-center">
          <button
            onClick={toggleMode}
            disabled={loading}
            className="text-[11px] text-white hover:text-slateDark-muted uppercase tracking-bmw-machined transition-colors font-bold active:scale-95 duration-100"
          >
            {isLogin 
              ? "Don't have an account? Sign up" 
              : "Already have an account? Sign in"
            }
          </button>
        </div>

      </div>
    </div>
  );
};

export default AuthScreen;
