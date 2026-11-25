---
kg: v0.4
---

Standard `set` library (pure KIR; a file uses it only after `@import set`, i.e. `@add k.file k.import set`): membership through subset, subset transitivity, `set.equal` aliases.

@add set.m1 = var.x set.member var.A
@add set.m2 = var.A set.subset var.B
@add set.m3 = var.x set.member var.B
@add set.mr = set.m2 k.then set.m3
@add set.m1 k.then set.mr
@add set.t1 = var.A set.subset var.B
@add set.t2 = var.B set.subset var.C
@add set.t3 = var.A set.subset var.C
@add set.tr = set.t2 k.then set.t3
@add set.t1 k.then set.tr
@add set.e1 = var.l1 set.equal var.l2
@add set.e2 = var.l2 set.equal var.l1
@add set.e1 k.then set.e2
@add set.a2 = var.a var.l1 var.b
@add set.a3 = var.a var.l2 var.b
@add set.ar = set.a2 k.then set.a3
@add set.e1 k.then set.ar
