// RNG uniformity harness: shuffle 8 items under 400 distinct seeds and tally
// how often each item lands at each position. Queried by test_stress.py,
// which checks every cell of the position×item matrix stays near uniform.

#import "/quizforge/src/rng.typ": shuffle, fnv1a

#let n = 8
#let trials = 400

#let counts = {
  let c = ()
  for _ in range(n) { c.push((0,) * n) }
  for t in range(trials) {
    let p = shuffle(range(n), "dist-test|" + str(t))
    for (pos, item) in p.enumerate() {
      c.at(pos).at(item) += 1
    }
  }
  c
}

#metadata((
  n: n,
  trials: trials,
  counts: counts,
  hash-regression: fnv1a("quizforge"), // pins the hash function itself
)) <dist>
