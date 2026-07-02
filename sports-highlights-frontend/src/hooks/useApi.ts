import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface UseApiOptions extends RequestInit {
  immediate?: boolean;
}

export function useApi<T>(endpoint: string, options: UseApiOptions = {}) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(!!options.immediate);

  const { immediate, ...fetchOptions } = options;

  const execute = useCallback(
    async (body?: any) => {
      setLoading(true);
      setError(null);
      try {
        const currentOptions: RequestInit = { ...fetchOptions };
        if (body) {
          currentOptions.body = JSON.stringify(body);
        }
        const result = await apiFetch<T>(endpoint, currentOptions);
        setData(result);
        return result;
      } catch (err: any) {
        const msg = err.message || "Erro de rede";
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [endpoint, JSON.stringify(fetchOptions)]
  );

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {});
    }
  }, [immediate, execute]);

  return { data, error, loading, execute, setData };
}
