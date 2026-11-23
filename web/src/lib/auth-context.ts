import { createContext, useContext } from 'react'
import type { Me } from './types'

export interface AuthContextValue {
  me: Me | null
  /** true só no carregamento inicial, enquanto descobrimos se há sessão salva */
  loading: boolean
  /** `login` aceita nome ou e-mail */
  login: (login: string, password: string) => Promise<void>
  register: (data: { name: string; email: string; password: string; inviteCode?: string }) => Promise<void>
  /** Usado depois de redefinir a senha: a API já devolve uma sessão nova. */
  loginWithToken: (token: string) => Promise<void>
  logout: () => void
  refresh: () => Promise<Me | null>
  setMe: (me: Me) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return ctx
}
