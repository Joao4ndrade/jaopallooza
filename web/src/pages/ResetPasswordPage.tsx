import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AuthLayout, FormError, inputClass } from '../components/AuthLayout'
import { useToast } from '../components/toast-context'
import { Button } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'

/** Destino do link enviado por e-mail: /redefinir-senha?token=... */
export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [linkExpired, setLinkExpired] = useState(false)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (password !== confirm) {
      setError('As senhas não batem. Digita de novo?')
      return
    }
    setError(null)
    setSaving(true)
    try {
      const { access_token } = await api<{ access_token: string }>('/auth/reset-password', {
        method: 'POST',
        body: { token, password },
      })
      await loginWithToken(access_token)
      toast('Senha nova salva! Você já está logado 🔑')
      navigate('/conta', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não deu pra salvar agora. Tenta de novo?')
      setLinkExpired(err instanceof ApiError && err.status === 400)
    } finally {
      setSaving(false)
    }
  }

  if (!token) {
    return (
      <AuthLayout title="Link incompleto 🤔" subtitle="Abre o link direto do e-mail, sem cortar nenhum pedaço.">
        <Link to="/esqueci-senha" className="mt-6 block font-semibold text-brand-600 hover:underline">
          Pedir um link novo
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Crie uma senha nova" subtitle="Dessa vez anota num lugar seguro, hein 😉">
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-bold">Nova senha</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={6}
            placeholder="Mínimo de 6 caracteres"
            className={inputClass}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-bold">Repita a senha</span>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            required
            minLength={6}
            className={inputClass}
          />
        </label>
        {error && (
          <FormError>
            {error}{' '}
            {linkExpired && (
              <Link to="/esqueci-senha" className="underline">
                Pedir link novo
              </Link>
            )}
          </FormError>
        )}
        <Button type="submit" size="lg" loading={saving}>
          Salvar nova senha
        </Button>
      </form>
    </AuthLayout>
  )
}
