import { CalendarDays, ChevronRight, Map, MapPin, Share2, Trophy, Users, type LucideIcon } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Avatar } from '../components/Avatar'
import { ClaimTicketButton } from '../components/ClaimTicketButton'
import { LoginNotice } from '../components/LoginNotice'
import { Poster } from '../components/Poster'
import { useToast } from '../components/toast-context'
import { PageLoader } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { EM_BREVE, eventWhen, plural } from '../lib/format'
import type { EventInfo, Person } from '../lib/types'
import { useEvent } from '../lib/useEvent'

export function EventPage() {
  const { event, error } = useEvent()
  const { me, loading } = useAuth()
  const visitor = !me && !loading

  if (!event) {
    return error ? <p className="p-10 text-center text-muted">{error}</p> : <PageLoader />
  }

  return (
    <div className={visitor ? 'pb-36 md:pb-0' : 'pb-24 md:pb-0'}>
      <Hero event={event} />

      <div className="relative -mt-5 rounded-t-3xl bg-white md:mt-0 md:rounded-none">
        <div className="mx-auto grid max-w-5xl gap-10 px-4 pt-6 pb-10 md:grid-cols-[1fr_320px] md:px-10 md:pt-10">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight md:hidden">{event.name}</h1>
            {/* No celular o aviso fica na barra fixa lá embaixo, sempre visível */}
            <div className="hidden md:block">
              <LoginNotice className="mb-8" />
            </div>
            <EventFacts event={event} />

            <hr className="my-6 border-line" />

            <h2 className="text-2xl font-extrabold">Sobre o evento</h2>
            <p className="mt-3 leading-relaxed whitespace-pre-line text-ink/80">{event.description ?? EM_BREVE}</p>

            <Link
              to="/awards"
              className="mt-8 flex items-center gap-4 rounded-2xl bg-ink p-5 text-white transition hover:bg-ink/90"
            >
              <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-brand-600">
                <Trophy className="size-6" aria-hidden />
              </span>
              <span className="flex-1">
                <span className="block font-display text-xl tracking-wide">JAOPALLOOZA AWARDS</span>
                <span className="block text-sm text-white/70">
                  Mais atrasado, mais engraçado, melhor casal… a votação já começou.
                </span>
              </span>
              <ChevronRight className="size-5 text-white/60" aria-hidden />
            </Link>

            <Attendees count={event.tickets_count} />
          </div>

          <aside className="hidden md:block">
            <div className="sticky top-8 rounded-3xl p-6 ring-1 ring-line">
              <p className="text-sm font-semibold text-muted">Ingresso</p>
              <p className="mt-1 text-2xl font-extrabold">Pista • Convidado(a)</p>
              <p className="mt-1 text-sm text-muted">Entrada garantida com QR code. Sem taxa, só alegria.</p>
              <ClaimTicketButton className="mt-6 w-full" />
              <TicketsCount count={event.tickets_count} className="mt-4 justify-center" />
            </div>
          </aside>
        </div>
      </div>

      {/* CTA fixo no mobile, logo acima da barra de navegação. Sem conta, vira o aviso de login. */}
      <div className="fixed inset-x-0 bottom-(--bottom-nav) z-10 border-t border-line bg-white/95 px-4 py-3 backdrop-blur md:hidden">
        {visitor ? <LoginNotice variant="bar" /> : <ClaimTicketButton className="w-full" />}
      </div>
    </div>
  )
}

function Hero({ event }: { event: EventInfo }) {
  const toast = useToast()

  async function share() {
    const data = { title: event.name, text: event.tagline ?? event.name, url: window.location.origin }
    try {
      if (navigator.share) {
        await navigator.share(data)
      } else {
        await navigator.clipboard.writeText(data.url)
        toast('Link copiado! Manda no grupo 😉')
      }
    } catch {
      /* a pessoa fechou o menu de compartilhar */
    }
  }

  return (
    <section className="relative overflow-hidden bg-brand-900">
      {/* fundo desfocado feito com o próprio cartaz, igual app de ingresso */}
      <div aria-hidden className="absolute inset-0 scale-150 opacity-70 blur-3xl">
        <Poster className="size-full" />
      </div>
      <div aria-hidden className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/10 to-black/50" />

      <div className="relative mx-auto max-w-5xl px-4 pt-4 pb-12 md:flex md:items-end md:gap-10 md:px-10 md:py-14">
        <div className="flex justify-end md:absolute md:top-6 md:right-10">
          <button
            onClick={share}
            className="grid size-12 place-items-center rounded-2xl bg-black/30 text-white backdrop-blur transition hover:bg-black/45"
            aria-label="Compartilhar evento"
          >
            <Share2 className="size-5" />
          </button>
        </div>

        <Poster className="mx-auto mt-2 w-60 rounded-2xl shadow-2xl shadow-black/40 sm:w-72 md:mx-0 md:mt-0 md:w-80" />

        <div className="hidden pb-2 text-white md:block">
          <p className="text-sm font-bold tracking-[0.3em] text-white/70 uppercase">Aniversário do João</p>
          <h1 className="mt-2 font-display text-6xl leading-none tracking-wide lg:text-7xl">{event.name}</h1>
          {event.tagline && <p className="mt-4 max-w-md text-lg text-white/85">{event.tagline}</p>}
          <TicketsCount count={event.tickets_count} className="mt-6 text-white/85" />
        </div>
      </div>
    </section>
  )
}

function EventFacts({ event }: { event: EventInfo }) {
  const when = eventWhen(event)
  const place = [event.venue_address, event.city].filter(Boolean).join(' • ')

  return (
    <div className="mt-5 flex flex-col gap-5 md:mt-0">
      <Fact
        icon={CalendarDays}
        title={when ? `${when.date} • ${when.time}` : EM_BREVE}
        subtitle={when ? when.weekday : 'Data e horário ainda não definidos'}
      />
      <Fact
        icon={MapPin}
        title={event.venue_name ?? EM_BREVE}
        subtitle={place || 'Local ainda em segredo 🤫'}
        action={
          event.maps_url ? (
            <a
              href={event.maps_url}
              target="_blank"
              rel="noreferrer"
              aria-label="Abrir no mapa"
              className="grid size-14 place-items-center rounded-2xl ring-1 ring-line transition hover:bg-surface"
            >
              <Map className="size-6" />
            </a>
          ) : null
        }
      />
    </div>
  )
}

function Fact({ icon: Icon, title, subtitle, action }: { icon: LucideIcon; title: string; subtitle: string; action?: ReactNode }) {
  return (
    <div className="flex items-center gap-4">
      <span className="grid size-14 shrink-0 place-items-center rounded-full bg-surface">
        <Icon className="size-6 text-ink/70" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-lg leading-tight font-bold first-letter:uppercase">{title}</p>
        <p className="text-muted first-letter:uppercase">{subtitle}</p>
      </div>
      {action}
    </div>
  )
}

function TicketsCount({ count, className = '' }: { count: number; className?: string }) {
  if (count === 0) {
    return <p className={`flex items-center gap-2 text-sm font-semibold ${className}`}>Seja a primeira pessoa a garantir! 🚀</p>
  }
  return (
    <p className={`flex items-center gap-2 text-sm font-semibold ${className}`}>
      <Users className="size-4" aria-hidden />
      {plural(count, 'pessoa já garantiu', 'pessoas já garantiram')} ingresso
    </p>
  )
}

/** Lista de presenças confirmadas. Só quem tem conta vê nomes e fotos (o site é público). */
function Attendees({ count }: { count: number }) {
  const { me, loading } = useAuth()
  const [people, setPeople] = useState<Person[] | null>(null)
  const loggedIn = me !== null

  useEffect(() => {
    if (!loggedIn) return
    api<Person[]>('/event/attendees')
      .then(setPeople)
      .catch(() => setPeople([]))
  }, [loggedIn])

  return (
    <section className="mt-10" aria-labelledby="attendees-title">
      <div className="flex items-baseline justify-between gap-4">
        <h2 id="attendees-title" className="text-2xl font-extrabold">
          Quem vai 🎉
        </h2>
        {count > 0 && <span className="text-sm font-semibold text-muted">{plural(count, 'confirmado', 'confirmados')}</span>}
      </div>

      {loading ? null : !loggedIn ? (
        <div className="mt-4 flex items-center gap-4 rounded-2xl bg-surface p-4">
          <div className="flex -space-x-3" aria-hidden>
            {[0, 1, 2, 3].map((i) => (
              <span key={i} className="size-10 rounded-full bg-line ring-2 ring-surface" />
            ))}
          </div>
          <p className="text-sm text-muted">
            {count > 0 ? `${plural(count, 'pessoa já confirmou', 'pessoas já confirmaram')}. ` : ''}
            <Link to="/entrar" className="font-semibold text-brand-600 hover:underline">
              Entre na sua conta
            </Link>{' '}
            pra ver quem vai.
          </p>
        </div>
      ) : people === null ? (
        <p className="mt-4 text-sm text-muted">Carregando a lista…</p>
      ) : people.length === 0 ? (
        <p className="mt-4 rounded-2xl bg-surface p-4 text-sm text-muted">Ninguém confirmou ainda. Seja a primeira pessoa! 🚀</p>
      ) : (
        <ul className="mt-5 grid grid-cols-3 gap-x-3 gap-y-5 sm:grid-cols-4 lg:grid-cols-5">
          {people.map((person) => (
            <li key={person.id} className="flex min-w-0 flex-col items-center text-center">
              <Avatar name={person.name} photoUrl={person.photo_url} size="lg" />
              <span className="mt-2 w-full truncate text-sm font-semibold">{person.id === me?.id ? 'Você' : person.name}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
