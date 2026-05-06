import useSWR from "swr";
import { fetchPlayerDNA, fetchPlayerRadar, fetchPlayerShots, PlayerDNA, RadarData, Shot } from "../lib/scoutApi";

const SWR_OPTS = { revalidateOnFocus: false, dedupingInterval: 300_000, errorRetryCount: 2 };

async function fetchAll(name: string): Promise<{ dna: PlayerDNA | null; radar: RadarData | null; shots: Shot[] }> {
  const [dnaRes, radarRes, shotsRes] = await Promise.allSettled([
    fetchPlayerDNA(name),
    fetchPlayerRadar(name),
    fetchPlayerShots(name),
  ]);
  return {
    dna:   dnaRes.status   === "fulfilled" ? dnaRes.value   : null,
    radar: radarRes.status === "fulfilled" ? radarRes.value : null,
    shots: shotsRes.status === "fulfilled" ? shotsRes.value : [],
  };
}

export function usePlayerDNA(name: string | null) {
  const { data, isLoading } = useSWR(
    name ? ["scout-dna", name] : null,
    ([, n]) => fetchAll(n as string),
    SWR_OPTS
  );
  return {
    dna:      data?.dna   ?? null,
    radar:    data?.radar ?? null,
    shots:    data?.shots ?? [],
    isLoading,
  };
}
