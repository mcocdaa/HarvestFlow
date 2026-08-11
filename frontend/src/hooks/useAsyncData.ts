import { useCallback, useEffect, useRef, useState } from 'react';

export interface UseAsyncDataResult<T> {
  /** 加载成功后的数据，初始为 null */
  data: T | null;
  /** 是否加载中（首次加载与每次 reload 期间为 true） */
  loading: boolean;
  /** 最近一次加载错误（拦截器已统一提示，此处仅记录） */
  error: Error | null;
  /** 手动重新加载（返回 Promise 可 await） */
  reload: () => Promise<void>;
}

/**
 * 通用数据加载 hook：管理 loading/data/error 状态，依赖变化自动重载。
 *
 * fetcher 可为内联箭头函数（内部通过 ref 持有最新引用，不会引发循环重载）；
 * deps 变化时自动 reload。
 *
 * @param fetcher 返回 axios 响应形状（含 data 字段）
 * @param deps 依赖数组，变化时自动 reload
 */
export const useAsyncData = <T>(
  fetcher: () => Promise<{ data: T }>,
  deps: React.DependencyList = []
): UseAsyncDataResult<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  // fetcher 引用随渲染更新（latest-ref 模式），reload 保持稳定（避免 effect 循环）
  const fetcherRef = useRef(fetcher);
  useEffect(() => {
    fetcherRef.current = fetcher;
  });
  // 竞态保护：请求序号，过期响应丢弃
  const seqRef = useRef(0);

  const reload = useCallback(async () => {
    const seq = ++seqRef.current;
    setLoading(true);
    try {
      const fetchFn = fetcherRef.current;
      const res = await fetchFn();
      if (seq === seqRef.current) {
        setData(res.data);
        setError(null);
      }
    } catch (err) {
      if (seq === seqRef.current) {
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (seq === seqRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    reload();
    return () => {
      // 卸载时使进行中的请求失效
      seqRef.current += 1;
    };
    // reload 稳定（空依赖），仅 deps 变化触发重载
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, ...deps]);

  return { data, loading, error, reload };
};
