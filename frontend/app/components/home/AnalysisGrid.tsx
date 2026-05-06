"use client";

import TacticalCard from "./TacticalCard";
import StatsCard from "./StatsCard";

export default function AnalysisGrid() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TacticalCard />
        <StatsCard />
      </div>
    </div>
  );
}