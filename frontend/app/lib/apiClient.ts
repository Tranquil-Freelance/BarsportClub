/**
 * Core API client for xPalermoStat frontend.
 * Uses native Next.js fetch API with automatic error handling.
 */

/** Base origin for backend (no path). Use for /api/... routes outside /api/v1. */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const BASE_URL = `${API_BASE}/api/v1`;

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestOptions {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: unknown; // Will be JSON.stringify'd
  cache?: RequestCache;
  next?: {
    revalidate?: number;
    tags?: string[];
  };
}

/**
 * Generic fetcher that throws an error if response is not ok.
 * Automatically sets Content-Type to application/json for non‑GET requests.
 */
export async function fetcher<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', headers = {}, body, cache, next } = options;

  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

  const config: RequestInit = {
    method,
    headers: {
      ...headers,
    },
    cache,
    next,
  };

  // Add JSON body for POST, PUT, PATCH
  if (body !== undefined && ['POST', 'PUT', 'PATCH'].includes(method)) {
    config.headers = {
      ...config.headers,
      'Content-Type': 'application/json',
    };
    config.body = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  const response = await fetch(url, { ...config, signal: controller.signal }).finally(() => clearTimeout(timeoutId));

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`API error ${response.status}: ${errorText}`);
  }

  // Handle empty responses (e.g., 204 No Content)
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const text = await response.text();
    if (!text) return undefined as unknown as T;
    try {
      return JSON.parse(text) as T;
    } catch (e) {
      throw new Error(`Failed to parse JSON: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }

  // Fallback for non‑JSON responses (should not happen in our API)
  return undefined as unknown as T;
}

/**
 * Convenience GET wrapper.
 */
export function get<T = unknown>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>) {
  return fetcher<T>(endpoint, { ...options, method: 'GET' });
}

/**
 * Convenience POST wrapper.
 */
export function post<T = unknown>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) {
  return fetcher<T>(endpoint, { ...options, method: 'POST', body });
}