// MCQ bank — Deep Learning fundamentals.
//
// Each question is mcq(id, [body], options: (...)). Options are plain content;
// mark the correct one with ans[...]. Pin an option with ans(fixed: "last")
// or opt(fixed: "last") — e.g. for "None of the above".

#import "/quizforge/lib.typ": mcq, opt, ans

#let mcq-questions = (
  mcq(
    "mcq-sigmoid-saturation",
    marks: 2, topic: "activations", difficulty: "medium",
    [Why do deep networks with sigmoid activations in every layer suffer from
      vanishing gradients?],
    options: (
      ans[The sigmoid derivative is at most $1\/4$, so products of many such factors shrink toward zero.],
      [The sigmoid output is always positive, so gradients cannot change sign.],
      [Sigmoid units have no learnable parameters.],
      [The sigmoid function is not differentiable at $x = 0$.],
    ),
    explanation: [$sigma'(x) = sigma(x)(1 - sigma(x)) <= 1\/4$; backprop multiplies
      one such factor per layer, so the gradient magnitude decays exponentially
      with depth.],
  ),

  mcq(
    "mcq-conv-params",
    marks: 2, topic: "cnn", difficulty: "medium",
    [A convolutional layer has kernel size $3 times 3$, 16 input channels,
      32 output channels, and a bias per output channel. How many learnable
      parameters does it have?],
    options: (
      ans[4640],
      [4608],
      [1184],
      [18464],
    ),
    explanation: [$3 dot 3 dot 16 dot 32 + 32 = 4608 + 32 = 4640$.],
  ),

  mcq(
    "mcq-backprop-mode",
    marks: 2, topic: "backprop", difficulty: "easy",
    [Backpropagation is a special case of which technique?],
    options: (
      ans[Reverse-mode automatic differentiation],
      [Forward-mode automatic differentiation],
      [Numerical differentiation via finite differences],
      [Symbolic differentiation of a closed-form expression],
    ),
  ),

  mcq(
    "mcq-dropout-test",
    marks: 2, topic: "regularization", difficulty: "easy",
    [A network is trained with _inverted_ dropout (activations scaled by $1\/p$
      during training, where $p$ is the keep probability). What must be done at
      test time?],
    options: (
      ans[Nothing — the network is used as-is.],
      [Multiply each activation by $p$.],
      [Divide each weight by $p$.],
      [Keep dropping neurons, but with a smaller drop probability.],
    ),
    explanation: [Inverted dropout moves the $1\/p$ correction into training, so
      expected activations already match at test time.],
  ),

  mcq(
    "mcq-batchnorm-inference",
    marks: 2, topic: "normalization", difficulty: "easy",
    [At inference time, batch normalization normalizes activations using which
      statistics?],
    options: (
      ans[Running estimates of mean and variance accumulated during training],
      [The mean and variance of the current test batch],
      [Statistics recomputed over the full training set at every forward pass],
      [No statistics — only the learned scale $gamma$ and shift $beta$ are applied],
    ),
  ),

  mcq(
    "mcq-softmax-ce-grad",
    marks: 2, topic: "backprop", difficulty: "hard",
    [For a softmax output $p = "softmax"(z)$ with one-hot target $y$ and
      cross-entropy loss $L = -sum_k y_k log p_k$, the gradient
      $(partial L)\/(partial z)$ equals:],
    options: (
      ans[$p - y$],
      [$y - p$],
      [$p (1 - p)$],
      [$-y \/ p$],
    ),
  ),

  mcq(
    "mcq-adaptive-optimizers",
    marks: 2, topic: "optimization", difficulty: "medium",
    multiple: true,
    [Which of the following optimizers maintain a per-parameter adaptive
      learning rate?],
    options: (
      ans[Adam],
      ans[RMSProp],
      [Vanilla SGD],
      [SGD with (classical) momentum],
    ),
    explanation: [Adam and RMSProp divide by a running estimate of per-parameter
      squared gradients; SGD variants use one global learning rate.],
  ),

  mcq(
    "mcq-conv-output",
    marks: 2, topic: "cnn", difficulty: "medium",
    [A $32 times 32$ input passes through a convolutional layer with kernel
      size 5, stride 1, and no padding. What is the spatial size of the output?],
    options: (
      [$30 times 30$],
      [$32 times 32$],
      [$27 times 27$],
      ans(fixed: "last")[None of the above], // pinned: never shuffled away from the end
    ),
    explanation: [$(32 - 5)\/1 + 1 = 28$, so the output is $28 times 28$ — not listed.],
  ),

  mcq(
    "mcq-activation-statements",
    marks: 2, topic: "activations", difficulty: "medium",
    shuffle: false, // options form a progression; shuffling would garble them
    columns: 2,
    [Consider the statements:
      #block(inset: (left: 1em, y: 2pt))[
        I. ReLU is not differentiable at $x = 0$. \
        II. tanh outputs lie in $(-1, 1)$. \
        III. Sigmoid outputs can be negative.
      ]
      Which statements are true?],
    options: (
      [I only],
      ans[I and II],
      [II and III],
      [I, II and III],
    ),
  ),
)
