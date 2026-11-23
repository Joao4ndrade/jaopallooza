import { CircleAlert, CircleCheck, ScanLine } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Navigate, useLocation, useParams } from 'react-router-dom'
import { Button, PageLoader } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { formatTime } from '../lib/format'
import type { Ticket } from '../lib/types'

/**
 * Destino do QR code do ingresso. A organização escaneia com a câmera do
 * celular, cai aqui e confirma a entrada com um toque.
 */
export function CheckinPage() {
  const { code = '' } = useParams()
  const { me, loading } = useAuth()
  const location = useLocation()

  if (loading) return <PageLoader />
  if (!me) return <Navigate to="/entrar" state={{ from: location.pathname }} replace />

  return (
    <div className="flex min-h-[calc(100dvh-var(--bottom-nav))] items-center justify-center bg-surface px-4 py-10 md:min-h-dvh">
      <div className="w-full max-w-sm rounded-3xl bg-white p-6 text-center shadow-sm ring-1 ring-line">
        {me.is_admin ? (
          <AdminCheckin code={code} />
        ) : (
          <>
            <ScanLine className="mx-auto size-12 text-brand-600" />
            <h1 className="mt-4 text-xl font-extrabold">Esse é o ingresso de alguém 🎟️</h1>
            <p className="mt-1 text-muted">Só a organização valida ingressos na entrada.</p>
          </>
        )}
      </div>
    </div>
  )
}

function AdminCheckin({ code }: { code: string }) {
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [justChecked, setJustChecked] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api<Ticket>(`/admin/tickets/${encodeURIComponent(code)}`)
      .then(setTicket)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Erro ao consultar o ingresso.'))
  }, [code])

  async function checkIn() {
    setSaving(true)
    try {
      setTicket(await api<Ticket>(`/admin/tickets/${encodeURIComponent(code)}/check-in`, { method: 'POST' }))
      setJustChecked(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Erro no check-in.')
    } finally {
      setSaving(false)
    }
  }

  if (error) {
    return (
      <>
        <CircleAlert className="mx-auto size-14 text-brand-600" />
        <h1 className="mt-4 text-xl font-extrabold">Opa!</h1>
        <p className="mt-1 text-muted">{error}</p>
        <p className="mt-4 font-mono text-sm text-muted">{code}</p>
      </>
    )
  }
  if (!ticket) return <PageLoader />

  if (justChecked) {
    return (
      <div className="animate-pop">
        <CircleCheck className="mx-auto size-16 text-green-600" />
        <h1 className="mt-4 text-2xl font-extrabold">Entrada liberada!</h1>
        <p className="mt-1 text-lg">Bem-vindo(a), {ticket.holder_name} 🎉</p>
      </div>
    )
  }

  return (
    <>
      <p className="text-sm font-bold tracking-widest text-muted uppercase">Check-in</p>
      <h1 className="mt-2 text-3xl font-extrabold">{ticket.holder_name}</h1>
      <p className="mt-1 font-mono text-muted">{ticket.code}</p>
      {ticket.checked_in_at ? (
        <p className="mt-6 rounded-2xl bg-amber-50 p-4 font-semibold text-amber-800">
          ⚠️ Já entrou em {formatTime(ticket.checked_in_at)}
        </p>
      ) : (
        <Button size="lg" className="mt-6 w-full" onClick={checkIn} loading={saving}>
          Confirmar entrada
        </Button>
      )}
    </>
  )
}
