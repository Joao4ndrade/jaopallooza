import { Link } from 'react-router-dom'
import { buttonClass } from '../components/button-class'

export function NotFoundPage() {
  return (
    <div className="grid min-h-[70dvh] place-items-center px-4 text-center">
      <div>
        <p className="font-display text-8xl text-brand-600">404</p>
        <h1 className="mt-2 text-2xl font-extrabold">Essa página não tá na line-up</h1>
        <p className="mt-1 text-muted">Mas a festa continua lá no início.</p>
        <Link to="/" className={buttonClass('primary', 'lg', 'mt-6')}>
          Voltar pro evento
        </Link>
      </div>
    </div>
  )
}
