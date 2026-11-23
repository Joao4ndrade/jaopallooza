import { Check, ChevronLeft, ChevronRight, Search, Trophy } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Avatar } from '../components/Avatar'
import { ClaimTicketButton } from '../components/ClaimTicketButton'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { useToast } from '../components/toast-context'
import { buttonClass } from '../components/button-class'
import { Button, PageLoader } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import type { AwardCategory, AwardsData, Nominee } from '../lib/types'

const SWIPE_THRESHOLD = 50

export function AwardsPage() {
  const { me, loading } = useAuth()

  if (loading) return <PageLoader />
  if (!me) return <AwardsTeaser />
  return <AwardsVoting />
}

function AwardsHeader({ children }: { children?: ReactNode }) {
  return (
    <header className="bg-ink px-4 pt-6 pb-5 text-white md:px-10 md:pt-12 md:pb-8">
      <p className="flex items-center gap-2 text-xs font-bold tracking-[0.25em] text-brand-200 uppercase md:text-sm">
        <Trophy className="size-4" aria-hidden /> Premiação oficial
      </p>
      <h1 className="mt-1 font-display text-3xl tracking-wide md:mt-2 md:text-5xl">JAOPALLOOZA AWARDS</h1>
      <p className="mt-1 max-w-xl text-sm text-white/70 md:mt-2 md:text-base">
        Um voto por categoria, sem direito a arrependimento. Os vencedores serão revelados na festa 🏆
      </p>
      {children}
    </header>
  )
}

function AwardsTeaser() {
  return (
    <div>
      <AwardsHeader />
      <div className="mx-auto max-w-md px-4 py-10 text-center">
        <p className="text-5xl">🗳️</p>
        <h2 className="mt-4 text-xl font-extrabold">A votação é só pra quem vai</h2>
        <p className="mt-1 text-muted">Garanta seu ingresso pra votar em quem é o mais atrasado, o mais engraçado e o melhor casal.</p>
        <ClaimTicketButton className="mt-6 w-full" />
      </div>
    </div>
  )
}

function AwardsVoting() {
  const toast = useToast()
  const [data, setData] = useState<AwardsData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState<Record<number, Nominee | undefined>>({})
  const [confirming, setConfirming] = useState<AwardCategory | null>(null)
  const [voting, setVoting] = useState(false)

  useEffect(() => {
    api<AwardsData>('/awards')
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Erro ao carregar o Awards.'))
  }, [])

  const total = data?.categories.length ?? 0
  const go = useCallback((delta: number) => setIndex((i) => Math.min(Math.max(i + delta, 0), Math.max(total - 1, 0))), [total])

  // Setas do teclado no PC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (confirming || (e.target as HTMLElement).tagName === 'INPUT') return
      if (e.key === 'ArrowRight') go(1)
      if (e.key === 'ArrowLeft') go(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, confirming])

  // Swipe no celular
  const start = useRef<{ x: number; y: number } | null>(null)
  function onPointerDown(e: PointerEvent) {
    if (e.pointerType !== 'mouse') start.current = { x: e.clientX, y: e.clientY }
  }
  function onPointerUp(e: PointerEvent) {
    if (!start.current) return
    const dx = e.clientX - start.current.x
    const dy = e.clientY - start.current.y
    start.current = null
    if (Math.abs(dx) > SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy) * 1.5) go(dx < 0 ? 1 : -1)
  }

  async function confirmVote() {
    if (!confirming) return
    const nominee = selected[confirming.id]
    if (!nominee) return
    setVoting(true)
    try {
      const updated = await api<AwardCategory>(`/awards/${confirming.id}/vote`, {
        method: 'POST',
        body: { nominee_id: nominee.id },
      })
      setData((d) => d && { ...d, categories: d.categories.map((c) => (c.id === updated.id ? updated : c)) })
      toast(`Voto computado: ${nominee.name} 🗳️`)
      setConfirming(null)
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra votar agora.', 'error')
      if (err instanceof ApiError && (err.status === 409 || err.status === 422)) {
        // Algo mudou (voto já registrado, indicado saiu): recarrega a lista
        api<AwardsData>('/awards').then(setData).catch(() => undefined)
        setConfirming(null)
      }
    } finally {
      setVoting(false)
    }
  }

  if (error) return <p className="p-10 text-center text-muted">{error}</p>
  if (!data) return <PageLoader />

  const active = data.categories[index] as AwardCategory | undefined
  const activeSelected = active ? selected[active.id] : undefined
  const votedCount = data.categories.filter((c) => c.my_vote).length
  const nextPending = data.categories.findIndex((c, i) => i > index && !c.my_vote)

  return (
    <div>
      <AwardsHeader>
        {data.can_vote && total > 0 && (
          <div className="mt-4 max-w-sm">
            <div className="flex justify-between text-sm font-semibold text-white/80">
              <span>Seus votos</span>
              <span>
                {votedCount}/{total}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/15">
              <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${(votedCount / total) * 100}%` }} />
            </div>
          </div>
        )}
      </AwardsHeader>

      {!data.can_vote && (
        <div className="mx-4 mt-6 flex flex-col items-center gap-3 rounded-2xl bg-brand-50 p-5 text-center md:mx-10 md:flex-row md:text-left">
          <p className="flex-1 font-semibold text-brand-800">Você pode espiar as categorias, mas só vota quem garantiu ingresso.</p>
          <ClaimTicketButton size="md" />
        </div>
      )}

      {total === 0 ? (
        <p className="p-10 text-center text-muted">Nenhuma categoria aberta ainda. Aguarde as cenas dos próximos capítulos!</p>
      ) : (
        <>
          {/* bolinhas de navegação */}
          <div className="flex justify-center gap-2 pt-6" role="tablist" aria-label="Categorias">
            {data.categories.map((c, i) => (
              <button
                key={c.id}
                role="tab"
                aria-selected={i === index}
                aria-label={`${c.title}${c.my_vote ? ' (votado)' : ''}`}
                onClick={() => setIndex(i)}
                className={`grid h-8 place-items-center rounded-full text-sm transition-all ${
                  i === index ? 'w-12 bg-brand-600 text-white' : c.my_vote ? 'w-8 bg-ink text-white' : 'w-8 bg-surface'
                }`}
              >
                {c.my_vote ? <Check className="size-4" /> : c.emoji}
              </button>
            ))}
          </div>

          <div className="overflow-x-clip" onPointerDown={onPointerDown} onPointerUp={onPointerUp} style={{ touchAction: 'pan-y' }}>
            <div className="flex transition-transform duration-300 ease-out" style={{ transform: `translateX(-${index * 100}%)` }}>
              {data.categories.map((category, i) => (
                <section key={category.id} className="w-full shrink-0 px-12 pt-5 pb-28 md:px-20 md:pt-6 md:pb-6" inert={i !== index} aria-roledescription="slide">
                  <CategorySlide
                    category={category}
                    canVote={data.can_vote}
                    selected={selected[category.id]}
                    onSelect={(n) => setSelected((s) => ({ ...s, [category.id]: n }))}
                    onNext={nextPending > -1 && i === index ? () => setIndex(nextPending) : undefined}
                  />
                </section>
              ))}
            </div>
          </div>

          {data.can_vote && active && !active.my_vote && active.nominees.length > 0 && (
            <div className="fixed inset-x-0 bottom-(--bottom-nav) z-10 border-t border-line bg-white/95 px-4 py-3 backdrop-blur md:sticky md:bottom-0 md:border-0 md:bg-white/90 md:px-20 md:py-5">
              <Button size="lg" className="w-full md:mx-auto md:flex md:max-w-2xl" disabled={!activeSelected} onClick={() => setConfirming(active)}>
                {activeSelected ? `Votar em ${activeSelected.name}` : 'Escolha alguém'}
              </Button>
            </div>
          )}

          {/* setas nas laterais da tela */}
          <Arrow side="left" disabled={index === 0} onClick={() => go(-1)} />
          <Arrow side="right" disabled={index === total - 1} onClick={() => go(1)} />
        </>
      )}

      <ConfirmDialog
        open={confirming !== null}
        title={`Confirmar voto ${confirming?.emoji ?? ''}`}
        confirmLabel="Confirmar voto"
        loading={voting}
        onConfirm={confirmVote}
        onCancel={() => setConfirming(null)}
      >
        Votar em <strong className="text-ink">{confirming ? selected[confirming.id]?.name : ''}</strong> para{' '}
        <strong className="text-ink">{confirming?.title}</strong>? Depois de confirmado, não dá pra mudar.
      </ConfirmDialog>
    </div>
  )
}

function Arrow({ side, disabled, onClick }: { side: 'left' | 'right'; disabled: boolean; onClick: () => void }) {
  const Icon = side === 'left' ? ChevronLeft : ChevronRight
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={side === 'left' ? 'Categoria anterior' : 'Próxima categoria'}
      className={`fixed top-1/2 z-10 grid size-10 -translate-y-1/2 place-items-center rounded-full bg-white text-ink shadow-lg ring-1 ring-line transition hover:bg-brand-600 hover:text-white disabled:pointer-events-none disabled:opacity-0 md:size-12 ${
        side === 'left' ? 'left-1.5 md:left-[calc(16rem+1rem)]' : 'right-1.5 md:right-4'
      }`}
    >
      <Icon className="size-6" />
    </button>
  )
}

interface SlideProps {
  category: AwardCategory
  canVote: boolean
  selected?: Nominee
  onSelect: (nominee: Nominee) => void
  onNext?: () => void
}

function CategorySlide({ category, canVote, selected, onSelect, onNext }: SlideProps) {
  const [query, setQuery] = useState('')
  const { my_vote: myVote } = category
  const isCouple = category.kind === 'couple'

  const nominees = useMemo(() => {
    const q = query.trim().toLocaleLowerCase('pt-BR')
    if (!q) return category.nominees
    return category.nominees.filter((n) => n.name.toLocaleLowerCase('pt-BR').includes(q))
  }, [category.nominees, query])

  return (
    <div className="mx-auto max-w-2xl">
      <div className="text-center">
        <p className="text-5xl md:text-6xl" aria-hidden>
          {category.emoji}
        </p>
        <h2 className="mt-2 font-display text-2xl tracking-wide uppercase md:mt-3 md:text-4xl">{category.title}</h2>
        {category.description && <p className="mx-auto mt-1 max-w-md text-muted">{category.description}</p>}
        {category.i_am_nominee && (
          <p className="mt-3 inline-block rounded-full bg-brand-50 px-3 py-1 text-xs font-bold text-brand-700">
            👀 Você está concorrendo aqui
          </p>
        )}
      </div>

      {myVote && (
        <div className="animate-pop mt-6 rounded-2xl bg-ink p-5 text-center text-white">
          <p className="text-sm text-white/70">Seu voto</p>
          <p className="mt-1 text-2xl font-extrabold">{myVote.nominee.name} ✅</p>
          {onNext && (
            <button onClick={onNext} className={buttonClass('primary', 'md', 'mt-4')}>
              Próxima categoria <ChevronRight className="size-4" />
            </button>
          )}
        </div>
      )}

      {category.nominees.length === 0 ? (
        <div className="mt-8 rounded-2xl bg-surface p-6 text-center text-muted">
          {isCouple ? (
            <>
              Nenhum casal confirmado ainda. Os dois precisam se escolher como par na aba{' '}
              <Link to="/conta" className="font-bold text-brand-600 underline">
                Conta
              </Link>{' '}
              💘
            </>
          ) : (
            'Ninguém concorrendo além de você ainda. Chama a galera pra garantir o ingresso!'
          )}
        </div>
      ) : (
        <>
          {category.nominees.length > 8 && !myVote && (
            <label className="relative mt-6 block">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" aria-hidden />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar pelo nome"
                className="h-11 w-full rounded-xl pr-4 pl-9 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
              />
            </label>
          )}

          <ul className="mt-6 grid gap-2 sm:grid-cols-2">
            {nominees.map((nominee) => {
              const isVoted = myVote?.nominee.id === nominee.id
              const isSelected = !myVote && selected?.id === nominee.id
              return (
                <li key={nominee.id}>
                  <button
                    onClick={() => onSelect(nominee)}
                    disabled={!canVote || Boolean(myVote)}
                    aria-pressed={isSelected}
                    className={`flex w-full items-center gap-3 rounded-2xl p-3 text-left ring-1 transition disabled:cursor-default ${
                      isSelected || isVoted ? 'bg-brand-50 ring-2 ring-brand-600' : 'ring-line enabled:hover:bg-surface'
                    } ${myVote && !isVoted ? 'opacity-45' : ''}`}
                  >
                    <span className="flex -space-x-3">
                      {nominee.members.map((m) => (
                        <Avatar key={m} name={m} />
                      ))}
                    </span>
                    <span className="flex-1 font-bold">{nominee.name}</span>
                    {(isSelected || isVoted) && (
                      <span className="grid size-6 place-items-center rounded-full bg-brand-600 text-white">
                        <Check className="size-4" />
                      </span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>

        </>
      )}
    </div>
  )
}
