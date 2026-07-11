// Subject demo: algorithms — code blocks, a trace question, true/false,
// two-column options, a lower-bound proof.

#import "/quizforge/lib.typ": *

#show: quiz.with(
  id: "cs201-demo",
  course: "CS 201: Data Structures & Algorithms",
  title: "Quiz 1 — Complexity & Sorting",
  duration: "30 minutes",
  sets: ("A", "B"),
  answer-grid: true,
)

= Multiple Choice

+ #m(2) What is the worst-case running time of binary search on a sorted array
  of $n$ elements?
  - ✓ $Theta(log n)$
  - $Theta(n)$
  - $Theta(n log n)$
  - $Theta(1)$

+ #m(2) What does this function print for `n = 6`?
  ```python
  def f(n):
      c = 0
      while n > 1:
          n = n // 2
          c += 1
      print(c)
  ```
  - ✓ `2`
  - `3`
  - `6`
  - `1`
  #explain[$6 arrow.r 3 arrow.r 1$: two halvings.]

+ #m(1) Dijkstra's algorithm produces correct shortest paths on graphs with
  negative edge weights.
  - True
  - ✓ False
  #explain[A negative edge can improve an already-finalized vertex;
    use Bellman–Ford instead.]

+ #m(2) #opts(columns: 2) By the master theorem, $T(n) = 2 T(n\/2) + n$ solves to:
  - $Theta(n)$
  - ✓ $Theta(n log n)$
  - $Theta(n^2)$
  - $Theta(log n)$

= Fill in the Blanks

+ #m(1) A sorting algorithm is *stable* if it preserves the relative order of
  #blank(width: 2cm)[equal] keys.

+ #m(1) The average-case running time of quicksort with uniformly random
  pivots is $Theta(#blank(width: 2cm)[$n log n$])$.

= Short Answer

+ #m(4) Sketch the decision-tree argument that any comparison-based sorting
  algorithm needs $Omega(n log n)$ comparisons in the worst case.
  #answer(6cm, rubric: [+1 model: binary decision tree, leaves = permutations;
    +1 at least $n!$ leaves; +1 height $>= log_2 n!$; +1 Stirling
    → $Omega(n log n)$.])[
    Any comparison sort is a binary decision tree whose leaves are the $n!$
    input permutations. A binary tree with $n!$ leaves has height at least
    $log_2 n! = Theta(n log n)$ (Stirling), so some input forces that many
    comparisons.]
