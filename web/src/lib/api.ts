const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'
const TOKEN_KEY = 'jaopallooza:token'

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string) {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* modo anônimo sem storage: segue só nesta aba */
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* idem */
    }
  },
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

let onUnauthorized: (() => void) | null = null

/** Chamado quando o token expira ou a conta deixa de existir. */
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
}

export async function api<T>(path: string, { method = 'GET', body }: RequestOptions = {}): Promise<T> {
  const token = tokenStore.get()
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'Sem conexão com o servidor. Tenta de novo?')
  }

  if (response.status === 204) return undefined as T
  const data: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized?.()
    throw new ApiError(response.status, errorMessage(data))
  }
  return data as T
}

interface ValidationIssue {
  loc?: (string | number)[]
  msg?: string
  type?: string
}

function errorMessage(data: unknown): string {
  const detail = (data as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const issue = detail[0] as ValidationIssue
    const field = issue.loc?.at(-1)
    if (field === 'password' && issue.type === 'string_too_short') {
      return 'A senha precisa ter pelo menos 6 caracteres.'
    }
    if (field === 'name' && issue.type === 'string_too_long') {
      return 'O nome pode ter no máximo 30 caracteres.'
    }
    if (issue.msg?.startsWith('Value error, ')) return issue.msg.replace('Value error, ', '')
    return 'Confere os dados e tenta de novo.'
  }
  return 'Algo deu errado. Tenta de novo em instantes.'
}
