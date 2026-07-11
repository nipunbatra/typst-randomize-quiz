// Scale stress: 122 code-generated questions, pick 100, float marks, topic and
// difficulty cycling, a 26-option question (the supported maximum), and a
// 2-option true/false. Exercises sampling, the answer-grid chunking, and
// compile performance on a large paper.

#import "/quizforge/lib.typ": *

#let bulk = range(120).map(i => mcq(
  "gen-" + str(i),
  [Auto-generated question #str(i): what is $#str(i) + 1$?],
  options: (
    ans[#str(i + 1)],
    [#str(i)],
    [#str(i + 2)],
    [#str(2 * i + 3)],
  ),
  marks: 1 + calc.rem(i, 3) * 0.5,
  topic: "topic-" + str(calc.rem(i, 5)),
  difficulty: ("easy", "medium", "hard").at(calc.rem(i, 3)),
))

#let extras = (
  mcq(
    "max-options",
    [Which letter is the 26th? (26 options — the supported maximum)],
    options: range(25).map(i => [Letter #str(i + 1)]) + (ans(fixed: "last")[Letter 26],),
    marks: 1,
    topic: "topic-0",
  ),
  mcq(
    "true-false",
    [Two options is the minimum.],
    options: (ans[True], [False]),
    marks: 0.5,
    topic: "topic-1",
  ),
)

#make-exam(
  exam: (
    id: "stress-bank",
    course: "QA 000: Stress Testing",
    title: "Bulk Generation Stress",
    sets: ("A", "B"),
    answer-grid: true,
  ),
  questions: bulk + extras,
  sections: (
    (
      title: "Bulk",
      use: ("max-options", "true-false"),
      filter: (type: "mcq"),
      pick: 100,
    ),
  ),
)
