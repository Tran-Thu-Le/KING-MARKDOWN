---
kg: v0.4
---
There are two worlds
Closed world: a fact that is not in the store prints `false`.

@import set
@world closed
@add Scientist set.subset Person
@add newton set.member Scientist
@add newton name "Isaac Newton"
@add leibniz set.member Person
@print(newton set.member Person)
@print(newton name "Isaac Newton")
@print(leibniz name "Leibniz")
