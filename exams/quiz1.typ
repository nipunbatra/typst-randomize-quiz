// Demo exam — this file IS the compile target:
//
//   typst compile exams/quiz1.typ set-A.pdf --root . --input set=A
//   typst compile exams/quiz1.typ key-B.pdf --root . --input set=B --input mode=key
//
// or build every set + keys + grading CSV in one go:
//
//   python3 scripts/build.py exams/quiz1.typ

#import "/quizforge/lib.typ": make-exam
#import "/questions/dl-mcq.typ": mcq-questions
#import "/questions/dl-fill.typ": fib-questions
#import "/questions/dl-subjective.typ": subj-questions

#make-exam(
  exam: (
    id: "dl-quiz-1", // seeds + output filenames derive from this — freeze once printed
    course: "ES 667: Deep Learning",
    title: "Quiz 1 — Neural Network Fundamentals",
    date: "2026-08-20",
    duration: "60 minutes",
    sets: ("A", "B", "C", "D"),
    answer-grid: true,
    instructions: (
      [Calculators are permitted; devices with network access are not.],
      [Answer subjective questions in the space provided below each question.],
    ),
  ),

  questions: mcq-questions + fib-questions + subj-questions,

  sections: (
    (
      title: "Multiple Choice",
      instructions: [Choose the single best answer unless a question says otherwise.],
      use: ("mcq-activation-statements",), // guaranteed to appear (rest sampled by pick)
      filter: (type: "mcq"),
      pick: 8, // 1 included + 7 sampled from the other 8 MCQs — same 8 in every set
    ),
    (
      title: "Fill in the Blanks",
      filter: (type: "fill_blank"),
    ),
    (
      title: "Short & Long Answers",
      use: ("subj-overfitting", "subj-cnn-vs-mlp", "subj-forward-backward", "subj-softmax-grad"),
      shuffle: false, // keep easy → hard order in every set
    ),
  ),
)
