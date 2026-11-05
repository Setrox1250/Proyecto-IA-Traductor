import { useCallback, useEffect, useRef, useState } from 'react';

import { fetchStatus } from '../api/client';

export default function useEngineStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const abortRef = useRef(null);

  const refresh = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    try {
      const payload = await fetchStatus({ signal: controller.signal });
      if (!controller.signal.aborted) {
        setStatus(payload);
        setError(null);
      }
    } catch (requestError) {
      if (requestError?.name !== 'AbortError') {
        setError(requestError);
        setStatus(null);
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 30000);
    return () => {
      clearInterval(timer);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [refresh]);

  return { status, error, loading, refresh };
}
