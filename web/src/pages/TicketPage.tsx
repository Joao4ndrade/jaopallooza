import { CircleCheck } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { ClaimTicketButton } from '../components/ClaimTicketButton'
import { Confetti } from '../components/Confetti'
import { Poster } from '../components/Poster'
import { PageHeader, PageLoader } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { EM_BREVE, eventWhen, formatTime } from '../lib/format'
import type { EventInfo, Ticket } from '../lib/types'
import { useEvent } from '../lib/useEvent'

export function TicketPage() {
  const { me, loading } = useAuth()
  const { event } = useEvent()
  const justClaimed = Boolean((useLocation().state as { justClaimed?: boolean } | null)?.justClaimed)
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [error, setError] = useState<string | null>(null)

  const hasTicket = Boolean(me?.has_ticket)

  useEffect(() => {
    if (!hasTicket) return
    api<Ticket>('/tickets/me')
      .then(setTicket)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Erro ao carregar o ingresso.'))
  }, [hasTicket])

  if (loading) return <PageLoader />

  return (
    <div className="min-h-[calc(100dvh-var(--bottom-nav))] bg-surface md:min-h-dvh">
      <PageHeader title="Carteira de ingressos" subtitle={hasTicket ? 'Vem aí 🎉' : undefined} />

      <div className="px-4 pb-10 md:px-10">
        {!hasTicket ? (
          <NoTicket event={event} />
        ) : ticket && event ? (
          <>
            {justClaimed && <Confetti />}
            <TicketCard ticket={ticket} event={event} highlight={justClaimed} />
          </>
        ) : error ? (
          <p className="text-muted">{error}</p>
        ) : (
          <PageLoader />
        )}
      </div>
    </div>
  )
}

function NoTicket({ event }: { event: EventInfo | null }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center rounded-3xl bg-white px-6 py-10 text-center ring-1 ring-line">
      <Poster className="w-32 rotate-[-4deg] rounded-xl shadow-lg" />
      <h2 className="mt-6 text-xl font-extrabold">Sua carteira tá vazia</h2>
      <p className="mt-1 text-muted">
        Garanta seu ingresso pro {event?.name ?? 'JAOPALLOOZA'} e ele aparece aqui com o QR code da entrada.
      </p>
      <ClaimTicketButton className="mt-6 w-full" />
    </div>
  )
}

function TicketCard({ ticket, event, highlight }: { ticket: Ticket; event: EventInfo; highlight: boolean }) {
  const when = eventWhen(event)
  const checkinUrl = `${window.location.origin}/checkin/${ticket.code}`

  return (
    <div className="mx-auto max-w-sm">
      {highlight && (
        <p className="animate-pop mb-4 rounded-2xl bg-ink px-4 py-3 text-center font-bold text-white">
          Ingresso garantido! Nos vemos no JAOPALLOOZA 🎉
        </p>
      )}

      <article className="animate-pop overflow-hidden rounded-3xl bg-white shadow-xl shadow-black/5 ring-1 ring-line">
        <header className="flex gap-4 bg-brand-600 p-5 text-white">
          <Poster className="w-16 shrink-0 rounded-lg shadow-md" />
          <div className="min-w-0">
            <p className="text-xs font-bold tracking-[0.2em] text-white/75 uppercase">Pista • Convidado(a)</p>
            <h2 className="font-display text-2xl leading-tight tracking-wide">{event.name}</h2>
            <p className="text-sm text-white/85 first-letter:uppercase">{when ? `${when.date} • ${when.time}` : `Data: ${EM_BREVE.toLowerCase()}`}</p>
          </div>
        </header>

        {/* picote do ingresso */}
        <div className="relative h-6" aria-hidden>
          <span className="absolute top-1/2 -left-3 size-6 -translate-y-1/2 rounded-full bg-surface" />
          <span className="absolute top-1/2 -right-3 size-6 -translate-y-1/2 rounded-full bg-surface" />
          <span className="absolute inset-x-5 top-1/2 border-t-2 border-dashed border-line" />
        </div>

        <div className="flex flex-col items-center px-6 pb-2">
          <div className={`rounded-2xl p-3 ring-1 ring-line ${ticket.checked_in_at ? 'opacity-40' : ''}`}>
            <QRCodeSVG value={checkinUrl} size={208} level="M" marginSize={0} fgColor="#121212" title={`QR code do ingresso ${ticket.code}`} />
          </div>
          <p className="mt-3 font-mono text-lg font-bold tracking-[0.2em]">{ticket.code}</p>
          {ticket.checked_in_at ? (
            <p className="mt-2 flex items-center gap-1.5 text-sm font-bold text-green-700">
              <CircleCheck className="size-4" /> Check-in feito em {formatTime(ticket.checked_in_at)}
            </p>
          ) : (
            <p className="mt-1 text-center text-sm text-muted">Apresente este QR code na entrada</p>
          )}
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-line p-5 text-sm">
          <div>
            <dt className="text-muted">Titular</dt>
            <dd className="font-bold">{ticket.holder_name}</dd>
          </div>
          <div>
            <dt className="text-muted">Local</dt>
            <dd className="font-bold">{event.venue_name ?? EM_BREVE}</dd>
          </div>
          <div>
            <dt className="text-muted">Horário</dt>
            <dd className="font-bold">{when?.time ?? EM_BREVE}</dd>
          </div>
          <div>
            <dt className="text-muted">Status</dt>
            <dd className="font-bold">{ticket.checked_in_at ? 'Utilizado' : 'Válido ✅'}</dd>
          </div>
        </dl>
      </article>

      <p className="mt-4 text-center text-xs text-muted">Dica: tira um print pra não depender da internet na porta 😉</p>
    </div>
  )
}
