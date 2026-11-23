import { PartyPopper, Ticket, Trophy, UserRound, type LucideIcon } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'
import { Avatar } from './Avatar'
import { Logo } from './Logo'
import { buttonClass } from './button-class'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

const NAV: NavItem[] = [
  { to: '/', label: 'Evento', icon: PartyPopper },
  { to: '/awards', label: 'Awards', icon: Trophy },
  { to: '/ingresso', label: 'Ingresso', icon: Ticket },
  { to: '/conta', label: 'Conta', icon: UserRound },
]

export function AppShell() {
  return (
    <div className="min-h-dvh md:pl-64">
      <Sidebar />
      <main className="pb-(--bottom-nav) md:pb-0">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  )
}

function Sidebar() {
  const { me } = useAuth()

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-line bg-white px-4 py-6 md:flex">
      <Logo className="px-2" />

      <nav className="mt-10 flex flex-col gap-1" aria-label="Principal">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-xl px-3 py-3 font-semibold transition ${
                isActive ? 'bg-brand-50 text-brand-600' : 'text-muted hover:bg-surface hover:text-ink'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute inset-y-2 left-0 w-1 rounded-full bg-brand-600" />}
                <Icon className="size-5" strokeWidth={isActive ? 2.4 : 2} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto">
        {me ? (
          <NavLink to="/conta" className="flex items-center gap-3 rounded-xl p-2 hover:bg-surface">
            <Avatar name={me.name} size="sm" />
            <span className="min-w-0">
              <span className="block truncate font-bold">{me.name}</span>
              <span className="block text-xs text-muted">{me.has_ticket ? '🎟️ Ingresso garantido' : 'Sem ingresso ainda'}</span>
            </span>
          </NavLink>
        ) : (
          <NavLink to="/entrar" className={buttonClass('secondary', 'md', 'w-full')}>
            Entrar
          </NavLink>
        )}
      </div>
    </aside>
  )
}

function BottomNav() {
  return (
    <nav
      aria-label="Principal"
      className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
    >
      <ul className="grid h-16 grid-cols-4">
        {NAV.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex h-full flex-col items-center justify-center gap-1 text-xs font-semibold transition ${
                  isActive ? 'text-brand-600' : 'text-muted'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="size-6" strokeWidth={isActive ? 2.4 : 1.8} />
                  {label}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
