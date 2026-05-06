"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import { usePlayerReplacement } from "../hooks/usePlayerReplacement";
import SearchHub from "./SearchHub";

export default function ReplaceTab({ onLoadTarget }: { onLoadTarget: (n: string) => void }) {
  const { t } = useTranslation();
  const [targetName, setTargetName] = useState<string | null>(null);
  const [history, setHistory]       = useState<string[]>([]);
  const { data, isLoading }         = usePlayerReplacement(targetName);

  const drillDown = (name: string) => {
    if (targetName) setHistory(h => [...h, targetName]);
    setTargetName(name);
  };

  const goBack = (idx: number) => {
    const prev = history[idx];
    setHistory(h => h.slice(0, idx));
    setTargetName(prev);
  };

  const reset = () => { setTargetName(null); setHistory([]); };

  if (!targetName) {
    return (
      <SearchHub
        onSelect={name => { setHistory([]); setTargetName(name); }}
        context={t("scout.pse_title")}
      />
    );
  }

  return (
    <div suppressHydrationWarning>
      {/* Breadcrumb */}
      {history.length > 0 && (
        <div className="flex items-center gap-1 mb-4 flex-wrap">
          <button onClick={reset}
            className="text-[10px] text-slate-400 hover:text-[#FF2A6D] font-bold uppercase tracking-wide transition-colors">
            {t("common.search")}
          </button>
          {history.map((h, i) => (
            <React.Fragment key={i}>
              <ChevronRight size={12} className="text-slate-300 shrink-0" />
              <button onClick={() => goBack(i)}
                className="text-[10px] text-slate-400 hover:text-[#FF2A6D] font-bold uppercase tracking-wide transition-colors">
                {h}
              </button>
            </React.Fragment>
          ))}
          <ChevronRight size={12} className="text-slate-300 shrink-0" />
          <span className="text-[10px] font-black uppercase tracking-wide text-[#FF2A6D]">{targetName}</span>
        </div>
      )}

      {isLoading && (
        <div className="space-y-6 animate-pulse">
          <div className="bg-slate-100 rounded-2xl h-24" />
          <div className="grid grid-cols-5 gap-5">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="bg-slate-100 rounded-2xl h-72" />)}
          </div>
        </div>
      )}

      <AnimatePresence mode="wait">
        {!isLoading && data && (
          <motion.div key={targetName} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {/* Target bar */}
            <div className="bg-white shadow-sm border border-slate-100 border-l-[6px] border-l-[#FF2A6D] rounded-2xl px-8 py-5 mb-8 flex flex-wrap justify-between items-center gap-6">
              <div>
                <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">{t("scout.pse_algorithm")}</p>
                <h2 className="text-[#334155] font-black text-4xl uppercase tracking-tighter" style={{ fontFamily: "var(--font-oswald)" }}>
                  {data.target.name}
                </h2>
                <p className="text-slate-400 text-[11px] uppercase mt-1">{data.target.team} · {data.target.position} · PIR {data.target.scores.PIR.toFixed(4)}</p>
              </div>
              <div className="flex gap-8 text-center">
                {[
                  { l: "Algoritmo", v: t("scout.algo_euclidean"), c: "#FF2A6D" },
                  { l: "Vettore",   v: t("scout.algo_metrics"),   c: "#00D1FF" },
                  { l: "Pool",      v: t("scout.algo_scope"),     c: "#10B981" },
                ].map(({ l, v, c }) => (
                  <div key={l}>
                    <div className="font-black text-[16px]" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
                    <div className="text-slate-400 text-[9px] uppercase tracking-widest">{l}</div>
                  </div>
                ))}
              </div>
              <button onClick={reset} className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-red-500 font-bold uppercase transition-colors">
                <X size={12} /> {t("scout.reset")}
              </button>
            </div>

            {/* Clone cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
              {data.substitutes.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  onClick={() => drillDown(s.name)}
                  className="bg-white border border-slate-100 shadow-sm rounded-2xl p-5 cursor-pointer transition-all
                             hover:border-[#FF2A6D] hover:-translate-y-1 hover:shadow-md"
                >
                  <div className="flex justify-between items-start mb-4">
                    <span className="text-[10px] text-slate-400 font-black">#{i + 1}</span>
                    <div className="bg-[#FF2A6D]/10 border border-[#FF2A6D]/30 rounded-lg px-2.5 py-1.5 text-center">
                      <div className="font-black text-[18px] leading-none text-[#FF2A6D]" style={{ fontFamily: "var(--font-oswald)" }}>
                        {s.similarity_pct.toFixed(1)}%
                      </div>
                      <div className="text-[8px] text-slate-400 uppercase font-bold mt-0.5">Match</div>
                    </div>
                  </div>

                  <h4 className="font-black text-[18px] uppercase tracking-tight text-[#334155] mb-1 leading-none"
                    style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</h4>
                  <p className="text-[10px] text-slate-400 uppercase font-bold mb-4">{s.team} · {s.position}</p>

                  {[
                    { k: "xg", l: "xG/90", c: "#FF2A6D", max: 0.5 },
                    { k: "xa", l: "xA/90", c: "#00D1FF", max: 0.4 },
                    { k: "xgchain", l: "xGChain", c: "#F59E0B", max: 0.8 },
                  ].map(({ k, l, c, max }) => {
                    const sv = s.p90[k] ?? 0;
                    return (
                      <div key={k} className="mb-3">
                        <div className="flex justify-between mb-1">
                          <span className="text-[9px] text-slate-400 uppercase font-bold">{l}</span>
                          <span className="text-[10px] font-black" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{sv.toFixed(3)}</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${Math.min(100, sv / max * 100)}%`, background: c }} />
                        </div>
                      </div>
                    );
                  })}

                  <div className="flex justify-between items-center pt-3 border-t border-slate-100 mt-1">
                    <span className="text-[9px] text-slate-400 uppercase font-bold">PIR</span>
                    <span className="font-black text-[13px] text-[#FF2A6D]" style={{ fontFamily: "var(--font-oswald)" }}>
                      {s.scores.PIR.toFixed(4)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
