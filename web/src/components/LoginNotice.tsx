import { LogIn } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'
import { buttonClass } from './button-class'

export const LOGIN_NOTICE = 'Faça o login ou crie sua conta para garantir seu ingresso.'

interface Props {
  /** "card": caixa destacada no conteúdo. "bar": versão compacta para a barra fixa do celular. */
  variant?: 'card' | 'bar'
  className?: string
}

/**
 * Aviso para quem ainda não entrou: o ingresso é da conta (1 conta = 1 QR code).
 * Some sozinho quando a pessoa está logada. Depois do login, o ingresso já é garantido.
 */
export function LoginNotice({ variant = 'card', className = '' }: Props) {
  const { me, loading } = useAuth()
  if (me || loading) return null

  const buttons = (
    <div className="grid grid-cols-2 gap-2 sm:flex">
      <Link to="/entrar" state={{ claim: true, mode: 'login' }} className={buttonClass('secondary', 'md')}>
        Entrar
      </Link>
      <Link to="/entrar" state={{ claim: true, mode: 'register' }} className={buttonClass('primary', 'md')}>
        Criar conta
      </Link>
    </div>
  )

  if (variant === 'bar') {
    return (
      <div role="note" className={className}>
        <p className="mb-2 flex items-center justify-center gap-2 text-center text-sm font-semibold text-brand-800">
          <LogIn className="size-4 shrink-0 text-brand-600" aria-hidden />
          {LOGIN_NOTICE}
        </p>
        {buttons}
      </div>
    )
  }

  return (
    <div
      role="note"
      className={`flex flex-col gap-3 rounded-2xl bg-brand-50 p-4 ring-1 ring-brand-100 sm:flex-row sm:items-center ${className}`}
    >
      <p className="flex flex-1 items-start gap-3 font-semibold text-brand-800">
        <LogIn className="mt-0.5 size-5 shrink-0 text-brand-600" aria-hidden />
        {LOGIN_NOTICE}
      </p>
      {buttons}
    </div>
  )
}
