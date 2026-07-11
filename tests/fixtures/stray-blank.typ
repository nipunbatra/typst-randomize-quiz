#import "/quizforge/lib.typ": make-exam, mcq, ans, blank
#make-exam(
  exam: (id: "t", sets: ("A",)),
  questions: (mcq("q-1", [oops #blank()], options: (ans[a], [b])),),
  sections: ((title: "S", filter: (type: "mcq")),),
)
