import { LoaderCircle } from 'lucide-react'
import type { ComponentProps, ReactNode } from 'react'
import { buttonClass, type ButtonSize, type ButtonVariant } from './button-class'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

export function Button({ variant = 'primary', size = 'md', loading, className = '', children, disabled, ...rest }: ButtonProps) {
  return (
    <button className={buttonClass(variant, size, className)} disabled={disabled || loading} {...rest}>
      {loading && <LoaderCircle className="size-5 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl bg-white p-5 ring-1 ring-line ${className}`}>{children}</section>
}

export function PageLoader() {
  return (
    <div className="grid min-h-[50dvh] place-items-center" role="status" aria-label="Carregando">
      <LoaderCircle className="size-8 animate-spin text-brand-600" />
    </div>
  )
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children?: ReactNode }) {
  return (
    <header className="px-4 pt-8 pb-4 md:px-10 md:pt-12">
      <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">{title}</h1>
      {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
      {children}
    </header>
  )
}
