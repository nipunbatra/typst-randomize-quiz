// Subject demo: introductory mechanics — units, numerics, a projectile figure.

#import "/quizforge/lib.typ": *

#let trajectory-fig = {
  let w = 6cm
  let h = 3.2cm
  align(center, box(width: w + 1.2cm, height: h + 1cm, inset: (left: 0.7cm, bottom: 0.7cm, top: 0.3cm, right: 0.5cm), {
    place(bottom + left, line(length: w, stroke: 0.6pt))
    place(bottom + left, line(angle: -90deg, length: h, stroke: 0.6pt))
    place(bottom + left, curve(
      stroke: 1pt,
      curve.move((0cm, 0cm)),
      curve.cubic((w * 0.3, -h * 1.25), (w * 0.7, -h * 1.25), (w, 0cm)),
    ))
    place(bottom + left, dx: 0.9cm, dy: -0.12cm, text(size: 9pt, [$theta$]))
    place(bottom + left, line(angle: -52deg, length: 1.1cm, stroke: (thickness: 0.7pt, dash: "dashed")))
    place(bottom + center, dy: 0.5cm, text(size: 9pt, [range $R$]))
  }))
}

#show: quiz.with(
  id: "ph101-demo",
  course: "PH 101: Mechanics",
  title: "Quiz 2 — Kinematics & Momentum",
  duration: "30 minutes",
  sets: ("A", "B"),
  answer-grid: true,
  instructions: ([Take $g = 10 "m/s"^2$ unless stated otherwise.],),
)

= Multiple Choice

+ #m(2) A projectile is launched over level ground with fixed speed and launch
  angle $theta$ (air resistance neglected).
  #trajectory-fig
  Which $theta$ maximizes the range $R$?
  - ✓ $45 degree$
  - $30 degree$
  - $60 degree$
  - $90 degree$
  #explain[$R = (v^2 sin 2theta) \/ g$ is maximal when $sin 2theta = 1$.]

+ #m(2) A ball is dropped from rest from a height of $20 "m"$. How long does it
  take to reach the ground?
  - ✓ $2 "s"$
  - $4 "s"$
  - $1 "s"$
  - $sqrt(2) "s"$
  #explain[$t = sqrt(2h\/g) = sqrt(4) = 2 "s"$.]

+ #m(2) In a perfectly *inelastic* collision, which quantity is generally
  #emph[not] conserved?
  - ✓ Kinetic energy
  - Linear momentum
  - Total energy
  - Mass

= Fill in the Blanks

+ #m(1) "For every action there is an equal and opposite reaction" is Newton's
  #blank(width: 1.8cm)[third] law.

+ #m(1) The SI unit of power is the #blank[watt], equal to one joule per second.

= Short Answer

+ #m(4) Starting from $v = u + a t$ and $s = u t + 1/2 a t^2$, derive
  $v^2 = u^2 + 2 a s$.
  #answer(6cm, rubric: [+1 solve first equation for $t$; +2 substitution;
    +1 algebra to the final form.])[
    From the first equation $t = (v - u)\/a$. Substituting,
    $s = u (v - u)\/a + 1/2 a ((v - u)\/a)^2 = (v^2 - u^2)\/(2a)$,
    hence $v^2 = u^2 + 2 a s$.]
