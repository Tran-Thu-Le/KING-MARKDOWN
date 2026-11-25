---
kg: v0.4
---

Schema check with k.else: every Person without a name gets an error fact.

@import set
@add Scientist set.subset Person
@add newton set.member Scientist
@add newton name "Isaac Newton"
@add leibniz set.member Person
@add w1 = var.x set.member Person
@add w2 = var.x name var.n
@add e = var.x error missing-name
@add r = w2 k.else e
@add w1 k.then r
@print(leibniz error missing-name)
@print(newton error missing-name)
