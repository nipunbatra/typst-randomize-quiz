#import "/quizforge/lib.typ": make-exam, fib, blank
#make-exam(
  exam: (id: "t", sets: ("A",)),
  questions: (fib("q-1", [only one #blank() here], answers: ("a", "b")),),
  sections: ((title: "S", filter: (type: "fill_blank")),),
)
