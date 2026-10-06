import { useCallback, useEffect, useState } from 'react'

export function useApi(loader, dependencies = []) {
  const [state, setState] = useState({
    data: null,
    error: null,
    loading: true,
  })

  const load = useCallback(async () => {
    setState((current) => ({ ...current, error: null, loading: true }))
    try {
      const data = await loader()
      setState({ data, error: null, loading: false })
    } catch (error) {
      setState({ data: null, error, loading: false })
    }
  }, dependencies)

  useEffect(() => {
    let active = true
    setState((current) => ({ ...current, error: null, loading: true }))
    loader()
      .then((data) => {
        if (active) setState({ data, error: null, loading: false })
      })
      .catch((error) => {
        if (active) setState({ data: null, error, loading: false })
      })
    return () => {
      active = false
    }
  }, dependencies)

  return { ...state, reload: load }
}
