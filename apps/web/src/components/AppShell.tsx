"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const navigation = [
  {
    label: "Overview",
    href: "/",
  },
  {
    label: "Buildings",
    href: "/buildings",
  },
  {
    label: "Consumption",
    href: "/consumption",
  },
  {
    label: "Forecasts",
    href: "/forecasts",
  },
  {
    label: "Anomalies",
    href: "/anomalies",
  },
  {
    label: "Model Lab",
    href: "/model-lab",
  }
];

function isActive(
  pathname: string,
  href: string,
): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return (
    pathname === href ||
    pathname.startsWith(`${href}/`)
  );
}

export default function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#f6f8fb] text-slate-950">

      {/* =========================================================
          DESKTOP SIDEBAR
      ========================================================= */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] border-r border-slate-200 bg-white lg:block">

        {/* Brand */}
        <div className="flex h-[88px] items-center border-b border-slate-200 px-7">
          <Link
            href="/"
            className="group"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-sm font-semibold text-white shadow-sm">
                B
              </div>

              <div>
                <p className="text-sm font-semibold tracking-tight text-slate-950">
                  Building Intelligence
                </p>

                <p className="mt-0.5 text-xs text-slate-400">
                  Energy operations
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <div className="px-4 py-7">

          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            Workspace
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const active = isActive(
                pathname,
                item.href,
              );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                    active
                      ? "bg-slate-950 text-white shadow-sm"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-950"
                  }`}
                >
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-lg text-[11px] font-semibold transition ${
                      active
                        ? "bg-white/10 text-white"
                        : "bg-slate-50 text-slate-400 group-hover:bg-white group-hover:text-slate-700"
                    }`}
                  >
                    {item.href === "/"
                      ? "O"
                      : item.label.charAt(0)}
                  </span>

                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom status */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-slate-100 p-5">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />

              <span className="text-xs font-medium text-slate-600">
                System operational
              </span>
            </div>

            <p className="mt-2 text-[11px] leading-4 text-slate-400">
              Energy intelligence services are connected.
            </p>
          </div>
        </div>
      </aside>

      {/* =========================================================
          MOBILE HEADER
      ========================================================= */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur lg:hidden">
        <div className="px-5 py-4">

          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-3"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-sm font-semibold text-white">
                B
              </div>

              <div>
                <p className="text-sm font-semibold tracking-tight">
                  Building Intelligence
                </p>

                <p className="text-[11px] text-slate-400">
                  Energy operations
                </p>
              </div>
            </Link>

            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-600">
              OP
            </div>
          </div>

          <nav className="mt-4 flex gap-1 overflow-x-auto pb-1">
            {navigation.map((item) => {
              const active = isActive(
                pathname,
                item.href,
              );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition ${
                    active
                      ? "bg-slate-950 text-white"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* =========================================================
          MAIN CONTENT
      ========================================================= */}
      <div className="lg:pl-[248px]">
        <main>
          {children}
        </main>
      </div>
    </div>
  );
}