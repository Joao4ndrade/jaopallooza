import type { ReactNode } from 'react'
import { Logo } from './Logo'

/** Moldura das telas de login, cadastro e recuperação de senha. */
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex min-h-[calc(100dvh-var(--bottom-nav))] items-center justify-center bg-surface px-4 py-10 md:min-h-dvh">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center md:hidden">
          <Logo />
        </div>
        <div className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-line sm:p-8">
          <h1 className="text-2xl font-extrabold">{title}</h1>
          {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  )
}

export const inputClass =
  'h-12 w-full rounded-xl px-4 ring-1 ring-line outline-none focus:ring-2 focus:ring-brand-600 aria-invalid:ring-brand-600'

export function FormError({ children }: { children: ReactNode }) {
  return (
    <p role="alert" className="rounded-xl bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-700">
      {children}
    </p>
  )
}
