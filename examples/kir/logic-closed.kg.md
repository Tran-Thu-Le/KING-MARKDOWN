---
kg: v0.4
---

# Closed world: Boolean logic

In a closed world the store is complete: a statement that is not in the store is **false**.
`and`, `or`, `not` follow ordinary two-valued (Boolean) logic.

@import set
@world closed
@add Scientist set.subset Person
@add newton set.member Scientist
@add newton name "Isaac Newton"
@add leibniz set.member Person

## Single statements

@print(newton set.member Person)
@print(leibniz name "Leibniz")

## and / or / not

@print(newton set.member Person and leibniz name "Leibniz")
@print(newton set.member Person or leibniz name "Leibniz")
@print(not leibniz name "Leibniz")

## Excluded middle holds: q or not q is always true

@print(leibniz name "Leibniz" or not leibniz name "Leibniz")

## Named compound statements (pure KIR)

@add has-name = leibniz name "Leibniz"
@add c k.subject k.not
@add c k.link k.of
@add c k.object has-name
@print(c)
