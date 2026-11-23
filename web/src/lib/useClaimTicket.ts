import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../components/toast-context'
import { api, ApiError } from './api'
import { useAuth } from './auth-context'

/** Garante o ingresso da pessoa logada e leva para a carteira com confete. */
export function useClaimTicket() {
  const { refresh } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [claiming, setClaiming] = useState(false)

  /** Retorna true se o ingresso foi garantido. */
  async function claim(): Promise<boolean> {
    setClaiming(true)
    try {
      await api('/tickets', { method: 'POST' })
      await refresh()
      navigate('/ingresso', { state: { justClaimed: true } })
      return true
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Não deu pra garantir agora. Tenta de novo?', 'error')
      return false
    } finally {
      setClaiming(false)
    }
  }

  return { claim, claiming }
}
