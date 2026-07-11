// Subjective bank. `answer-space` is the vertical space printed on the student
// paper; `model-answer` and `rubric` appear only in the answer key.

#import "/quizforge/lib.typ": subj

#let subj-questions = (
  subj(
    "subj-softmax-grad",
    marks: 5, topic: "backprop", difficulty: "hard",
    answer-space: 8cm,
    [Derive the gradient of the cross-entropy loss with respect to the logits
      when the output layer is a softmax. That is, for $p = "softmax"(z)$,
      one-hot target $y$, and $L = -sum_k y_k log p_k$, show that
      $(partial L)\/(partial z_j) = p_j - y_j$.],
    model-answer: [Write $L = -z_c + log sum_k e^(z_k)$ where $c$ is the true
      class. Then $(partial L)\/(partial z_j) = -bb(1)[j = c] + e^(z_j) \/ sum_k e^(z_k)
      = p_j - y_j$.],
    rubric: [+1 correct setup of softmax and cross-entropy; +2 log-sum-exp
      simplification or correct case split ($j = c$ vs. $j != c$); +1 algebra;
      +1 final form $p - y$.],
  ),

  subj(
    "subj-overfitting",
    marks: 4, topic: "generalization", difficulty: "easy",
    answer-space: 6cm,
    [Define overfitting and underfitting in terms of training and validation
      error. Name two techniques to reduce overfitting in deep networks and
      briefly explain why each works.],
    model-answer: [Overfitting: low training error, high validation error (high
      variance). Underfitting: both errors high (high bias). Mitigations include
      dropout (ensemble effect / prevents co-adaptation), weight decay
      (penalizes complexity), early stopping, data augmentation (enlarges
      effective data).],
    rubric: [+1 each for correct definitions; +1 per valid technique with a
      correct one-line justification (max 2).],
  ),

  subj(
    "subj-forward-backward",
    marks: 6, topic: "backprop", difficulty: "medium",
    answer-space: 10cm,
    [Consider the scalar network $a = w_1 x$, $h = "ReLU"(a)$, $hat(y) = w_2 h$,
      with squared loss $L = 1/2 (hat(y) - t)^2$. For $x = 2$, $w_1 = 0.5$,
      $w_2 = -1$, $t = 1$:

      + Compute the forward pass ($a$, $h$, $hat(y)$, $L$).
      + Compute $(partial L)\/(partial w_2)$ and $(partial L)\/(partial w_1)$ by
        backpropagation, showing each intermediate gradient.],
    model-answer: [Forward: $a = 1$, $h = 1$, $hat(y) = -1$,
      $L = 1/2 (-1 - 1)^2 = 2$. Backward:
      $(partial L)\/(partial hat(y)) = hat(y) - t = -2$;
      $(partial L)\/(partial w_2) = -2 dot h = -2$;
      $(partial L)\/(partial h) = w_2 dot (-2) = 2$; ReLU is active at $a = 1$,
      so $(partial L)\/(partial a) = 2$;
      $(partial L)\/(partial w_1) = 2 dot x = 4$.],
    rubric: [+2 forward pass (0.5 each); +1 loss gradient; +1 $w_2$ gradient;
      +1 ReLU gating; +1 $w_1$ gradient.],
  ),

  subj(
    "subj-cnn-vs-mlp",
    marks: 4, topic: "cnn", difficulty: "medium",
    answer-space: 6cm,
    [Give two structural reasons why convolutional networks outperform fully
      connected networks on images, and illustrate one of them with a rough
      parameter count for a $224 times 224$ RGB input.],
    model-answer: [(i) Local connectivity and weight sharing: parameters are
      independent of image size — e.g. a first FC layer to 1000 units needs
      $224 dot 224 dot 3 dot 1000 approx 1.5 times 10^8$ weights, while a
      $3 times 3$ conv with 64 filters needs $3 dot 3 dot 3 dot 64 + 64 = 1792$.
      (ii) Translation equivariance: features detected regardless of position,
      matching image statistics and improving generalization.],
    rubric: [+1.5 per structural reason correctly explained; +1 plausible
      parameter comparison.],
  ),
)
