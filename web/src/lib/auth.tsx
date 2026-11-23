import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, setUnauthorizedHandler, tokenStore } from './api'
import { AuthContext, type AuthContextValue } from './auth-context'
import type { Me } from './types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null)
  const [loading, setLoading] = useState(() => tokenStore.get() !== null)

  const logout = useCallback(() => {
    tokenStore.clear()
    setMe(null)
  }, [])

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setMe(null)
      return null
    }
    try {
      const fresh = await api<Me>('/me')
      setMe(fresh)
      return fresh
    } catch {
      return null
    }
  }, [])

  // Restaura a sessão salva ao abrir o site.
  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!tokenStore.get()) return
    api<Me>('/me')
      .then(setMe)
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [logout])

  const loginWithToken = useCallback(
    async (token: string) => {
      tokenStore.set(token)
      await refresh()
    },
    [refresh],
  )

  const authenticate = useCallback(
    async (path: string, body: object) => {
      const { access_token } = await api<{ access_token: string }>(path, { method: 'POST', body })
      await loginWithToken(access_token)
    },
    [loginWithToken],
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      me,
      loading,
      login: (login, password) => authenticate('/auth/login', { login, password }),
      register: ({ name, email, password, inviteCode }) =>
        authenticate('/auth/register', { name, email, password, invite_code: inviteCode || null }),
      loginWithToken,
      logout,
      refresh,
      setMe,
    }),
    [me, loading, authenticate, loginWithToken, logout, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
