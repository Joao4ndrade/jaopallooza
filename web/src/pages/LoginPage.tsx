import { CircleCheck, CircleX, Eye, EyeOff, LoaderCircle } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AuthLayout, FormError, inputClass } from '../components/AuthLayout'
import { LOGIN_NOTICE } from '../components/LoginNotice'
import { Button } from '../components/ui'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { useClaimTicket } from '../lib/useClaimTicket'
import { useEvent } from '../lib/useEvent'
import { useNameCheck } from '../lib/useNameCheck'

type Mode = 'login' | 'register'

interface LocationState {
  claim?: boolean
  mode?: Mode
  from?: string
}

export function LoginPage() {
  const { me, login, register } = useAuth()
  const { event } = useEvent()
  const { claim } = useClaimTicket()
  const navigate = useNavigate()
  const state = (useLocation().state ?? {}) as LocationState

  const [mode, setMode] = useState<Mode>(state.mode ?? (state.claim ? 'register' : 'login'))
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [invite, setInvite] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  // Depois de autenticar, quem decide o destino é o handleSubmit. Sem esse flag,
  // o redirect abaixo atropelaria a navegação (o navigate do Router é uma transition).
  const [authenticated, setAuthenticated] = useState(false)

  const isRegister = mode === 'register'
  const nameCheck = useNameCheck(name, isRegister)

  // Chegou aqui já logado: nada a fazer nesta tela.
  if (me && !submitting && !authenticated) return <Navigate to={state.from ?? '/conta'} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (isRegister) await register({ name, email, password, inviteCode: invite })
      else await login(name, password)
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

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
  }

  return (
    <AuthLayout
      title={state.claim ? 'Falta pouco pro seu ingresso! 🎟️' : 'Bora pro JAOPALLOOZA'}
      subtitle={state.claim ? LOGIN_NOTICE : isRegister ? 'Rapidinho: nome, e-mail e senha.' : 'Entre com seu nome ou e-mail.'}
    >
      <div role="tablist" className="mt-6 grid grid-cols-2 rounded-xl bg-surface p-1">
        {(['register', 'login'] as const).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => switchMode(m)}
            className={`h-10 rounded-lg text-sm font-bold transition ${mode === m ? 'bg-white shadow-sm' : 'text-muted'}`}
          >
            {m === 'register' ? 'Criar conta' : 'Já tenho conta'}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-bold">{isRegister ? 'Nome' : 'Nome ou e-mail'}</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="username"
            required
            minLength={2}
            maxLength={isRegister ? 30 : 254}
            placeholder={isRegister ? 'Como a galera te chama' : 'Seu nome ou e-mail'}
            aria-invalid={isRegister && nameCheck.status === 'taken'}
            aria-describedby="name-hint"
            className={inputClass}
          />
          {isRegister && <NameHint check={nameCheck} />}
        </label>

        {isRegister && (
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold">E-mail</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              maxLength={254}
              placeholder="voce@exemplo.com"
              className={inputClass}
            />
            <span className="text-xs text-muted">Só pra recuperar a senha se você esquecer. Nada de spam 🤝</span>
          </label>
        )}

        <label className="flex flex-col gap-1.5">
          <span className="flex items-center justify-between">
            <span className="text-sm font-bold">Senha</span>
            {!isRegister && (
              <Link to="/esqueci-senha" className="text-sm font-semibold text-brand-600 hover:underline">
                Esqueci minha senha
              </Link>
            )}
          </span>
          <span className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              required
              minLength={isRegister ? 6 : undefined}
              placeholder={isRegister ? 'Mínimo de 6 caracteres' : ''}
              className={`${inputClass} pr-12`}
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

        {isRegister && event?.invite_required && (
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold">Código do convite</span>
            <input
              value={invite}
              onChange={(e) => setInvite(e.target.value)}
              required
              placeholder="O código que o João passou pra você"
              className={inputClass}
            />
          </label>
        )}

        {error && <FormError>{error}</FormError>}

        <Button type="submit" size="lg" loading={submitting} disabled={isRegister && nameCheck.status === 'taken'} className="mt-2">
          {state.claim ? 'Garantir meu ingresso' : isRegister ? 'Criar conta' : 'Entrar'}
        </Button>
      </form>
    </AuthLayout>
  )
}

function NameHint({ check }: { check: ReturnType<typeof useNameCheck> }) {
  if (check.status === 'checking') {
    return (
      <span id="name-hint" className="flex items-center gap-1.5 text-xs text-muted">
        <LoaderCircle className="size-3.5 animate-spin" /> Conferindo se o nome está livre…
      </span>
    )
  }
  if (check.status === 'available') {
    return (
      <span id="name-hint" className="flex items-center gap-1.5 text-xs font-semibold text-green-700">
        <CircleCheck className="size-3.5" /> {check.message}
      </span>
    )
  }
  if (check.status === 'taken') {
    return (
      <span id="name-hint" role="alert" className="flex items-center gap-1.5 text-xs font-semibold text-brand-700">
        <CircleX className="size-3.5 shrink-0" /> {check.message}
      </span>
    )
  }
  return (
    <span id="name-hint" className="text-xs text-muted">
      É esse nome que aparece na votação do Awards. Dois Lucas? Use “Lucas B.” 😉
    </span>
  )
}
