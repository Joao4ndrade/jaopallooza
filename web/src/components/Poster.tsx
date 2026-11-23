import { useId } from 'react'

interface PosterProps {
  className?: string
  year?: string
}

const CENTER = { x: 150, y: 262 }
const RAYS = Array.from({ length: 14 }, (_, i) => {
  // Raios de "sol nascente" atrás do palco, estilo xilogravura.
  const step = Math.PI / 14
  const a1 = Math.PI + i * step
  const a2 = a1 + step / 2
  const r = 320
  return `M${CENTER.x},${CENTER.y} L${CENTER.x + r * Math.cos(a1)},${CENTER.y + r * Math.sin(a1)} L${
    CENTER.x + r * Math.cos(a2)
  },${CENTER.y + r * Math.sin(a2)} Z`
})

const HEADS = [18, 52, 88, 122, 162, 196, 232, 268, 290]
const ARMS: [number, number, number, number][] = [
  [40, 352, 22, 300],
  [70, 350, 84, 296],
  [140, 350, 128, 292],
  [178, 352, 196, 300],
  [250, 350, 236, 294],
  [284, 352, 300, 306],
]

/** Cartaz do JAOPALLOOZA em SVG: vermelho e preto, título em arco, sol, multidão. */
export function Poster({ className = '', year = '2027' }: PosterProps) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, '')
  const arcId = `arc-${id}`
  const clipId = `clip-${id}`

  return (
    <svg
      viewBox="0 0 300 400"
      className={className}
      role="img"
      aria-label={`Cartaz do JAOPALLOOZA ${year}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <path id={arcId} d="M 14 112 Q 150 8 286 112" />
        <clipPath id={clipId}>
          <rect x="0" y="150" width="300" height="250" />
        </clipPath>
      </defs>

      <rect width="300" height="400" fill="#e3261c" />

      <g clipPath={`url(#${clipId})`} fill="#121212">
        {RAYS.map((d) => (
          <path key={d} d={d} />
        ))}
      </g>

      {/* sol / palco */}
      <circle cx={CENTER.x} cy={CENTER.y} r="64" fill="#e3261c" stroke="#121212" strokeWidth="7" />
      <circle cx={CENTER.x} cy={CENTER.y} r="50" fill="none" stroke="#121212" strokeWidth="2" strokeDasharray="4 6" />
      <text
        x={CENTER.x}
        y={CENTER.y + 15}
        textAnchor="middle"
        fontFamily="Anton, Impact, sans-serif"
        fontSize="44"
        fill="#fff"
      >
        {year}
      </text>

      {/* multidão */}
      <g fill="#121212" stroke="#121212">
        {ARMS.map(([x1, y1, x2, y2]) => (
          <line key={`${x1}-${y1}`} x1={x1} y1={y1} x2={x2} y2={y2} strokeWidth="9" strokeLinecap="round" />
        ))}
        {HEADS.map((x, i) => (
          <circle key={x} cx={x} cy={i % 2 ? 340 : 346} r="15" stroke="none" />
        ))}
        <rect x="0" y="350" width="300" height="50" stroke="none" />
      </g>

      {/* título em arco */}
      <text fontFamily="Anton, Impact, sans-serif" fontSize="50" fill="#fff" letterSpacing="1">
        <textPath href={`#${arcId}`} startOffset="50%" textAnchor="middle">
          JAOPALLOOZA
        </textPath>
      </text>
      <text
        x="150"
        y="140"
        textAnchor="middle"
        fontFamily="Anton, Impact, sans-serif"
        fontSize="17"
        letterSpacing="3"
        fill="#121212"
      >
        ANIVERSÁRIO DO JOÃO
      </text>
      <text
        x="150"
        y="386"
        textAnchor="middle"
        fontFamily="Anton, Impact, sans-serif"
        fontSize="15"
        letterSpacing="4"
        fill="#e3261c"
      >
        DATA E LOCAL EM BREVE
      </text>
    </svg>
  )
}
