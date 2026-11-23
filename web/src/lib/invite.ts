const INVITE_KEY = 'jaopallooza:invite'

/**
 * Se o link compartilhado tiver ?convite=XYZ, guarda o código para o cadastro
 * e limpa a URL. Assim o convite vai junto sem a pessoa precisar digitar.
 */
export function captureInviteFromUrl() {
  const url = new URL(window.location.href)
  const code = url.searchParams.get('convite')
  if (!code) return
  try {
    sessionStorage.setItem(INVITE_KEY, code)
  } catch {
    /* sem storage, a pessoa digita no formulário */
  }
  url.searchParams.delete('convite')
  window.history.replaceState(null, '', url.toString())
}

export function storedInvite(): string {
  try {
    return sessionStorage.getItem(INVITE_KEY) ?? ''
  } catch {
    return ''
  }
}
