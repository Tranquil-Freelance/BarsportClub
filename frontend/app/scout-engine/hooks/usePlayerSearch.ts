import useSWR from "swr";
import { fetchSearch, Suggestion } from "../lib/scoutApi";

const SWR_OPTS = { revalidateOnFocus: false, dedupingInterval: 60_000, errorRetryCount: 1 };

export function usePlayerSearch(query: string) {
  const key = query.trim().length >= 2 ? ["scout-search", query.trim()] : null;
  const { data, isLoading } = useSWR<Suggestion[]>(
    key,
    ([, q]) => fetchSearch(q as string),
    SWR_OPTS
  );
  return { suggestions: data ?? [], isLoading };
}
