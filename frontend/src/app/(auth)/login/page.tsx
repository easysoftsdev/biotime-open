"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import { Clock, Eye, EyeOff, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp] = useState("");
  const [showTotp, setShowTotp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password, totp || undefined);
      router.push("/dashboard");
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : "Login failed";
      if (msg.toLowerCase().includes("totp")) {
        setShowTotp(true);
        setError("Enter your 2FA code");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-indigo-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/25">
            <Clock className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">BioTime Open</h1>
          <p className="text-sm text-slate-400 mt-1">ZKTeco Attendance Platform</p>
        </div>

        {/* Card */}
        <div className="card p-6 shadow-2xl shadow-black/40">
          <h2 className="text-lg font-semibold text-white mb-1">Sign in</h2>
          <p className="text-sm text-slate-400 mb-6">Enter your admin credentials</p>

          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2.5 mb-4">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="admin@example.com"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {showTotp && (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">2FA Code</label>
                <input
                  type="text"
                  value={totp}
                  onChange={(e) => setTotp(e.target.value)}
                  className="input tracking-widest text-center text-lg"
                  placeholder="000 000"
                  maxLength={6}
                  autoFocus
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 h-10"
            >
              {loading && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          BioTime Open — MIT License · by EasySofts
        </p>
      </div>
    </div>
  );
}
