"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import TeamLogo from "@/components/TeamLogo";

// ── Types ──────────────────────────────────────────────────────────────────
type Standing = {
  pos: number;
  name: string;
  pts: number;
  played?: number;
  won?: number;
  drawn?: number;
};

type MeritRow = {
  name: string;
  total_imr: number;
};

// ── Constants ──────────────────────────────────────────────────────────────
const LEAGUES = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"];

const API_ORIGIN =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(
    /\/api\/v1$/,
    ""
  );

// ── Framer-motion variants ─────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

// ── Helpers ────────────────────────────────────────────────────────────────

function CoverImage({ src, alt }: { src: string; alt: string }) {
  const [errored, setErrored] = useState(false);
  if (errored) return null;
  return (
    <Image
      src={src}
      alt={alt}
      fill
      className="object-cover object-center"
      onError={() => setErrored(true)}
      unoptimized
    />
  );
}

function secureHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem("admin_api_key");
  return key ? { "X-ADMIN-API-KEY": key } : {};
}

// ── Component ──────────────────────────────────────────────────────────────
export default function ToolsPage() {
  const { t } = useTranslation();

  const [activeLeague, setActiveLeague] = useState("Serie A");
  const [topTeams, setTopTeams] = useState<Standing[]>([]);
  const [topMerit, setTopMerit] = useState<MeritRow[]>([]);
  const [loadingStandings, setLoadingStandings] = useState(true);
  const [loadingMerit, setLoadingMerit] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingStandings(true);
    fetch(
      `${API_ORIGIN}/api/standings?league=${encodeURIComponent(activeLeague)}`,
      { headers: secureHeaders(), signal: controller.signal }
    )
      .then((r) => (r.ok ? r.json() : []))
      .then((data: Standing[]) => setTopTeams(data.slice(0, 5)))
      .catch((err) => { if (err.name !== "AbortError") setTopTeams([]); })
      .finally(() => setLoadingStandings(false));
    return () => controller.abort();
  }, [activeLeague]);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingMerit(true);
    fetch(
      `${API_ORIGIN}/api/meritometro/imr_standings?league=${encodeURIComponent(activeLeague)}`,
      { headers: secureHeaders(), signal: controller.signal }
    )
      .then((r) => (r.ok ? r.json() : []))
      .then((data: MeritRow[]) => setTopMerit(data.slice(0, 5)))
      .catch((err) => { if (err.name !== "AbortError") setTopMerit([]); })
      .finally(() => setLoadingMerit(false));
    return () => controller.abort();
  }, [activeLeague]);

  const maxImr = topMerit[0]?.total_imr ?? 1;

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0f172a] font-body">

      {/* ── LEAGUE SUB-BAR ── */}
      <div className="w-full bg-[#0d2137] border-b border-white/5 h-10 flex items-center px-6 sticky top-[48px] z-40">
        <span className="text-white/35 text-[8px] font-black uppercase tracking-[0.22em] mr-6 flex-shrink-0 hidden sm:block">
          {t("home.db_active")}
        </span>
        <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
          {LEAGUES.map((league) => (
            <button
              key={league}
              onClick={() => setActiveLeague(league)}
              className={`text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded-full transition-all flex-shrink-0 ${
                activeLeague === league
                  ? "bg-[#ff0055] text-white shadow-[0_0_10px_rgba(255,0,85,0.35)]"
                  : "text-white/40 hover:text-white"
              }`}
            >
              {league}
            </button>
          ))}
        </div>
      </div>

      {/* ── EDITORIAL GRID ── */}
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_272px] gap-8 items-start">

          {/* ── MAIN COLUMN ── */}
          <motion.div
            className="flex flex-col gap-6"
            variants={stagger}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={fadeUp} className="flex items-center gap-2">
              <span className="block w-4 h-0.5 bg-[#ff0055]" />
              <span className="text-[#ff0055] text-[8px] font-black uppercase tracking-[0.22em]">
                {t("home.analysis_of_week")}
              </span>
            </motion.div>

            {/* HERO STORY */}
            <motion.article variants={fadeUp}>
              <div className="relative w-full h-[300px] bg-[#0a192f] rounded-sm overflow-hidden mb-4">
                <CoverImage src="/images/home/meritometro-cover.webp" alt={t("home.hero_img_title")} />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a192f]/88 via-[#0a192f]/10 to-transparent" />
                <div className="absolute bottom-0 left-0 p-4 z-10">
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.22em] mb-1">
                    {t("home.hero_category")}
                  </p>
                  <p className="text-white font-heading text-lg font-black uppercase leading-tight">
                    {t("home.hero_img_title")}
                  </p>
                </div>
              </div>

              <h1 className="font-heading text-[26px] md:text-[30px] font-black uppercase leading-[1.08] tracking-tight text-[#0a192f] mb-3">
                {t("home.hero_headline_pre")}{" "}
                <em className="text-[#ff0055] not-italic">
                  {t("home.hero_headline_hot")}
                </em>
              </h1>

              <p className="text-[#475569] text-sm leading-relaxed border-l-[3px] border-[#e2e8f0] pl-3 mb-4">
                {t("home.hero_deck")}
              </p>

              <div className="flex items-center gap-3 flex-wrap">
                <Link
                  href="/meritometro"
                  className="text-[8px] font-black uppercase tracking-[0.14em] text-[#0a192f] bg-[#f1f5f9] px-4 py-2 rounded-sm border border-[#e2e8f0] hover:bg-[#e2e8f0] transition-colors"
                >
                  {t("home.read_full_analysis")} →
                </Link>
                <span className="text-[9px] text-[#94a3b8]">{t("home.hero_date")}</span>
              </div>
            </motion.article>

            <motion.hr variants={fadeUp} className="border-[#e2e8f0]" />

            {/* SECONDARY GRID */}
            <motion.div variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <motion.article variants={fadeUp}>
                <Link href="/scout-engine" className="group block">
                  <div className="relative w-full h-[130px] bg-[#1e293b] rounded-sm overflow-hidden mb-2.5">
                    <CoverImage src="/images/home/scout-cover.webp" alt={t("home.sec1_title")} />
                  </div>
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.18em] mb-1">
                    {t("home.sec1_cat")}
                  </p>
                  <h3 className="font-heading text-sm font-black uppercase leading-snug text-[#0a192f] group-hover:text-[#ff0055] transition-colors duration-200">
                    {t("home.sec1_title")}
                  </h3>
                </Link>
              </motion.article>

              <motion.article variants={fadeUp}>
                <Link href="/nerd-zone" className="group block">
                  <div className="relative w-full h-[130px] bg-[#0f2044] rounded-sm overflow-hidden mb-2.5">
                    <CoverImage src="/images/home/nerdzone-cover.webp" alt={t("home.sec2_title")} />
                  </div>
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.18em] mb-1">
                    {t("home.sec2_cat")}
                  </p>
                  <h3 className="font-heading text-sm font-black uppercase leading-snug text-[#0a192f] group-hover:text-[#ff0055] transition-colors duration-200">
                    {t("home.sec2_title")}
                  </h3>
                </Link>
              </motion.article>
            </motion.div>

          </motion.div>

          {/* ── SIDEBAR ── */}
          <motion.aside
            className="flex flex-col gap-6 lg:sticky lg:top-[96px]"
            variants={stagger}
            initial="hidden"
            animate="visible"
          >
            {/* MERITOMETRO WIDGET */}
            <motion.div variants={fadeUp} className="bg-white p-4 shadow-sm border border-[#f1f5f9]">
              <div className="border-l-[3px] border-[#0a192f] pl-2 mb-3 flex items-baseline justify-between">
                <h4 className="text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f]">
                  {t("home.widget_merit_title")}
                </h4>
                <span className="text-[7px] font-bold text-[#94a3b8] uppercase tracking-wider">
                  {activeLeague}
                </span>
              </div>

              {loadingMerit ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-6 bg-[#f1f5f9] rounded animate-pulse" />
                  ))}
                </div>
              ) : topMerit.length === 0 ? (
                <p className="text-[10px] text-[#94a3b8] font-bold uppercase py-2">
                  {t("common.no_data")}
                </p>
              ) : (
                <div>
                  {topMerit.map((row, i) => (
                    <div
                      key={row.name}
                      className="grid grid-cols-[18px_1fr_48px_52px] items-center gap-1.5 py-1.5 border-b border-[#f1f5f9] last:border-0"
                    >
                      <span className="text-[9px] font-black text-[#cbd5e1] text-center tabular-nums">
                        {i + 1}
                      </span>
                      <span className="text-[10px] font-black uppercase tracking-tight text-[#0f172a] truncate">
                        {row.name}
                      </span>
                      <span className="text-[12px] font-black text-[#ff0055] text-right tabular-nums">
                        {Math.round(row.total_imr)}
                      </span>
                      <div className="h-[3px] bg-[#f1f5f9] rounded overflow-hidden">
                        <div
                          className="h-[3px] bg-[#ff0055] rounded opacity-65"
                          style={{ width: `${(row.total_imr / maxImr) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>

            {/* STANDINGS WIDGET */}
            <motion.div variants={fadeUp} className="bg-white p-4 shadow-sm border border-[#f1f5f9]">
              <div className="border-l-[3px] border-[#0a192f] pl-2 mb-3 flex items-baseline justify-between">
                <h4 className="text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f]">
                  {t("home.widget_standings_title")} · {activeLeague}
                </h4>
                <span className="text-[7px] font-bold text-[#94a3b8] uppercase tracking-wider">Top 5</span>
              </div>

              <div className="grid grid-cols-[18px_1fr_22px_22px_22px_28px] gap-1 pb-2 border-b border-[#e2e8f0] mb-1">
                {["#", t("common.team"), "G", "W", "D", "PTS"].map((h) => (
                  <span
                    key={h}
                    className={`text-[7px] font-black uppercase tracking-wider text-[#94a3b8] text-center ${h === t("common.team") ? "text-left" : ""}`}
                  >
                    {h}
                  </span>
                ))}
              </div>

              {loadingStandings ? (
                <div className="space-y-1.5 pt-1">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-5 bg-[#f1f5f9] rounded animate-pulse" />
                  ))}
                </div>
              ) : topTeams.length === 0 ? (
                <p className="text-[10px] text-[#94a3b8] font-bold uppercase py-2">
                  {t("common.no_data")}
                </p>
              ) : (
                topTeams.map((team) => (
                  <div
                    key={team.name}
                    className="grid grid-cols-[18px_1fr_22px_22px_22px_28px] items-center gap-1 py-1.5 border-b border-[#f8f9fb] last:border-0"
                  >
                    <span className="text-[9px] font-black text-[#94a3b8] text-center tabular-nums">
                      {team.pos}
                    </span>
                    <div className="flex items-center gap-1.5 min-w-0">
                      <TeamLogo teamName={team.name} size={14} />
                      <span className="text-[9px] font-black uppercase tracking-tight text-[#0f172a] truncate">
                        {team.name}
                      </span>
                    </div>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.played ?? "–"}
                    </span>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.won ?? "–"}
                    </span>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.drawn ?? "–"}
                    </span>
                    <span className="text-[10px] font-black text-[#0a192f] text-center tabular-nums">
                      {team.pts}
                    </span>
                  </div>
                ))
              )}
            </motion.div>

            {/* MODULE PROMO CARDS */}
            {(
              [
                {
                  href: "/scout-engine",
                  titleKey: "home.mod_scout_title",
                  tagKey: "home.mod_scout_tag",
                  descKey: "home.mod_scout_desc",
                  ctaKey: "home.mod_scout_cta",
                },
                {
                  href: "/fanta-draft",
                  titleKey: "home.mod_fanta_title",
                  tagKey: "home.mod_fanta_tag",
                  descKey: "home.mod_fanta_desc",
                  ctaKey: "home.mod_fanta_cta",
                },
                {
                  href: "/nerd-zone",
                  titleKey: "home.mod_nerd_title",
                  tagKey: "home.mod_nerd_tag",
                  descKey: "home.mod_nerd_desc",
                  ctaKey: "home.mod_nerd_cta",
                },
              ] as const
            ).map((mod) => (
              <motion.div
                key={mod.href}
                variants={fadeUp}
                className="border border-[#e2e8f0] rounded-sm overflow-hidden shadow-sm"
              >
                <div className="bg-[#0a192f] px-3 py-2 flex items-center justify-between">
                  <h5 className="text-[8px] font-black uppercase tracking-[0.18em] text-white">
                    {t(mod.titleKey)}
                  </h5>
                  <span className="text-[7px] font-black uppercase tracking-wider text-[#ff0055]">
                    {t(mod.tagKey)}
                  </span>
                </div>
                <div className="bg-white px-3 py-3">
                  <p className="text-[10px] text-[#475569] leading-relaxed mb-2">
                    {t(mod.descKey)}
                  </p>
                  <Link
                    href={mod.href}
                    className="text-[8px] font-black uppercase tracking-[0.14em] text-[#0a192f] flex items-center gap-1 hover:text-[#ff0055] transition-colors duration-200 group"
                  >
                    {t(mod.ctaKey)}
                    <span className="text-[#ff0055] group-hover:translate-x-0.5 transition-transform duration-200">
                      →
                    </span>
                  </Link>
                </div>
              </motion.div>
            ))}

          </motion.aside>

        </div>
      </div>
    </div>
  );
}
