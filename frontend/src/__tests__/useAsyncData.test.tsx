import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useAsyncData } from '../hooks/useAsyncData'

describe('useAsyncData', () => {
  it('loads data successfully with loading transition', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: { count: 42 } })

    const { result } = renderHook(() => useAsyncData(fetcher, []))

    // 初始 loading
    expect(result.current.loading).toBe(true)
    expect(result.current.data).toBeNull()

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.data).toEqual({ count: 42 })
    expect(result.current.error).toBeNull()
    expect(fetcher).toHaveBeenCalledTimes(1)
  })

  it('records error when fetch fails', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('network down'))

    const { result } = renderHook(() => useAsyncData(fetcher, []))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.data).toBeNull()
    expect(result.current.error?.message).toBe('network down')
  })

  it('reload re-fetches and updates data', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ data: { v: 1 } })
      .mockResolvedValueOnce({ data: { v: 2 } })

    const { result } = renderHook(() => useAsyncData(fetcher, []))

    await waitFor(() => {
      expect(result.current.data).toEqual({ v: 1 })
    })

    await act(async () => {
      await result.current.reload()
    })

    expect(result.current.data).toEqual({ v: 2 })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('discards stale responses (race protection)', async () => {
    let resolveFirst: (value: unknown) => void
    const firstPromise = new Promise((resolve) => {
      resolveFirst = resolve
    })
    const fetcher = vi
      .fn()
      .mockReturnValueOnce(firstPromise)
      .mockResolvedValueOnce({ data: { v: 2 } })

    const { result } = renderHook(() => useAsyncData(fetcher, []))

    // 挂载触发的 reload（序号1）挂起；手动 reload（序号2）立即完成
    await act(async () => {
      result.current.reload()
      await Promise.resolve()
    })

    expect(result.current.data).toEqual({ v: 2 })
    expect(result.current.loading).toBe(false)

    // 序号1（过期）返回：不应覆盖
    await act(async () => {
      resolveFirst({ data: { v: 1 } })
    })
    expect(result.current.data).toEqual({ v: 2 })
  })

  it('reloads automatically when deps change', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 1 })

    const { result, rerender } = renderHook(
      ({ id }) => useAsyncData(() => fetcher(id), [id]),
      { initialProps: { id: 'a' } }
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher).toHaveBeenCalledWith('a')

    rerender({ id: 'b' })

    await waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(2)
    })
    expect(fetcher).toHaveBeenCalledWith('b')
  })
})
