#import "/quizforge/lib.typ": make-exam, mcq, ans
#make-exam(
  exam: (id: "t", sets: ("A",)),
  questions: (mcq("q-1", [x], options: (ans[a], [b])),),
  sections: ((title: "S", use: ("nope",)),),
)
