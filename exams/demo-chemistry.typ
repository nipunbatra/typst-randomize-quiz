// Subject demo: general chemistry — molecular formulas, a two-blank balancing
// question, multi-select, periodic trends.

#import "/quizforge/lib.typ": *

#show: quiz.with(
  id: "ch101-demo",
  course: "CH 101: General Chemistry",
  title: "Quiz 3 — Stoichiometry & Periodicity",
  duration: "30 minutes",
  sets: ("A", "B"),
  instructions: ([Answer Part C in your answer booklet, not on this paper.],),
)

= Multiple Choice

+ #m(2) What is the oxidation state of manganese in KMnO#sub[4]?
  - ✓ $+7$
  - $+2$
  - $+4$
  - $-1$
  #explain[K is $+1$ and each O is $-2$: $1 + x - 8 = 0$, so $x = +7$.]

+ #m(2) Which of the following are strong acids in water?
  - ✓ HCl
  - ✓ HNO#sub[3]
  - CH#sub[3]COOH
  - NH#sub[3]
  #explain[Acetic acid is weak; ammonia is a base.]

+ #m(2) Among the period-3 elements Na, Mg, Al and Si, which has the *largest*
  atomic radius?
  - ✓ Na
  - Mg
  - Al
  - Si
  #explain[Radius decreases across a period as nuclear charge grows.]

= Fill in the Blanks

+ #m(2) Balance: #blank(width: 1.2cm)[2] H#sub[2] + O#sub[2] $arrow.r$
  #blank(width: 1.2cm)[2] H#sub[2]O.

+ #m(1) One mole contains $6.022 times 10^(#blank(width: 1.2cm)[$23$])$
  elementary entities.

= Short Answer

+ #m(3) The Haber process $N_2 + 3 H_2 arrows.rl 2 N H_3$ is exothermic.
  Using Le Chatelier's principle, predict how (i) raising the temperature and
  (ii) raising the pressure each shift the equilibrium, with one-line reasons.
  #answer(none, rubric: [+1.5 temperature: shifts left (heat is a product);
    +1.5 pressure: shifts right (4 gas moles → 2).])[
    (i) Heating shifts the equilibrium left — the reverse (endothermic)
    direction absorbs the added heat. (ii) Compression shifts it right, toward
    fewer moles of gas (4 → 2), reducing pressure.]
