// Torture chamber for the markup parser: unicode, code blocks, tables inside
// options, nested enums, #list escape hatch, term lists, blanks inside styled
// text and math fractions, pinned+✓ combinations, float marks, tight ✓, #yes,
// multi-paragraph bodies. Must COMPILE and produce a consistent answer key.

#import "/quizforge/lib.typ": *

#show: quiz.with(
  id: "stress-markup",
  course: "QA 000: Stress Testing",
  title: "The Torture Quiz — नमूना 🎉",
  sets: ("A", "B"),
  answer-grid: true,
)

= Mixed Content

These instructions contain a list on purpose:
#list([lists in instructions are fine], [they are not options])

+ #m(2) तंत्रिका जाल में सक्रियण फलन की भूमिका क्या है? (Unicode + emoji 🎉 stress)
  - ✓ अरैखिकता (non-linearity) जोड़ना
  - वज़न घटाना
  - डेटा को क्रमबद्ध करना

+ #m(1) What does this Python snippet print?
  ```python
  x = [i * i for i in range(4)]
  print(x[-1])
  ```
  - ✓ `9`
  - `16`
  - `[0, 1, 4, 9]`

+ #m(2) Which table correctly shows XOR? (tables inside options)
  - ✓ #table(columns: 3, inset: 3pt, [a], [b], [out], [0], [0], [0], [0], [1], [1], [1], [0], [1], [1], [1], [0])
  - #table(columns: 3, inset: 3pt, [a], [b], [out], [0], [0], [1], [0], [1], [0], [1], [0], [0], [1], [1], [1])

+ #m(2) A training loop performs the steps:
  + forward pass
  + loss computation
  + backward pass

  Which step computes $partial L slash partial theta$? (nested enum + multi-paragraph body)
  - ✓ The backward pass
  - The forward pass
  - The loss computation

+ #m(1) Consider the properties #list([convex], [smooth]) — which hold for the
  MSE loss of linear regression? (the \#list escape hatch is not parsed as options)
  - ✓ Both
  - Only convexity
  - Neither

+ #m(1.5) / bias: systematic error. / variance: sensitivity to the sample.
  Which decreases when a decision tree is pruned? (term list + fractional marks)
  - ✓ variance
  - bias

+ #m(1) Tight checkmark and long options:
  - ✓Correct even though the ✓ touches the word, and this option is
    deliberately long enough to wrap across multiple lines so that hanging
    indentation after the option letter can be inspected in the output.
  - A wrong option that is also long enough to wrap onto at least two separate
    lines when typeset at the default width of an A4 exam paper.

+ #m(1) The \#yes marker instead of ✓:
  - #yes This one is correct
  - This one is not

+ #m(1) Both options pinned (shuffle becomes a no-op):
  - #pin-first ✓ Stays first
  - #pin Stays last

+ #m(2) #opts(shuffle: false, columns: 2) Fixed order, two columns:
  - I only
  - ✓ I and II
  - II and III
  - I, II and III

= Blanks in Odd Places

+ #m(2) Styled blank: the *#blank[bold answer]* sits inside strong text, and a
  math blank sits in a fraction: $x = 1 / #blank(width: 1.2cm)[$n$]$.

+ #m(1) Blank at the very start: #blank[Gradient descent] iteratively follows
  the negative gradient.

= Frozen Part #section(shuffle: false)

+ #m(3) First long question, always first.
  #answer(3cm)[Model answer with math $sum_i x_i$ and *bold*.]

+ #m(3) Second long question, always second.
  #answer(3cm, rubric: [All-or-nothing.])[Another model answer.]
