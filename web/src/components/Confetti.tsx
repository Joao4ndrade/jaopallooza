const EMOJIS = ['🎉', '🎊', '✨', '🎈', '🎟️', '❤️']

// Posições "aleatórias" determinísticas: render puro e sem pulos entre re-renders.
const PIECES = Array.from({ length: 28 }, (_, i) => ({
  id: i,
  emoji: EMOJIS[i % EMOJIS.length],
  left: (i * 37 + 11) % 100,
  delay: ((i * 13) % 9) / 10,
  size: 16 + ((i * 7) % 18),
}))

/** Chuva de confete de ~3s para comemorar o ingresso garantido. */
export function Confetti() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-30 overflow-hidden">
      {PIECES.map((p) => (
        <span
          key={p.id}
          className="animate-confetti absolute -top-10"
          style={{ left: `${p.left}%`, animationDelay: `${p.delay}s`, fontSize: p.size }}
        >
          {p.emoji}
        </span>
      ))}
    </div>
  )
}
