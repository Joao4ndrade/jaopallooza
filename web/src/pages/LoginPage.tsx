import { Eye, EyeOff } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useClaimTicket } from '../lib/useClaimTicket'
import { Logo } from '../components/Logo'
import { Button } from '../components/ui'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { storedInvite } from '../lib/invite'
import { useEvent } from '../lib/useEvent'

type Mode = 'login' | 'register'

interface LocationState {
  claim?: boolean
  from?: string
}

export function LoginPage() {
  const { me, login, register } = useAuth()
  const { event } = useEvent()
  const { claim } = useClaimTicket()
  const navigate = useNavigate()
  const state = (useLocation().state ?? {}) as LocationState

  const [mode, setMode] = useState<Mode>(state.claim ? 'register' : 'login')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [invite, setInvite] = useState(storedInvite)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  // Depois de autenticar, quem decide o destino é o handleSubmit. Sem esse flag,
  // o redirect abaixo atropelaria a navegação (o navigate do Router é uma transition).
  const [authenticated, setAuthenticated] = useState(false)

  // Chegou aqui já logado: nada a fazer nesta tela.
  if (me && !submitting && !authenticated) return <Navigate to={state.from ?? '/conta'} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (mode === 'login') await login(name, password)
      else await register(name, password, invite)
      setAuthenticated(true)

      if (state.claim) {
        // Se garantir falhar (o toast já avisou), leva pra carteira, que tem o botão de novo.
        if (!(await claim())) navigate('/ingresso', { replace: true })
      } else {
        navigate(state.from ?? '/', { replace: true })
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Algo deu errado. Tenta de novo?')
    } finally {
      setSubmitting(false)
    }
  }

  const isRegister = mode === 'register'
  const showInvite = isRegister && event?.invite_required

  return (
    <div className="flex min-h-[calc(100dvh-var(--bottom-nav))] items-center justify-center bg-surface px-4 py-10 md:min-h-dvh">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center md:hidden">
          <Logo />
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-line sm:p-8">
          <h1 className="text-2xl font-extrabold">{state.claim ? 'Falta pouco pro seu ingresso! 🎟️' : 'Bora pro JAOPALLOOZA'}</h1>
          <p className="mt-1 text-muted">Sem e-mail, sem burocracia: só seu nome e uma senha.</p>

          <div role="tablist" className="mt-6 grid grid-cols-2 rounded-xl bg-surface p-1">
            {(['register', 'login'] as const).map((m) => (
              <button
                key={m}
                role="tab"
                aria-selected={mode === m}
                onClick={() => {
                  setMode(m)
                  setError(null)
                }}
                className={`h-10 rounded-lg text-sm font-bold transition ${mode === m ? 'bg-white shadow-sm' : 'text-muted'}`}
              >
                {m === 'register' ? 'Criar conta' : 'Já tenho conta'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-bold">Nome</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="username"
                required
                minLength={2}
                maxLength={30}
                placeholder="Como a galera te chama"
                className="h-12 rounded-xl px-4 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
              />
              {isRegister && (
                <span className="text-xs text-muted">É esse nome que aparece na votação do Awards. Dois Lucas? Use “Lucas B.” 😉</span>
              )}
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-bold">Senha</span>
              <span className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  required
                  minLength={isRegister ? 6 : undefined}
                  placeholder={isRegister ? 'Mínimo de 6 caracteres' : ''}
                  className="h-12 w-full rounded-xl pr-12 pl-4 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 grid w-12 place-items-center text-muted"
                  aria-label={showPassword ? 'Esconder senha' : 'Mostrar senha'}
                >
                  {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </span>
            </label>

            {showInvite && (
              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-bold">Código do convite</span>
                <input
                  value={invite}
                  onChange={(e) => setInvite(e.target.value)}
                  required
                  placeholder="Tá no convite que o João mandou"
                  className="h-12 rounded-xl px-4 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
                />
              </label>
            )}

            {error && (
              <p role="alert" className="rounded-xl bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-700">
                {error}
              </p>
            )}

            <Button type="submit" size="lg" loading={submitting} className="mt-2">
              {state.claim ? 'Garantir meu ingresso' : isRegister ? 'Criar conta' : 'Entrar'}
            </Button>
          </form>

          {!isRegister && (
            <p className="mt-4 text-center text-xs text-muted">Esqueceu a senha? Chama o João que ele reseta pra você.</p>
          )}
        </div>
      </div>
    </div>
  )
}
