import Image from "next/image";
import Link from "next/link";

export const metadata = {
  title: "Palermo 1–1 Parma · Analyse-Dashboard · Barsport.club",
  description: "xG 1.78, PPDA 8.9, Schusskarte und IMR. Palermo unter der Datenlupe.",
};

export default function PalermoFocusPage() {
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white font-body">

      {/* ── HERO ──────────────────────────────────────────────────────── */}
      <div className="relative border-b border-slate-800/60 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 15% 60%, rgba(212,0,106,0.12) 0%, transparent 55%)" }} />

        <div className="relative max-w-[1280px] mx-auto px-5 md:px-8 pt-5 pb-6">

          <div className="flex items-center gap-2 mb-4">
            <Link href="/" className="text-[7px] font-black uppercase tracking-[0.26em] text-slate-600 hover:text-[#d4006a] transition-colors">← Magazin</Link>
            <span className="text-slate-800">·</span>
            <span className="text-[7px] font-black uppercase tracking-[0.26em] text-slate-700">21. April 2026 · Serie B Spieltag 34</span>
          </div>

          {/* Score */}
          <div className="flex flex-wrap items-center gap-5 mb-6">
            <div className="flex items-center gap-3">
              <Image src="/logos/Palermo.png" alt="Palermo" width={56} height={56} className="object-contain flex-shrink-0" unoptimized />
              <h1 className="font-heading text-5xl md:text-7xl font-black uppercase tracking-tight leading-none text-white"
                style={{ textShadow: "0 0 40px rgba(212,0,106,0.35)" }}>
                PALERMO
              </h1>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-slate-700 text-2xl">▶</span>
              <span className="font-heading text-5xl font-black tabular-nums text-white">1</span>
              <span className="text-slate-600 text-3xl font-black">–</span>
              <span className="font-heading text-5xl font-black tabular-nums text-slate-400">1</span>
            </div>
            <div className="flex items-center gap-3">
              <Image src="/logos/Parma.png" alt="Parma" width={48} height={48} className="object-contain" unoptimized />
              <span className="font-heading text-3xl font-black uppercase text-slate-400 tracking-tight">PARMA</span>
            </div>
          </div>

          {/* xG bar */}
          <div className="max-w-[560px] mb-5">
            <p className="text-[8px] font-black uppercase tracking-[0.28em] text-slate-500 mb-2">Expected Goals</p>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black tabular-nums text-[#d4006a]">1.78</span>
              <div className="flex-1 relative h-[6px] bg-slate-800 rounded-full overflow-hidden">
                <div className="absolute left-0 top-0 h-full rounded-full bg-[#d4006a]" style={{ width: "59%" }} />
              </div>
              <span className="text-2xl font-black text-slate-500 tabular-nums">1.22</span>
            </div>
          </div>

          {/* Stat cards */}
          <div className="flex flex-wrap gap-3 mb-5">
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[150px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Ballbesitz</p>
              <div className="flex items-end justify-between mb-2">
                <span className="font-heading text-3xl font-black text-[#d4006a]">56%</span>
                <span className="text-sm font-bold text-slate-600">44%</span>
              </div>
              <div className="h-[3px] bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-[#d4006a]" style={{ width: "56%" }} />
              </div>
              <div className="flex justify-between mt-1.5 text-[7px] text-slate-700 tabular-nums">
                <span>17 ▶ 2</span><span>15 ▶ 2</span>
              </div>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[110px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Schüsse</p>
              <div className="flex items-baseline gap-2">
                <span className="font-heading text-3xl font-black text-white">11</span>
                <span className="text-slate-600 text-sm">⚽</span>
                <span className="font-heading text-2xl font-black text-slate-500">13</span>
              </div>
              <p className="text-[7px] text-slate-700 mt-1">Aufs Tor: 4 — 5</p>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[100px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">PPDA</p>
              <span className="font-heading text-3xl font-black text-[#d4006a]">8.9</span>
              <p className="text-[7px] text-slate-600 mt-1.5">#5 per def. action</p>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[100px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Deep Compl.</p>
              <span className="font-heading text-3xl font-black text-[#d4006a]">52%</span>
              <p className="text-[7px] text-slate-600 mt-1.5">#5 zona finale</p>
            </div>
            <div className="flex items-center">
              <div className="bg-[#16a34a] hover:bg-[#15803d] text-white text-[8px] font-black uppercase tracking-[0.2em] px-5 py-3 rounded-sm cursor-pointer transition-colors">
                Match Report anzeigen →
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ── TRE COLONNE ───────────────────────────────────────────────── */}
      <div className="max-w-[1280px] mx-auto px-5 md:px-8 py-7">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* COL 1 — Match Report */}
          <div className="bg-[#121826] border border-slate-800 rounded-md p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-[2px] bg-[#d4006a]" />
              <h3 className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-400">Spielbericht Palermo – Parma</h3>
            </div>
            <p className="text-[7px] font-black uppercase tracking-[0.18em] text-slate-600 mb-2">Schusskarte</p>

            {/* Shot map */}
            <div className="relative bg-[#071a10] border border-slate-800 rounded-sm overflow-hidden" style={{ paddingBottom: "62%" }}>
              <div className="absolute inset-0">
                <div className="absolute inset-2 border border-[#0f3320] rounded-sm" />
                <div className="absolute top-2 bottom-2 left-1/2 border-l border-[#0f3320]" />
                <div className="absolute w-8 h-8 rounded-full border border-[#0f3320]" style={{ top: "50%", left: "50%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute border border-[#0f3320]" style={{ left: "8px", top: "22%", width: "17%", height: "56%" }} />
                <div className="absolute border border-[#0f3320]" style={{ right: "8px", top: "22%", width: "17%", height: "56%" }} />
                {/* Palermo shots pink */}
                <div className="absolute w-4 h-4 rounded-full bg-[#d4006a]"         style={{ top: "36%", left: "66%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-[#d4006a]/50"       style={{ top: "52%", left: "71%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-[#d4006a]/50"       style={{ top: "32%", left: "63%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-[#d4006a]/40"   style={{ top: "62%", left: "74%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-[#d4006a]/40"   style={{ top: "44%", left: "80%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2 h-2 rounded-full bg-[#d4006a]/35"       style={{ top: "56%", left: "59%", transform: "translate(-50%,-50%)" }} />
                {/* Parma shots amber */}
                <div className="absolute w-4 h-4 rounded-full bg-amber-500"          style={{ top: "40%", left: "28%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-amber-500/50"       style={{ top: "54%", left: "22%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-amber-500/50"       style={{ top: "35%", left: "32%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-amber-500/40"   style={{ top: "62%", left: "26%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2 h-2 rounded-full bg-amber-500/35"       style={{ top: "46%", left: "18%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute bottom-1.5 left-2 flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#d4006a]" />
                    <span className="text-[6px] font-bold uppercase text-slate-600">Palermo</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-amber-500" />
                    <span className="text-[6px] font-bold uppercase text-slate-600">Parma</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800">
              <p className="text-[8px] font-black uppercase tracking-[0.16em] text-slate-400 mb-2">Vollständige Taktikanalyse</p>
              <p className="text-xs text-slate-500 leading-relaxed mb-3">
                Die erweiterte Spielanalyse: xG, xA, die Schusskarte und taktische Betrachtungen zum Remis von Palermo gegen Parma.
              </p>
              <Link href="/blog/meritometro" className="text-[8px] font-black uppercase tracking-[0.18em] text-[#d4006a] hover:opacity-75 transition-opacity">
                Analyse lesen →
              </Link>
            </div>
          </div>

          {/* COL 2 — Classifica */}
          <div className="bg-[#121826] border border-slate-800 rounded-md p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-[2px] bg-[#d4006a]" />
              <h3 className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-400">Serie B Tabelle</h3>
            </div>
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 pb-2 border-b border-slate-800 mb-1">
              <span className="text-[7px] font-black uppercase text-slate-700">#</span>
              <span className="text-[7px] font-black uppercase text-slate-700">Team</span>
              <span className="text-[7px] font-black uppercase text-slate-700 text-center">GF</span>
              <span className="text-[7px] font-black uppercase text-slate-700 text-center">GA</span>
              <span className="text-[7px] font-black uppercase text-slate-700 text-center">Pkt</span>
            </div>

            {/* 1 Parma */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">1</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Parma</span>
              <span className="text-[9px] text-slate-600 text-center">64</span>
              <span className="text-[9px] text-slate-600 text-center">29</span>
              <span className="text-[10px] font-black text-slate-400 text-center">72</span>
            </div>
            {/* 2 Como */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">2</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Como</span>
              <span className="text-[9px] text-slate-600 text-center">60</span>
              <span className="text-[9px] text-slate-600 text-center">31</span>
              <span className="text-[10px] font-black text-slate-400 text-center">70</span>
            </div>
            {/* 3 Venezia */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">3</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Venezia</span>
              <span className="text-[9px] text-slate-600 text-center">56</span>
              <span className="text-[9px] text-slate-600 text-center">38</span>
              <span className="text-[10px] font-black text-slate-400 text-center">65</span>
            </div>
            {/* 4 Cremonese */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">4</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Cremonese</span>
              <span className="text-[9px] text-slate-600 text-center">52</span>
              <span className="text-[9px] text-slate-600 text-center">44</span>
              <span className="text-[10px] font-black text-slate-400 text-center">58</span>
            </div>
            {/* 5 PALERMO — evidenziato */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40 rounded-sm" style={{ backgroundColor: "#3d0020" }}>
              <span className="text-[9px] font-black text-[#d4006a]">5</span>
              <span className="text-[9px] font-black uppercase text-[#d4006a]">Palermo</span>
              <span className="text-[9px] text-slate-500 text-center">50</span>
              <span className="text-[9px] text-slate-500 text-center">46</span>
              <span className="text-[10px] font-black text-white text-center">56</span>
            </div>
            {/* 6 Catanzaro */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">6</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Catanzaro</span>
              <span className="text-[9px] text-slate-600 text-center">47</span>
              <span className="text-[9px] text-slate-600 text-center">47</span>
              <span className="text-[10px] font-black text-slate-400 text-center">53</span>
            </div>
            {/* 7 Brescia */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2">
              <span className="text-[9px] font-black text-slate-600">7</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Brescia</span>
              <span className="text-[9px] text-slate-600 text-center">43</span>
              <span className="text-[9px] text-slate-600 text-center">49</span>
              <span className="text-[10px] font-black text-slate-400 text-center">49</span>
            </div>

            <Link href="/tools" className="block mt-4 text-center text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 hover:text-slate-400 transition-colors pt-3 border-t border-slate-800">
              Komplette Tabelle anzeigen →
            </Link>
          </div>

          {/* COL 3 — Dati e Statistiche */}
          <div className="bg-[#121826] border border-slate-800 rounded-md p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-[2px] bg-[#d4006a]" />
              <h3 className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-400">Daten & Statistiken</h3>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-slate-900/60 rounded-sm p-3">
                <p className="text-[7px] font-black uppercase tracking-[0.18em] text-slate-600 mb-1">IMR Spiel</p>
                <div className="flex items-baseline justify-between">
                  <span className="font-heading text-3xl font-black text-[#d4006a]">52</span>
                  <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#6</span>
                </div>
              </div>
              <div className="bg-slate-900/60 rounded-sm p-3">
                <p className="text-[7px] font-black uppercase tracking-[0.18em] text-slate-600 mb-1">IMR Avvers.</p>
                <div className="flex items-baseline justify-between">
                  <span className="font-heading text-3xl font-black text-slate-400">48</span>
                  <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#5</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xG</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#d4006a]">1.78</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#6</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xA</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#d4006a]">1.23</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#5</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">PPDA</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#d4006a]">8.9</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#5</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">Deep Compl.</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#d4006a]">52%</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#5</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xGChain</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#d4006a]">63%</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#3</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800">
              <p className="text-[7px] font-black uppercase tracking-[0.2em] text-slate-600 mb-2">xG H2H</p>
              <div className="relative h-[4px] bg-slate-800 rounded-full overflow-hidden">
                <div className="absolute left-0 top-0 h-full rounded-full bg-[#d4006a]" style={{ width: "59%" }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[8px] font-black tabular-nums text-[#d4006a]">1.78</span>
                <span className="text-[8px] font-black tabular-nums text-slate-600">1.22</span>
              </div>
            </div>
            <Link href="/tools" className="block mt-4 text-center text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 hover:text-slate-400 transition-colors pt-3 border-t border-slate-800">
              Serie B Dashboard →
            </Link>
          </div>

        </div>
      </div>

      {/* ── ANALISI E APPROFONDIMENTI ─────────────────────────────────── */}
      <div className="max-w-[1280px] mx-auto px-5 md:px-8 pb-10">
        <div className="flex items-center gap-3 mb-4">
          <span className="w-5 h-[2px] bg-[#d4006a]" />
          <h3 className="text-[8px] font-black uppercase tracking-[0.28em] text-[#d4006a]">Analyse & Einblicke zu Palermo</h3>
          <span className="flex-1 h-px bg-slate-800" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="relative overflow-hidden bg-[#121826] border border-slate-800 rounded-md min-h-[200px]">
            <Image src="/palermo/AL1_0070-1920x1060.jpg" alt="Palermo match" fill className="object-cover object-center opacity-20" unoptimized />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0a0e17]/95 via-[#0a0e17]/60 to-transparent" />
            <div className="relative p-6">
              <p className="text-[7px] font-black uppercase tracking-[0.24em] text-slate-600 mb-2">Barsport.club · Analyse</p>
              <h4 className="font-heading text-lg font-black uppercase tracking-tight text-white leading-tight mb-3">
                BRUNORI: ERWEITERTE SAISONANALYSE
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed mb-5">
                Erweiterte Spielanalyse: xG, die Schusskarte und taktische Betrachtungen zum Remis von Palermo gegen Parma.
              </p>
              <Link href="/blog/meritometro" className="inline-flex items-center gap-2 text-[8px] font-black uppercase tracking-[0.2em] border border-[#d4006a] text-[#d4006a] px-4 py-2.5 rounded-sm hover:opacity-75 transition-opacity">
                Weiterlesen →
              </Link>
            </div>
          </div>
          <div className="relative overflow-hidden bg-[#121826] border border-slate-800 rounded-md min-h-[200px]">
            <Image src="/palermo/abbraccio.jpg" alt="Palermo squadra" fill className="object-cover object-center opacity-20" unoptimized />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0a0e17]/95 via-[#0a0e17]/60 to-transparent" />
            <div className="relative p-6">
              <p className="text-[7px] font-black uppercase tracking-[0.24em] text-slate-600 mb-2">Barsport.club · Hintergrund</p>
              <h4 className="font-heading text-lg font-black uppercase tracking-tight text-white leading-tight mb-3">
                TOP & FLOP: DIE ANALYSTEN-BEWERTUNGEN
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed mb-5">
                Die detaillierten Bewertungen jedes Rosanero-Spielers. Wer glänzte und wer in diesem Match enttäuschte.
              </p>
              <Link href="/blog/scout-engine" className="inline-flex items-center gap-2 text-[8px] font-black uppercase tracking-[0.2em] border border-slate-700 text-slate-400 px-4 py-2.5 rounded-sm hover:border-slate-500 hover:text-white transition-all">
                Weiterlesen →
              </Link>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
