"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Home,
  Activity,
  Book,
  Users,
  FileDown,
  CheckSquare,
  Bell,
  Menu,
  X,
  BarChart,
  Target,
} from "lucide-react";

interface SidebarLinkProps {
  href: string;
  icon: React.ReactNode;
  label: string;
}

const SidebarLink = ({ href, icon, label }: SidebarLinkProps) => (
  <Link
    href={href}
    className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-colors"
  >
    <span className="w-5 h-5">{icon}</span>
    <span className="font-medium">{label}</span>
  </Link>
);

interface AdminSidebarProps {
  children: React.ReactNode;
}

export default function AdminSidebar({ children }: AdminSidebarProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navLinks = [
    { href: "/admin/dashboard", icon: <Home />, label: "Dashboard" },
    { href: "/admin/exercises", icon: <Activity />, label: "Exercises (Animations)" },
    { href: "/admin/coach-insights", icon: <Target />, label: "Coach Insights" },
    { href: "/admin/match-analysis", icon: <BarChart />, label: "Match Analysis" },
    { href: "/admin/teams", icon: <Users />, label: "Teams Management" },
    { href: "/admin/csv-import", icon: <FileDown />, label: "CSV Import" },
    { href: "/admin/homework", icon: <CheckSquare />, label: "Assigned Homework" },
    { href: "/admin/notifications", icon: <Bell />, label: "Notifications" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile header */}
      <div className="lg:hidden sticky top-0 z-40 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-md text-gray-600 hover:bg-gray-100"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <h1 className="text-xl font-bold text-gray-800">Admin Portal</h1>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar for desktop and mobile overlay */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out
            ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          `}
        >
          <div className="h-full flex flex-col">
            {/* Sidebar header */}
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800">xPalermoStat</h2>
              <p className="text-sm text-gray-500 mt-1">Administration Panel</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
              {navLinks.map((link) => (
                <SidebarLink key={link.href} {...link} />
              ))}
            </nav>

            {/* User profile footer */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  A
                </div>
                <div>
                  <p className="font-medium text-gray-800">Admin User</p>
                  <p className="text-sm text-gray-500">Administrator</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              {children}
            </div>
          </div>
        </main>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}