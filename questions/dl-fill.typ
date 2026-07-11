// Fill-in-the-blank bank. Put one #blank() marker in the body per entry of
// `answers` (consumed in order). Answers may be strings or content (math!)
// — they are printed in the key and exported to the grading CSV.

#import "/quizforge/lib.typ": fib, blank

#let fib-questions = (
  fib(
    "fib-relu",
    marks: 1, topic: "activations", difficulty: "easy",
    answers: ("ReLU",),
    [The #blank() activation function is defined as $max(0, x)$.],
  ),

  fib(
    "fib-universal",
    marks: 1, topic: "theory", difficulty: "medium",
    answers: ("continuous",),
    [By the universal approximation theorem, an MLP with a single hidden layer
      and enough units can approximate any #blank() function on a compact
      domain to arbitrary accuracy.],
  ),

  fib(
    "fib-shapes",
    marks: 2, topic: "mlp", difficulty: "medium",
    answers: ($B$, $h$),
    blank-width: 1.8cm,
    [For a batch $X in RR^(B times d)$ and a linear layer with weights
      $W in RR^(h times d)$, the pre-activation $Z = X W^top$ has shape
      ( #blank() , #blank() ).],
  ),

  fib(
    "fib-weight-sharing",
    marks: 1, topic: "cnn", difficulty: "easy",
    answers: ("weight (parameter) sharing",),
    blank-width: 3.5cm,
    [Convolutional layers need far fewer parameters than fully connected layers
      because the same kernel is applied at every spatial location, a property
      known as #blank().],
  ),
)
