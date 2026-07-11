#import "/quizforge/lib.typ": mcq, ans
#let q = mcq("huge", [Pick one of 27?],
  options: (ans[right],) + range(26).map(i => [wrong #i]))
