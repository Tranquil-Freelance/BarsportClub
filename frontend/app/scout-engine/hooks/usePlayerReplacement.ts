import useSWR from "swr";
import { fetchReplacement, ReplacementData } from "../lib/scoutApi";

const SWR_OPTS = { revalidateOnFocus: false, dedupingInterval: 300_000, errorRetryCount: 2 };

export function usePlayerReplacement(name: string | null) {
  const { data, isLoading } = useSWR<ReplacementData | null>(
    name ? ["scout-replace", name] : null,
    ([, n]) => fetchReplacement(n as string),
    SWR_OPTS
  );
  return { data: data ?? null, isLoading };
}
