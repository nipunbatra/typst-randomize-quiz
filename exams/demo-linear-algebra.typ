// Subject demo: linear algebra — matrices via mat(), multi-select on
// invertibility, an eigenvalue proof with model answer.

#import "/quizforge/lib.typ": *

#show: quiz.with(
  id: "ma102-demo",
  course: "MA 102: Linear Algebra",
  title: "Quiz 2 — Determinants & Eigenvalues",
  duration: "30 minutes",
  sets: ("A", "B"),
)

= Multiple Choice

+ #m(2) Compute $det mat(2, 1; 3, 4)$.
  - ✓ $5$
  - $11$
  - $-5$
  - $8$
  #explain[$2 dot 4 - 1 dot 3 = 5$.]

+ #m(2) What is the rank of the $3 times 3$ matrix of all ones,
  $mat(1, 1, 1; 1, 1, 1; 1, 1, 1)$?
  - ✓ $1$
  - $0$
  - $2$
  - $3$
  #explain[Every row is the same nonzero vector.]

+ #m(2) For a square real matrix $A$, which conditions are *equivalent* to
  invertibility?
  - ✓ $det A != 0$
  - ✓ $A$ has full rank
  - $A$ is symmetric
  - $A$ is diagonalizable
  #explain[Symmetry and diagonalizability are neither necessary nor
    sufficient: $mat(0, 0; 0, 0)$ is symmetric and diagonalizable but singular.]

= Fill in the Blanks

+ #m(1) A nonzero vector $v$ is an eigenvector of $A$ when
  $A v = #blank(width: 1.4cm)[$lambda$] thin v$ for some scalar.

+ #m(1) For square matrices, $det(A B) = det(A) dot$
  #blank(width: 1.8cm)[$det(B)$].

= Short Answer

+ #m(4) Let $lambda$ be an eigenvalue of $A$ with eigenvector $v$. Show that
  $lambda^2$ is an eigenvalue of $A^2$, and state the corresponding
  eigenvector. Then give a $2 times 2$ example where $A^2$ has an eigenvalue
  that $A$ does #emph[not] have... is that possible if we only square
  eigenvalues? Justify briefly.
  #answer(7cm, rubric: [+2 the computation $A^2 v = lambda^2 v$; +1 eigenvector
    is the same $v$; +1 justification that eigenvalues of $A^2$ are exactly
    squares of eigenvalues of $A$ (over $CC$), so no new ones appear.])[
    $A^2 v = A(A v) = A(lambda v) = lambda (A v) = lambda^2 v$, so $lambda^2$
    is an eigenvalue with the *same* eigenvector $v$. Over $CC$ every
    eigenvalue of $A^2$ is the square of an eigenvalue of $A$ (triangularize),
    so squaring cannot create eigenvalues unrelated to those of $A$.]
