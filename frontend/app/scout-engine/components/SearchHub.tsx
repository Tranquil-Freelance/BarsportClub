"use client";
import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Activity } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import { usePlayerSearch } from "../hooks/usePlayerSearch";

interface Props {
  onSelect: (name: string) => void;
  placeholder?: string;
  context?: string;
  pills?: { name: string; team: string }[];
  autoFocus?: boolean;
  size?: "sm" | "lg";
}

export default function SearchHub({ onSelect, placeholder, context, pills, autoFocus, size = "lg" }: Props) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [show, setShow] = useState(false);
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedQ, setDebouncedQ] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const { suggestions, isLoading } = usePlayerSearch(debouncedQ);

  const handleChange = (val: string) => {
    setQ(val);
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(() => {
      setDebouncedQ(val);
      setShow(val.trim().length >= 2);
    }, 300);
  };

  const handleSelect = (name: string) => {
    setQ(""); setDebouncedQ(""); setShow(false);
    onSelect(name);
  };

  const isLg = size === "lg";

  return (
    <div className={isLg ? "flex flex-col items-center py-14 px-4" : "relative w-full"} suppressHydrationWarning>
      {isLg && context && (
        <div className="mb-10 text-center">
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.4em] mb-3">{context}</p>
          <h2 className="font-black text-5xl md:text-6xl uppercase tracking-tighter text-[#334155] leading-none mb-3"
            style={{ fontFamily: "var(--font-oswald)" }}>
            {t("scout.analyze_player")}
          </h2>
          <p className="text-slate-400 text-[13px]">Top 5 leghe europee · Stagione 25/26 · Min. 500'</p>
        </div>
      )}

      <div className={`relative ${isLg ? "w-full max-w-2xl" : "w-full"}`}>
        <div
          className={`flex items-center bg-white border-2 border-slate-200 rounded-2xl gap-3 shadow-sm
                      focus-within:border-[#FF2A6D] focus-within:shadow-[0_8px_40px_rgba(255,42,109,0.10)]
                      transition-all duration-200 ${isLg ? "px-5 py-4" : "px-4 py-3"}`}
        >
          <Search size={isLg ? 20 : 16} className="text-slate-400 shrink-0" />
          <input
            ref={inputRef}
            value={q}
            onChange={e => handleChange(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && suggestions.length) handleSelect(suggestions[0].name); }}
            placeholder={placeholder ?? t("scout.search_name_placeholder")}
            className={`flex-1 bg-transparent outline-none text-[#334155] font-bold placeholder:text-slate-400 placeholder:font-normal ${isLg ? "text-[15px]" : "text-[13px]"}`}
            style={{ fontFamily: "var(--font-oswald)" }}
            autoFocus={autoFocus}
          />
          {isLoading && <Activity size={15} className="text-[#FF2A6D] shrink-0 animate-spin" />}
          {q && !isLoading && (
            <button onClick={() => { setQ(""); setDebouncedQ(""); setShow(false); }} className="text-slate-400 hover:text-slate-600 transition-colors shrink-0">
              <X size={15} />
            </button>
          )}
        </div>

        <AnimatePresence>
          {show && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="absolute top-full left-0 right-0 bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto mt-2"
            >
              {suggestions.map((s, i) => (
                <div key={i} onClick={() => handleSelect(s.name)}
                  className="flex justify-between items-center px-5 py-3.5 cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#FF2A6D] shrink-0" />
                    <span className="font-black text-[13px] uppercase text-[#334155]"
                      style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</span>
                  </div>
                  {s.team && <span className="text-[10px] text-slate-400 font-medium shrink-0 ml-3">{s.team}</span>}
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {isLg && pills && pills.length > 0 && (
        <div className="mt-10 max-w-2xl w-full">
          <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400 mb-4 text-center">{t("scout.serie_a_stars")}</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {pills.map(s => (
              <button key={s.name} onClick={() => handleSelect(s.name)}
                className="group inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 shadow-sm
                           hover:border-[#FF2A6D] hover:shadow-[0_4px_20px_rgba(255,42,109,0.12)] hover:-translate-y-0.5
                           transition-all duration-200 cursor-pointer">
                <span className="text-[#334155] text-[12px] font-black uppercase group-hover:text-[#FF2A6D] transition-colors"
                  style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</span>
                <span className="text-slate-400 text-[9px] font-medium">{s.team}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
