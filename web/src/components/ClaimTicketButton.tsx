import { Ticket } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'
import { useClaimTicket } from '../lib/useClaimTicket'
import { buttonClass } from './button-class'
import { Button } from './ui'

interface Props {
  className?: string
  size?: 'md' | 'lg'
}

/** O botão principal do site: "Garanta seu ingresso". */
export function ClaimTicketButton({ className = '', size = 'lg' }: Props) {
  const { me } = useAuth()
  const navigate = useNavigate()
  const { claim, claiming } = useClaimTicket()

  if (me?.has_ticket) {
    return (
      <Link to="/ingresso" className={buttonClass('primary', size, className)}>
        <Ticket className="size-5" aria-hidden />
        Ver meu ingresso
      </Link>
    )
  }

  function handleClick() {
    if (!me) {
      navigate('/entrar', { state: { claim: true } })
      return
    }
    void claim()
  }

  return (
    <Button size={size} className={className} onClick={handleClick} loading={claiming}>
      Garanta seu ingresso
    </Button>
  )
}
