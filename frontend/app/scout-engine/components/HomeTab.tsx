"use client";
import React from "react";
import { Flame, Sparkles, ChevronRight } from "lucide-react";
import useSWR from "swr";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import { fetchLeaders, Leaders } from "../lib/scoutApi";

function LeaderList({ title, subtitle, Icon, accent, leaders, onLoad }: {
  title: string; subtitle: string; Icon: React.ElementType;
  accent: string; leaders: any[]; onLoad: (n: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 flex items-center gap-3 border-b border-slate-100">
        <Icon size={16} style={{ color: accent }} />
        <div>
          <h3 className="text-[#334155] font-black text-[14px] uppercase tracking-wider" style={{ fontFamily: "var(--font-oswald)" }}>{title}</h3>
          <p className="text-slate-400 text-[10px] uppercase tracking-widest">{subtitle}</p>
        </div>
      </div>
      {leaders.length === 0 ? (
        <div className="py-12 text-center text-slate-400 text-[12px] font-bold uppercase tracking-widest">
          {t("scout.backend_offline")}
        </div>
      ) : (
        leaders.map((l, i) => (
          <div
            key={i}
            onClick={() => onLoad(l.name)}
            className="flex items-center gap-4 px-6 py-4 border-b border-slate-50 last:border-0 cursor-pointer transition-colors hover:bg-slate-50"
          >
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-black"
              style={{ background: i === 0 ? accent : "#F1F5F9", color: i === 0 ? "#fff" : "#94A3B8" }}>
              {i + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-black text-[14px] uppercase text-[#334155] truncate" style={{ fontFamily: "var(--font-oswald)" }}>{l.name}</div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">{l.team}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="font-black text-[20px] leading-none" style={{ color: accent, fontFamily: "var(--font-oswald)" }}>
                {typeof l.value === "number" ? (l.value < 10 ? l.value.toFixed(2) : l.value) : l.value}
              </div>
              <div className="text-[9px] text-slate-400 uppercase tracking-wide">{l.stat}</div>
            </div>
            <ChevronRight size={14} className="text-slate-300 shrink-0" />
          </div>
        ))
      )}
    </div>
  );
}

export default function HomeTab({ onLoad }: { onLoad: (n: string) => void }) {
  const { t } = useTranslation();
  const { data } = useSWR<Leaders>("scout-leaders", fetchLeaders, {
    revalidateOnFocus: false, dedupingInterval: 300_000,
  });
  const leaders = data ?? { scorers: [], architects: [] };

  return (
    <div suppressHydrationWarning>
      <div className="mb-8">
        <h2 className="text-3xl font-black uppercase tracking-tighter text-[#334155] mb-1" style={{ fontFamily: "var(--font-oswald)" }}>
          {t("scout.european_intel")}
        </h2>
        <p className="text-slate-400 text-[11px] uppercase tracking-[0.2em]">{t("scout.top_performers_desc")}</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LeaderList title={t("scout.top_scorers")}    subtitle={t("scout.scorers_subtitle")} Icon={Flame}    accent="#FF2A6D" leaders={leaders.scorers}    onLoad={onLoad} />
        <LeaderList title={t("scout.top_architects")} subtitle={t("scout.architects_subtitle")} Icon={Sparkles} accent="#00D1FF" leaders={leaders.architects} onLoad={onLoad} />
      </div>
    </div>
  );
}
