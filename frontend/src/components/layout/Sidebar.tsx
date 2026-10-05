"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/store/auth";
import {
  LayoutDashboard, Monitor, Users, Clock, Calendar,
  Umbrella, Wallet, Link2, BarChart3, LogOut, Settings,
} from "lucide-react";

const NAV = [
  { label: "Dashboard",    href: "/dashboard",   icon: LayoutDashboard },
  { label: "Devices",      href: "/devices",      icon: Monitor },
  { label: "Employees",    href: "/employees",    icon: Users },
  { label: "Attendance",   href: "/attendance",   icon: Clock },
  { label: "Shifts",       href: "/shifts",       icon: Calendar },
  { label: "Leave",        href: "/leave",        icon: Umbrella },
  { label: "Payroll",      href: "/payroll",      icon: Wallet },
  { label: "HRM Push",     href: "/hrm-push",     icon: Link2 },
  { label: "Reports",      href: "/reports",      icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-60 shrink-0 h-screen flex flex-col bg-[hsl(var(--card))] border-r border-[hsl(var(--border))]">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-[hsl(var(--border))]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
            <Clock className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-none">BioTime</p>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5">Open Source</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                active
                  ? "bg-blue-600/15 text-blue-400 font-medium"
                  : "text-slate-400 hover:text-slate-100 hover:bg-[hsl(var(--muted))]"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-3 py-3 border-t border-[hsl(var(--border))] space-y-0.5">
        <Link href="/settings" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-slate-100 hover:bg-[hsl(var(--muted))] transition-colors">
          <Settings className="w-4 h-4" />
          Settings
        </Link>
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
            {user?.email?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-200 truncate">{user?.email}</p>
            <p className="text-[10px] text-slate-500 capitalize">{user?.role?.replace("_", " ")}</p>
          </div>
          <button onClick={logout} className="text-slate-500 hover:text-red-400 transition-colors">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
