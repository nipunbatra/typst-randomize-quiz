#import "/quizforge/lib.typ": quiz
#show: quiz.with(
  id: "furniture-test",
  sets: ("A",),
  header: none,
  footer: info => align(center, text(8pt)[#info.exam.id — set #info.at("set") — #info.total marks — #info.mode]),
)
+ Does custom page furniture work?
  - ✓ Yes
  - No
