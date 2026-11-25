---
kg: v0.4
---

Open world (default): a fact that is not in the store prints `unknown`.

@import set
@add Scientist set.subset Person
@add newton set.member Scientist
@add newton name "Isaac Newton"
@add leibniz set.member Person
@print(newton set.member Person)
@print(leibniz name "Leibniz")
