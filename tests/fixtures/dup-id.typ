#import "/quizforge/lib.typ": make-exam, mcq, ans
#let q = mcq("q-1", [x], options: (ans[a], [b]))
#make-exam(
  exam: (id: "t", sets: ("A",)),
  questions: (q, q),
  sections: ((title: "S", filter: (type: "mcq")),),
)
