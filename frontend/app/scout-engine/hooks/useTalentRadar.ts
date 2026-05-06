import useSWR from "swr";
import { fetchTalentRadar, PlayerDNA, TalentCategory, LeagueKey } from "../lib/scoutApi";

const SWR_OPTS = { revalidateOnFocus: false, dedupingInterval: 300_000, errorRetryCount: 2 };

export function useTalentRadar(category: TalentCategory, league: LeagueKey, pos: string) {
  const { data, isLoading } = useSWR<PlayerDNA[]>(
    ["scout-talent", category, league, pos],
    () => fetchTalentRadar(category, league, pos),
    SWR_OPTS
  );
  return { talents: data ?? [], isLoading };
}
