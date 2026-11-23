import { MailCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { AuthLayout, FormError, inputClass } from '../components/AuthLayout'
import { buttonClass } from '../components/button-class'
import { Button } from '../components/ui'
import { api, ApiError } from '../lib/api'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSending(true)
    try {
      const { detail } = await api<{ detail: string }>('/auth/forgot-password', { method: 'POST', body: { email } })
      setSent(detail)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não deu pra enviar agora. Tenta de novo?')
    } finally {
      setSending(false)
    }
  }

  if (sent) {
    return (
      <AuthLayout title="Confere seu e-mail 📬">
        <div className="mt-6 flex gap-3 rounded-2xl bg-surface p-4">
          <MailCheck className="size-6 shrink-0 text-brand-600" aria-hidden />
          <p className="text-sm">{sent}</p>
        </div>
        <p className="mt-4 text-sm text-muted">O link vale por 1 hora e só funciona uma vez. Não chegou? Espera um minutinho e pede de novo.</p>
        <Link to="/entrar" className={buttonClass('secondary', 'lg', 'mt-6 w-full')}>
          Voltar pro login
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Esqueceu a senha? Acontece 😅" subtitle="Digita o e-mail da sua conta que a gente manda um link pra criar uma nova.">
      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-bold">E-mail</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            placeholder="voce@exemplo.com"
            className={inputClass}
          />
        </label>
        {error && <FormError>{error}</FormError>}
        <Button type="submit" size="lg" loading={sending}>
          Enviar link
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-muted">
        Lembrou?{' '}
        <Link to="/entrar" className="font-semibold text-brand-600 hover:underline">
          Entrar
        </Link>
      </p>
    </AuthLayout>
  )
}
