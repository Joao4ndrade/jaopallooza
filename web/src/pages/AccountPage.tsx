import { Camera, HeartCrack, LogOut, Mail, ShieldCheck, Trash2, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Avatar } from '../components/Avatar'
import { ClaimTicketButton } from '../components/ClaimTicketButton'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { useToast } from '../components/toast-context'
import { buttonClass } from '../components/button-class'
import { Button, Card, PageHeader, PageLoader } from '../components/ui'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth-context'
import { preparePhoto } from '../lib/preparePhoto'
import type { Me, Person } from '../lib/types'

type Dialog = 'leave-awards' | 'delete' | null

export function AccountPage() {
  const { me, loading } = useAuth()

  if (loading) return <PageLoader />
  if (!me) {
    return (
      <div>
        <PageHeader title="Conta" />
        <div className="mx-auto max-w-md px-4 text-center">
          <p className="text-5xl">👋</p>
          <h2 className="mt-4 text-xl font-extrabold">Você ainda não entrou</h2>
          <p className="mt-1 text-muted">Crie sua conta com nome e senha pra garantir o ingresso e votar no Awards.</p>
          <div className="mt-6 flex flex-col gap-2">
            <ClaimTicketButton className="w-full" />
            <Link to="/entrar" className={buttonClass('secondary', 'lg', 'w-full')}>
              Já tenho conta
            </Link>
          </div>
        </div>
      </div>
    )
  }
  return <AccountDetails me={me} />
}

function AccountDetails({ me }: { me: Me }) {
  const { logout, setMe } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [dialog, setDialog] = useState<Dialog>(null)
  const [busy, setBusy] = useState(false)

  async function run<T>(action: () => Promise<T>, success?: string) {
    setBusy(true)
    try {
      const result = await action()
      if (success) toast(success)
      return result
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Algo deu errado.', 'error')
      return undefined
    } finally {
      setBusy(false)
    }
  }

  async function setAwards(optIn: boolean) {
    const updated = await run(
      () => api<Me>('/me/awards', { method: 'PUT', body: { opt_in: optIn } }),
      optIn ? 'Você voltou pra disputa! 🏆' : 'Você saiu da votação.',
    )
    if (updated) setMe(updated)
    setDialog(null)
  }

  async function deleteAccount() {
    const done = await run(() => api<void>('/me', { method: 'DELETE' }).then(() => true))
    if (done) {
      logout()
      toast('Conta excluída. Vamos sentir sua falta 💔')
      navigate('/')
    }
  }

  return (
    <div className="pb-10">
      <PageHeader title="Conta" />

      <div className="mx-auto flex max-w-2xl flex-col gap-4 px-4 md:mx-0 md:px-10">
        <ProfileCard me={me} onChange={setMe} />

        <EmailCard me={me} onChange={setMe} />

        <Card>
          <h2 className="text-lg font-extrabold">Concorrendo no Awards</h2>
          {!me.has_ticket ? (
            <>
              <p className="mt-1 text-muted">Garanta seu ingresso pra entrar na disputa (e pra votar).</p>
              <ClaimTicketButton size="md" className="mt-4" />
            </>
          ) : !me.awards_opt_in ? (
            <>
              <p className="mt-1 text-muted">Você saiu da votação: ninguém pode votar em você, mas você continua votando normalmente.</p>
              <Button className="mt-4" onClick={() => setAwards(true)} loading={busy}>
                Voltar a concorrer
              </Button>
            </>
          ) : (
            <>
              {me.competing_in.length > 0 ? (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {me.competing_in.map((c) => (
                    <li key={c.id} className="rounded-full bg-brand-50 px-3 py-1.5 text-sm font-bold text-brand-700">
                      {c.emoji} {c.title}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-muted">Nenhuma categoria aberta no momento.</p>
              )}
              <Button variant="secondary" className="mt-4" onClick={() => setDialog('leave-awards')}>
                Sair da votação
              </Button>
            </>
          )}
        </Card>

        {me.has_ticket && <PartnerCard me={me} onChange={setMe} />}

        {me.is_admin && (
          <Card>
            <h2 className="flex items-center gap-2 text-lg font-extrabold">
              <ShieldCheck className="size-5 text-brand-600" /> Organização
            </h2>
            <p className="mt-1 text-muted">
              Lista de convidados, resultado do Awards, edição do evento e reset de senha ficam no painel da API (faça login no
              botão “Authorize”). Para o check-in, é só escanear o QR code do ingresso com a câmera do celular.
            </p>
            <a href="/api/docs" target="_blank" rel="noreferrer" className={buttonClass('secondary', 'md', 'mt-4')}>
              Abrir painel da API
            </a>
          </Card>
        )}

        <Card>
          <Button variant="ghost" className="-ml-2" onClick={logout}>
            <LogOut className="size-5" /> Sair da conta
          </Button>
        </Card>

        <section className="rounded-2xl p-5 ring-1 ring-brand-200">
          <h2 className="text-lg font-extrabold text-brand-700">Zona de perigo</h2>
          <p className="mt-1 text-sm text-muted">Mudou de planos? Cancelar a presença apaga sua conta, seu ingresso e seus votos.</p>
          <Button variant="danger" className="mt-4" onClick={() => setDialog('delete')}>
            <Trash2 className="size-5" /> Cancelar presença e excluir conta
          </Button>
        </section>
      </div>

      <ConfirmDialog
        open={dialog === 'leave-awards'}
        title="Sair da votação?"
        confirmLabel="Sair da votação"
        destructive
        loading={busy}
        onConfirm={() => setAwards(false)}
        onCancel={() => setDialog(null)}
      >
        Você deixa de concorrer em todas as categorias e os votos que recebeu são descartados. Você continua podendo votar e pode
        voltar a concorrer quando quiser.
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === 'delete'}
        title="Cancelar presença? 😢"
        confirmLabel="Excluir minha conta"
        cancelLabel="Mudei de ideia"
        destructive
        loading={busy}
        onConfirm={deleteAccount}
        onCancel={() => setDialog(null)}
      >
        Isso apaga sua conta, seu ingresso e todos os seus votos. <strong className="text-ink">Não tem como desfazer.</strong>
      </ConfirmDialog>
    </div>
  )
}

function ProfileCard({ me, onChange }: { me: Me; onChange: (me: Me) => void }) {
  const toast = useToast()
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<{ blob: Blob; url: string } | null>(null)
  const [saving, setSaving] = useState(false)

  const openPicker = () => inputRef.current?.click()

  async function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = '' // permite escolher a mesma foto de novo
    if (!file) return
    try {
      const blob = await preparePhoto(file)
      setPreview({ blob, url: URL.createObjectURL(blob) })
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Não deu pra abrir essa foto.', 'error')
    }
  }

  function closePreview() {
    if (preview) URL.revokeObjectURL(preview.url)
    setPreview(null)
  }

  async function save() {
    if (!preview) return
    const form = new FormData()
    form.append('file', preview.blob, 'foto.jpg')
    setSaving(true)
    try {
      onChange(await api<Me>('/me/photo', { method: 'PUT', body: form }))
      toast('Foto atualizada! 📸')
      closePreview()
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra salvar a foto.', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    setSaving(true)
    try {
      onChange(await api<Me>('/me/photo', { method: 'DELETE' }))
      toast('Foto removida.')
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra remover a foto.', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="flex items-center gap-4">
      <button
        type="button"
        onClick={openPicker}
        aria-label={me.photo_url ? 'Trocar foto de perfil' : 'Adicionar foto de perfil'}
        className="relative shrink-0 rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
      >
        <Avatar name={me.name} photoUrl={me.photo_url} size="lg" />
        <span className="absolute -right-1 -bottom-1 grid size-8 place-items-center rounded-full bg-brand-600 text-white ring-4 ring-white">
          <Camera className="size-4" aria-hidden />
        </span>
      </button>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />

      <div className="min-w-0">
        <p className="truncate text-2xl font-extrabold">{me.name}</p>
        <div className="mt-1 flex flex-wrap gap-2 text-xs font-bold">
          <span className={`rounded-full px-2.5 py-1 ${me.has_ticket ? 'bg-ink text-white' : 'bg-surface text-muted'}`}>
            {me.has_ticket ? '🎟️ Ingresso garantido' : 'Sem ingresso'}
          </span>
          {me.is_admin && <span className="rounded-full bg-brand-600 px-2.5 py-1 text-white">Organização</span>}
        </div>
        {me.photo_url ? (
          <button type="button" onClick={remove} disabled={saving} className="mt-2 text-xs font-semibold text-muted hover:text-brand-600 hover:underline">
            Remover foto
          </button>
        ) : (
          <button type="button" onClick={openPicker} className="mt-2 text-xs font-semibold text-brand-600 hover:underline">
            📸 Adicionar foto
          </button>
        )}
      </div>

      <ConfirmDialog
        open={preview !== null}
        title="Usar esta foto?"
        confirmLabel="Salvar foto"
        cancelLabel="Cancelar"
        loading={saving}
        onConfirm={save}
        onCancel={closePreview}
      >
        {preview && <img src={preview.url} alt="Prévia da foto de perfil" className="mx-auto mt-2 size-40 rounded-full object-cover" />}
        <p className="mt-3 text-center text-sm">Ela aparece pra galera no Awards e na lista de presenças.</p>
      </ConfirmDialog>
    </Card>
  )
}

function EmailCard({ me, onChange }: { me: Me; onChange: (me: Me) => void }) {
  const toast = useToast()
  const [editing, setEditing] = useState(false)
  const [email, setEmail] = useState(me.email ?? '')
  const [saving, setSaving] = useState(false)

  async function save(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      onChange(await api<Me>('/me/email', { method: 'PUT', body: { email } }))
      toast('E-mail salvo! 📬')
      setEditing(false)
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra salvar.', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <h2 className="flex items-center gap-2 text-lg font-extrabold">
        <Mail className="size-5" aria-hidden /> E-mail de recuperação
      </h2>
      {editing ? (
        <form onSubmit={save} className="mt-3 flex flex-col gap-2 sm:flex-row">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
            autoComplete="email"
            placeholder="voce@exemplo.com"
            className="h-11 flex-1 rounded-xl px-4 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
          />
          <div className="flex gap-2">
            <Button type="submit" loading={saving}>
              Salvar
            </Button>
            <Button type="button" variant="ghost" onClick={() => setEditing(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      ) : (
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          {me.email ? (
            <p className="text-muted">{me.email}</p>
          ) : (
            <p className="flex items-center gap-2 text-sm font-semibold text-amber-700">
              <TriangleAlert className="size-4" /> Sem e-mail: se esquecer a senha, não tem como recuperar.
            </p>
          )}
          <Button
            variant="secondary"
            onClick={() => {
              setEmail(me.email ?? '')
              setEditing(true)
            }}
          >
            {me.email ? 'Alterar' : 'Adicionar e-mail'}
          </Button>
        </div>
      )}
    </Card>
  )
}

function PartnerCard({ me, onChange }: { me: Me; onChange: (me: Me) => void }) {
  const toast = useToast()
  const [options, setOptions] = useState<Person[] | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api<Person[]>('/me/partner-options')
      .then(setOptions)
      .catch(() => setOptions([]))
  }, [])

  async function choose(partnerId: string | null) {
    setSaving(true)
    try {
      const updated = await api<Me>('/me/partner', { method: 'PUT', body: { partner_id: partnerId } })
      onChange(updated)
      if (updated.partner_status === 'confirmed') toast('Casal confirmado! Vocês concorrem a Melhor casal 💘')
      else if (updated.partner_status === 'pending') toast(`Pedido enviado! Agora ${updated.partner?.name} precisa confirmar.`)
      else toast('Par removido.')
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra salvar.', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <h2 className="text-lg font-extrabold">Meu par 💘</h2>
      <p className="mt-1 text-sm text-muted">
        Pra concorrer a <strong>Melhor casal</strong>, os dois precisam se escolher aqui. Só vale quando é recíproco.
      </p>

      {me.partner_requests.map((p) => (
        <div key={p.id} className="mt-4 flex items-center gap-3 rounded-2xl bg-brand-50 p-3">
          <Avatar name={p.name} photoUrl={p.photo_url} size="sm" />
          <p className="flex-1 text-sm">
            <strong>{p.name}</strong> escolheu você como par!
          </p>
          <Button className="h-9 px-3 text-sm" onClick={() => choose(p.id)} loading={saving}>
            Confirmar
          </Button>
        </div>
      ))}

      {me.partner && (
        <div className="mt-4 flex items-center gap-3 rounded-2xl bg-surface p-3">
          <span className="flex -space-x-3">
            <Avatar name={me.name} photoUrl={me.photo_url} size="sm" className="ring-2 ring-surface" />
            <Avatar name={me.partner.name} photoUrl={me.partner.photo_url} size="sm" className="ring-2 ring-surface" />
          </span>
          <p className="flex-1 text-sm">
            {me.partner_status === 'confirmed' ? (
              <>
                <strong>Casal confirmado</strong> com {me.partner.name} ✅
              </>
            ) : (
              <>
                Esperando <strong>{me.partner.name}</strong> confirmar…
              </>
            )}
          </p>
          <button
            onClick={() => choose(null)}
            disabled={saving}
            className="grid size-9 place-items-center rounded-full text-muted hover:bg-white hover:text-brand-600"
            aria-label="Desfazer par"
            title="Desfazer par"
          >
            <HeartCrack className="size-5" />
          </button>
        </div>
      )}

      <label className="mt-4 flex flex-col gap-1.5">
        <span className="text-sm font-bold">{me.partner ? 'Trocar par' : 'Escolher par'}</span>
        <select
          value={me.partner?.id ?? ''}
          disabled={saving || options === null}
          onChange={(e) => choose(e.target.value || null)}
          className="h-12 rounded-xl bg-white px-3 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600"
        >
          <option value="">{options === null ? 'Carregando…' : 'Ninguém (solteiro(a) e feliz)'}</option>
          {options?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
    </Card>
  )
}
