"use client"

import { motion } from "framer-motion"

type Shot = {
  x: number
  y: number
  xg: number
  player: string
  minute: number
  result: string
}

const shots: Shot[] = [
  { x: 92, y: 50, xg: 0.42, player: "Lautaro Martínez", minute: 41, result: "Goal" },
  { x: 85, y: 60, xg: 0.22, player: "Barella", minute: 36, result: "SavedShot" },
  { x: 88, y: 40, xg: 0.18, player: "Dimarco", minute: 55, result: "BlockedShot" },
  { x: 78, y: 55, xg: 0.08, player: "Thuram", minute: 72, result: "MissedShot" },
]

export default function PremiumShotMap() {

  return (

<div className="rounded-xl border border-white/10 bg-[#0b0f19] p-6">

<h2 className="text-white text-xl mb-4">
Cinematic Shot Map
</h2>

<svg
viewBox="0 0 120 80"
className="w-full h-[420px] bg-[#0e5f43] rounded-lg"
>

{/* Pitch */}

<g stroke="rgba(255,255,255,0.3)" strokeWidth="0.4" fill="none">

<rect x="0" y="0" width="120" height="80"/>

<line x1="60" y1="0" x2="60" y2="80"/>

<circle cx="60" cy="40" r="9"/>

<circle cx="60" cy="40" r="1" fill="white"/>

<rect x="102" y="18" width="18" height="44"/>
<rect x="0" y="18" width="18" height="44"/>

</g>


{/* SHOTS */}

{shots.map((shot,i)=>{

const size = 2 + shot.xg * 10
const goal = shot.result === "Goal"

return(

<g key={i}>

<motion.line
x1={shot.x}
y1={shot.y}
x2="120"
y2="40"
stroke="rgba(255,255,255,0.2)"
strokeWidth="0.5"
initial={{pathLength:0}}
animate={{pathLength:1}}
transition={{duration:1}}
/>

<motion.circle
cx={shot.x}
cy={shot.y}
r={size}
fill={goal ? "#ff3c6a" : "white"}
initial={{scale:0}}
animate={{scale:1}}
transition={{duration:0.4}}
/>

{goal && (

<motion.circle
cx={shot.x}
cy={shot.y}
r={size*2}
fill="rgba(255,60,106,0.3)"
animate={{scale:[1,1.4,1]}}
transition={{duration:0.6,repeat:2}}
/>

)}

</g>

)

})}

</svg>

</div>

  )
}