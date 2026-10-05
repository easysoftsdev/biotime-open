"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { KeyRound, ShieldCheck, User } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Badge } from "@/components/ui/Badge";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { authApi } from "@/lib/api";
import { apiErrorMessage } from "@/lib/utils";
import { useAuth } from "@/store/auth";

export default function SettingsPage() {
  const { user } = useAuth();

  const [passwords, setPasswords] = useState({ current_password: "", new_password: "", confirm: "" });
  const [totpSecret, setTotpSecret] = useState<{ secret: string; uri: string } | null>(null);
  const [code, setCode] = useState("");

  const changePassword = useMutation({
    mutationFn: () => authApi.changePassword(passwords.current_password, passwords.new_password),
    onSuccess: () => {
      toast("success", "Password changed");
      setPasswords({ current_password: "", new_password: "", confirm: "" });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const setupTotp = useMutation({
    mutationFn: async () => (await authApi.totpSetup()).data,
    onSuccess: (data) => setTotpSecret(data),
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const verifyTotp = useMutation({
    mutationFn: () => authApi.totpVerify(code, totpSecret?.secret),
    onSuccess: () => {
      toast("success", "Two-factor authentication enabled");
      setTotpSecret(null);
      setCode("");
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const passwordValid =
    passwords.current_password &&
    passwords.new_password.length >= 8 &&
    passwords.new_password === passwords.confirm;

  return (
    <Page title="Settings" subtitle="Your account, security and 2FA">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 max-w-5xl">
        {/* Profile */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Profile</h2>
          </div>
          <div className="flex items-center gap-4 mb-5">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xl font-bold text-white">
              {user?.email?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div>
              <p className="text-sm font-medium text-white">{user?.email}</p>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="info">{user?.role?.replace("_", " ")}</Badge>
                <Badge variant={user?.totp_enabled ? "success" : "default"}>
                  {user?.totp_enabled ? "2FA on" : "2FA off"}
                </Badge>
              </div>
            </div>
          </div>
          <dl className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-[hsl(var(--border))] pb-2">
              <dt className="text-slate-500">User ID</dt>
              <dd className="text-slate-300 font-mono">{user?.id}</dd>
            </div>
            <div className="flex justify-between border-b border-[hsl(var(--border))] pb-2">
              <dt className="text-slate-500">Tenant</dt>
              <dd className="text-slate-300 font-mono">{user?.tenant_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Status</dt>
              <dd className="text-slate-300">{user?.is_active ? "Active" : "Disabled"}</dd>
            </div>
          </dl>
        </div>

        {/* Change password */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <KeyRound className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-semibold text-white">Change password</h2>
          </div>
          <div className="space-y-4">
            <Field label="Current password" required>
              <input
                type="password"
                className="input"
                value={passwords.current_password}
                onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })}
              />
            </Field>
            <Field label="New password" required hint="At least 8 characters">
              <input
                type="password"
                className="input"
                value={passwords.new_password}
                onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}
              />
            </Field>
            <Field
              label="Confirm new password"
              required
              error={
                passwords.confirm && passwords.new_password !== passwords.confirm
                  ? "Passwords do not match"
                  : undefined
              }
            >
              <input
                type="password"
                className="input"
                value={passwords.confirm}
                onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
              />
            </Field>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={!passwordValid || changePassword.isPending}
              onClick={() => changePassword.mutate()}
            >
              {changePassword.isPending ? "Updating…" : "Update password"}
            </button>
          </div>
        </div>

        {/* 2FA */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Two-factor authentication</h2>
          </div>

          {user?.totp_enabled ? (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <p className="text-sm text-emerald-300">
                TOTP is enabled on your account. You will be asked for a code at every sign-in.
              </p>
            </div>
          ) : totpSecret ? (
            <div className="space-y-4 max-w-md">
              <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))] px-4 py-3">
                <p className="text-[11px] text-slate-500 uppercase mb-1">Secret key</p>
                <p className="text-sm font-mono text-white break-all">{totpSecret.secret}</p>
              </div>
              <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))] px-4 py-3">
                <p className="text-[11px] text-slate-500 uppercase mb-1">Provisioning URI</p>
                <p className="text-xs font-mono text-slate-300 break-all">{totpSecret.uri}</p>
              </div>
              <Field label="Verification code" required hint="Enter the 6-digit code from your authenticator app">
                <input
                  className="input tracking-widest text-center text-lg"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  maxLength={6}
                  placeholder="000000"
                />
              </Field>
              <div className="flex gap-2">
                <button className="btn-ghost" onClick={() => setTotpSecret(null)}>
                  Cancel
                </button>
                <button
                  className="btn-primary disabled:opacity-50"
                  disabled={code.length !== 6 || verifyTotp.isPending}
                  onClick={() => verifyTotp.mutate()}
                >
                  {verifyTotp.isPending ? "Verifying…" : "Enable 2FA"}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs text-slate-500 max-w-lg">
                Protect your account with a time-based one-time password (TOTP). Scan the secret
                with Google Authenticator, Authy or 1Password.
              </p>
              <button
                className="btn-primary shrink-0 disabled:opacity-50"
                disabled={setupTotp.isPending}
                onClick={() => setupTotp.mutate()}
              >
                {setupTotp.isPending ? "Generating…" : "Set up 2FA"}
              </button>
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
