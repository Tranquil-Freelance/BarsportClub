import Image from "next/image";
import Link from "next/link";

export const metadata = {
  title: "Como 2–1 Venezia · Analyse-Dashboard · Barsport.club",
  description: "xG 2.11, PPDA 8.1, Schusskarte und IMR. Como unter der Datenlupe.",
};

export default function ComoFocusPage() {
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white font-body">

      {/* ── HERO ──────────────────────────────────────────────────────── */}
      <div className="relative border-b border-slate-800/60 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 15% 60%, rgba(0,51,160,0.14) 0%, transparent 55%)" }} />

        <div className="relative max-w-[1280px] mx-auto px-5 md:px-8 pt-5 pb-6">

          <div className="flex items-center gap-2 mb-4">
            <Link href="/" className="text-[7px] font-black uppercase tracking-[0.26em] text-slate-600 hover:text-[#0055cc] transition-colors">← Magazin</Link>
            <span className="text-slate-800">·</span>
            <span className="text-[7px] font-black uppercase tracking-[0.26em] text-slate-700">21. April 2026 · Serie B Spieltag 34</span>
          </div>

          {/* Score */}
          <div className="flex flex-wrap items-center gap-5 mb-6">
            <div className="flex items-center gap-3">
              <Image src="/logos/Como.png" alt="Como" width={56} height={56} className="object-contain flex-shrink-0" unoptimized />
              <h1 className="font-heading text-5xl md:text-7xl font-black uppercase tracking-tight leading-none text-white"
                style={{ textShadow: "0 0 40px rgba(0,80,200,0.4)" }}>
                COMO
              </h1>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-slate-700 text-2xl">▶</span>
              <span className="font-heading text-5xl font-black tabular-nums text-white">2</span>
              <span className="text-slate-600 text-3xl font-black">–</span>
              <span className="font-heading text-5xl font-black tabular-nums text-slate-400">1</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full border border-slate-700 bg-slate-800 flex items-center justify-center flex-shrink-0">
                <span className="text-slate-400 text-[10px] font-black">VEN</span>
              </div>
              <span className="font-heading text-3xl font-black uppercase text-slate-400 tracking-tight">VENEZIA</span>
            </div>
          </div>

          {/* xG bar */}
          <div className="max-w-[560px] mb-5">
            <p className="text-[8px] font-black uppercase tracking-[0.28em] text-slate-500 mb-2">Expected Goals</p>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black tabular-nums text-[#0066ff]">2.11</span>
              <div className="flex-1 relative h-[6px] bg-slate-800 rounded-full overflow-hidden">
                <div className="absolute left-0 top-0 h-full rounded-full bg-[#0066ff]" style={{ width: "76%" }} />
              </div>
              <span className="text-2xl font-black text-slate-500 tabular-nums">0.67</span>
            </div>
          </div>

          {/* Stat cards */}
          <div className="flex flex-wrap gap-3 mb-5">
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[150px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Ballbesitz</p>
              <div className="flex items-end justify-between mb-2">
                <span className="font-heading text-3xl font-black text-[#0066ff]">57%</span>
                <span className="text-sm font-bold text-slate-600">43%</span>
              </div>
              <div className="h-[3px] bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-[#0066ff]" style={{ width: "57%" }} />
              </div>
              <div className="flex justify-between mt-1.5 text-[7px] text-slate-700 tabular-nums">
                <span>15 ▶ 4</span><span>8 ▶ 3</span>
              </div>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[110px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Schüsse</p>
              <div className="flex items-baseline gap-2">
                <span className="font-heading text-3xl font-black text-white">15</span>
                <span className="text-slate-600 text-sm">⚽</span>
                <span className="font-heading text-2xl font-black text-slate-500">8</span>
              </div>
              <p className="text-[7px] text-slate-700 mt-1">Aufs Tor: 5 — 3</p>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[100px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">PPDA</p>
              <span className="font-heading text-3xl font-black text-[#0066ff]">8.1</span>
              <p className="text-[7px] text-slate-600 mt-1.5">#3 per def. action</p>
            </div>
            <div className="bg-[#121826] border border-slate-800 rounded-md p-4 min-w-[100px]">
              <p className="text-[7px] font-black uppercase tracking-[0.22em] text-slate-600 mb-2">Deep Compl.</p>
              <span className="font-heading text-3xl font-black text-[#0066ff]">54%</span>
              <p className="text-[7px] text-slate-600 mt-1.5">#6 zona finale</p>
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
              <span className="w-3 h-[2px] bg-[#0066ff]" />
              <h3 className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-400">Spielbericht Como – Venezia</h3>
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
                {/* Como shots blue */}
                <div className="absolute w-4 h-4 rounded-full bg-[#0066ff]"        style={{ top: "38%", left: "68%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-4 h-4 rounded-full bg-[#0066ff]"        style={{ top: "50%", left: "73%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-[#0066ff]/50"     style={{ top: "30%", left: "65%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-3 h-3 rounded-full bg-[#0066ff]/50"     style={{ top: "64%", left: "76%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-[#0066ff]/40" style={{ top: "44%", left: "82%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-[#0066ff]/40" style={{ top: "56%", left: "61%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2 h-2 rounded-full bg-[#0066ff]/35"     style={{ top: "35%", left: "79%", transform: "translate(-50%,-50%)" }} />
                {/* Venezia shots amber */}
                <div className="absolute w-3 h-3 rounded-full bg-amber-500"        style={{ top: "42%", left: "26%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-amber-500/50" style={{ top: "55%", left: "20%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2.5 h-2.5 rounded-full bg-amber-500/50" style={{ top: "34%", left: "30%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute w-2 h-2 rounded-full bg-amber-500/35"     style={{ top: "62%", left: "24%", transform: "translate(-50%,-50%)" }} />
                <div className="absolute bottom-1.5 left-2 flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#0066ff]" />
                    <span className="text-[6px] font-bold uppercase text-slate-600">Como</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-amber-500" />
                    <span className="text-[6px] font-bold uppercase text-slate-600">Venezia</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800">
              <p className="text-[8px] font-black uppercase tracking-[0.16em] text-slate-400 mb-2">Vollständige Taktikanalyse</p>
              <p className="text-xs text-slate-500 leading-relaxed mb-3">
                Die erweiterte Spielanalyse: xG, xA, die Schusskarte und taktische Betrachtungen zum Sieg von Como gegen Venezia.
              </p>
              <Link href="/blog/meritometro" className="text-[8px] font-black uppercase tracking-[0.18em] text-[#0066ff] hover:opacity-75 transition-opacity">
                Analyse lesen →
              </Link>
            </div>
          </div>

          {/* COL 2 — Classifica */}
          <div className="bg-[#121826] border border-slate-800 rounded-md p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-3 h-[2px] bg-[#0066ff]" />
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
            {/* 2 COMO — evidenziato */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40 rounded-sm" style={{ backgroundColor: "#001a4d" }}>
              <span className="text-[9px] font-black text-[#0066ff]">2</span>
              <span className="text-[9px] font-black uppercase text-[#0066ff]">Como</span>
              <span className="text-[9px] text-slate-500 text-center">60</span>
              <span className="text-[9px] text-slate-500 text-center">31</span>
              <span className="text-[10px] font-black text-white text-center">70</span>
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
            {/* 5 Palermo */}
            <div className="grid grid-cols-[22px_1fr_28px_28px_32px] gap-1 items-center py-2 border-b border-slate-800/40">
              <span className="text-[9px] font-black text-slate-600">5</span>
              <span className="text-[9px] font-black uppercase text-slate-400">Palermo</span>
              <span className="text-[9px] text-slate-600 text-center">50</span>
              <span className="text-[9px] text-slate-600 text-center">46</span>
              <span className="text-[10px] font-black text-slate-400 text-center">56</span>
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
              <span className="w-3 h-[2px] bg-[#0066ff]" />
              <h3 className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-400">Daten & Statistiken</h3>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-slate-900/60 rounded-sm p-3">
                <p className="text-[7px] font-black uppercase tracking-[0.18em] text-slate-600 mb-1">IMR Partita</p>
                <div className="flex items-baseline justify-between">
                  <span className="font-heading text-3xl font-black text-[#0066ff]">61</span>
                  <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#3</span>
                </div>
              </div>
              <div className="bg-slate-900/60 rounded-sm p-3">
                <p className="text-[7px] font-black uppercase tracking-[0.18em] text-slate-600 mb-1">IMR Avvers.</p>
                <div className="flex items-baseline justify-between">
                  <span className="font-heading text-3xl font-black text-slate-400">39</span>
                  <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#7</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xG</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#0066ff]">2.11</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#3</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xA</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#0066ff]">0.85</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#3</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">PPDA</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#0066ff]">8.1</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#3</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5 border-b border-slate-800/50">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">Deep Compl.</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#0066ff]">54%</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#6</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2.5">
              <span className="text-[8px] font-black uppercase tracking-wider text-slate-500">xGChain</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black tabular-nums text-[#0066ff]">58%</span>
                <span className="text-[7px] bg-slate-800 text-slate-400 font-black rounded px-1.5 py-0.5">#6</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800">
              <p className="text-[7px] font-black uppercase tracking-[0.2em] text-slate-600 mb-2">xG H2H</p>
              <div className="relative h-[4px] bg-slate-800 rounded-full overflow-hidden">
                <div className="absolute left-0 top-0 h-full rounded-full bg-[#0066ff]" style={{ width: "76%" }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[8px] font-black tabular-nums text-[#0066ff]">2.11</span>
                <span className="text-[8px] font-black tabular-nums text-slate-600">0.67</span>
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
          <span className="w-5 h-[2px] bg-[#0066ff]" />
          <h3 className="text-[8px] font-black uppercase tracking-[0.28em] text-[#0066ff]">Analyse & Einblicke zum Como</h3>
          <span className="flex-1 h-px bg-slate-800" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="relative overflow-hidden bg-[#121826] border border-slate-800 rounded-md min-h-[200px]">
            <div className="absolute inset-0" style={{ background: "linear-gradient(135deg, rgba(0,60,180,0.25) 0%, transparent 60%)" }} />
            <div className="relative p-6">
              <p className="text-[7px] font-black uppercase tracking-[0.24em] text-slate-600 mb-2">Barsport.club · Analyse</p>
              <h4 className="font-heading text-lg font-black uppercase tracking-tight text-white leading-tight mb-3">
                COMO ALS PROTAGONIST: DER TRAUM AUFSTIEG
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed mb-5">
                Taktische Analyse der Como-Dominanz: Ballbesitz, xG und konstanter Druck auf Venezia. Die Zahlen des Aufstiegstraums.
              </p>
              <Link href="/blog/meritometro" className="inline-flex items-center gap-2 text-[8px] font-black uppercase tracking-[0.2em] border border-[#0066ff] text-[#0066ff] px-4 py-2.5 rounded-sm hover:opacity-75 transition-opacity">
                Weiterlesen →
              </Link>
            </div>
          </div>
          <div className="relative overflow-hidden bg-[#121826] border border-slate-800 rounded-md min-h-[200px]">
            <div className="absolute inset-0" style={{ background: "linear-gradient(225deg, rgba(0,40,120,0.20) 0%, transparent 60%)" }} />
            <div className="relative p-6">
              <p className="text-[7px] font-black uppercase tracking-[0.24em] text-slate-600 mb-2">Barsport.club · Hintergrund</p>
              <h4 className="font-heading text-lg font-black uppercase tracking-tight text-white leading-tight mb-3">
                COMOS TAKTIKANALYSE: WAS FUNKTIONIERT
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed mb-5">
                Die taktischen Schlüssel und entscheidenden Momente des Como-Siegs. Pressing, Ballbesitz und Verwaltung der Führung.
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
