// Third-party package compatibility: question bodies, options, and blanks
// that use cetz (drawings), unify (SI units), and physica (physics notation).
// Needs network on first compile (typst downloads @preview packages).

#import "@preview/cetz:0.4.2"
#import "@preview/unify:0.7.1": qty, unit, num
#import "@preview/physica:0.9.5": dv, pdv, vb, curl, grad

#import "/quizforge/lib.typ": *

#let circuit = cetz.canvas(length: 0.8cm, {
  import cetz.draw: *
  rect((0, 0), (4, 2), stroke: 0.8pt)
  circle((0, 1), radius: 0.25, stroke: 0.8pt)
  content((0, 1), text(size: 8pt, [V]))
  line((1.6, 2), (1.8, 2.3), (2.0, 1.7), (2.2, 2.3), (2.4, 1.7), (2.6, 2), stroke: 0.8pt)
  content((2.1, 2.7), text(size: 8pt, [$R_1$]))
  line((1.6, 0), (1.8, 0.3), (2.0, -0.3), (2.2, 0.3), (2.4, -0.3), (2.6, 0), stroke: 0.8pt)
  content((2.1, -0.7), text(size: 8pt, [$R_2$]))
})

#show: quiz.with(
  id: "stress-packages",
  course: "QA 001: Package Compatibility",
  title: "Third-Party Package Torture",
  sets: ("A", "B"),
)

= Packages Everywhere

+ #m(2) The circuit below connects $R_1$ and $R_2$ in parallel across a source
  (cetz drawing in a question body).
  #align(center, circuit)
  With $R_1 = R_2 = qty("10", "ohm")$, the equivalent resistance is:
  - ✓ #qty("5", "ohm")
  - #qty("20", "ohm")
  - #qty("10", "ohm")
  - #qty("100", "ohm")
  #explain[Parallel: $R_"eq" = (R_1 R_2)\/(R_1 + R_2) = qty("5", "ohm")$.]

+ #m(2) Which cetz sketch shows a *closed* curve? (drawings inside options)
  - ✓ #box(cetz.canvas(length: 0.5cm, {
      import cetz.draw: *
      circle((0, 0), radius: 0.5, stroke: 0.8pt)
    }))
  - #box(cetz.canvas(length: 0.5cm, {
      import cetz.draw: *
      arc((0, 0), start: 0deg, stop: 250deg, radius: 0.5, stroke: 0.8pt)
    }))

+ #m(2) In physica notation, Faraday's law reads
  $curl vb(E) = -pdv(vb(B), t)$. The left-hand side is the:
  - ✓ curl of the electric field
  - divergence of the electric field
  - gradient of the potential
  - Laplacian of the field

= Blanks With Package Content

+ #m(1) Free fall acceleration at sea level is approximately
  #blank(width: 2.4cm)[#qty("9.81", "m/s^2")] (unify content as the answer).

+ #m(1) The derivative $dv(, x) sin x$ equals #blank(width: 1.6cm)[$cos x$].
