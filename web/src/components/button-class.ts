export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'md' | 'lg'

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm shadow-brand-900/20',
  secondary: 'bg-white text-ink ring-1 ring-inset ring-line hover:bg-surface',
  ghost: 'text-ink hover:bg-surface',
  danger: 'bg-white text-brand-600 ring-1 ring-inset ring-brand-200 hover:bg-brand-50',
}

/** Classes de botão, reaproveitadas também em <Link>s com cara de botão. */
export function buttonClass(variant: ButtonVariant = 'primary', size: ButtonSize = 'md', extra = '') {
  const sizing = size === 'lg' ? 'h-14 px-6 text-lg' : 'h-11 px-4 text-[15px]'
  return `inline-flex items-center justify-center gap-2 rounded-xl font-bold transition active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${sizing} ${VARIANTS[variant]} ${extra}`
}
