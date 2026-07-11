// Demo of the plain-markup front-end: this file is an ordinary Typst document.
// Compiled as-is it renders the ANSWER KEY (✓ marks visible — the master IS
// the key). For randomized student papers / the full build:
//
//   typst compile exams/quiz2.typ set-B.pdf --root . --input set=B --input mode=exam
//   python3 scripts/build.py exams/quiz2.typ

#import "/quizforge/lib.typ": *

#show: quiz.with(
  id: "dl-quiz-2",
  course: "ES 667: Deep Learning",
  title: "Quiz 2 — Optimization & Regularization",
  date: "2026-09-17",
  duration: "45 minutes",
  sets: ("A", "B", "C", "D"),
  answer-grid: true,
  instructions: ([Calculators are permitted; devices with network access are not.],),
)

= Multiple Choice

Choose the single best answer unless a question says otherwise.

+ #m(2) Classical SGD with momentum uses which update for the velocity $v$?
  - ✓ $v arrow.l beta v + nabla_theta L$, then $theta arrow.l theta - eta v$
  - $v arrow.l nabla_theta L - beta v$, then $theta arrow.l theta - eta v$
  - $v arrow.l beta v - theta$, then $theta arrow.l theta - eta nabla_theta L$
  - $v arrow.l v + beta nabla_theta L$, then $theta arrow.l theta - eta \/ v$

+ #m(2) Adding an L2 penalty $lambda norm(theta)_2^2$ to the loss is equivalent
  to placing which prior on the weights (MAP view)?
  - ✓ Gaussian
  - Laplace
  - Uniform
  - None of the above
  #explain[The Laplace prior corresponds to L1; a zero-mean Gaussian prior
    yields the L2 penalty.]

+ #m(2) Which of the following reduce overfitting?
  - ✓ Dropout
  - ✓ Weight decay
  - Increasing model capacity
  - Removing data augmentation

+ #m(2) #qid("lr-too-high") If the learning rate is far too high, the training
  loss typically:
  - ✓ Diverges or oscillates wildly
  - Decreases smoothly but slowly
  - Reaches zero in one step
  - Is unaffected — learning rate only changes memory usage

= Fill in the Blanks

+ #m(1) Halting training when the validation loss stops improving is called
  #blank(width: 3cm)[early stopping].

+ #m(2) The gradient of the L2 penalty $lambda norm(theta)_2^2$ with respect to
  $theta$ is #blank[$2 lambda theta$], which is why L2 regularization is also
  called weight #blank(width: 2cm)[decay].

= Long Answers #section(shuffle: false)

Answer in the space provided. Show your working.

+ #m(4) Adam divides the update by $sqrt(hat(v)) + epsilon$, where $hat(v)$ is a
  bias-corrected second-moment estimate. Explain (i) what problem this division
  solves and (ii) why the bias correction is needed early in training.
  #answer(6cm, rubric: [+2 per-parameter scaling / poorly conditioned gradients;
    +2 moments initialized at zero are biased toward zero for small $t$.])[
    (i) It adapts the step size per parameter: directions with persistently
    large gradients get smaller steps, flat directions larger ones.
    (ii) $v$ is initialized at 0 and updated as an EMA, so early estimates are
    biased toward 0; dividing by $1 - beta_2^t$ corrects this.]

+ #m(4) Sketch the typical training-loss vs. validation-loss curves for an
  overfitting run, mark where early stopping should trigger, and justify.
  #answer(7cm)[Training loss decreases monotonically; validation loss falls,
    then rises. Early stopping triggers at the validation minimum — beyond it
    the model fits noise, increasing generalization error.]
