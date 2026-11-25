---
kg: v0.4
---

# Open world: Kleene three-valued logic

In an open world (the default) the store may be incomplete: a statement that is not in the store is **unknown**.
`and`, `or`, `not` follow Kleene logic with false < unknown < true: and = the smaller, or = the larger, not swaps true and false (not unknown = unknown).

@import set
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

## Excluded middle does not hold: q or not q is unknown when q is unknown

@print(leibniz name "Leibniz" or not leibniz name "Leibniz")

## Named compound statements (pure KIR)

@add has-name = leibniz name "Leibniz"
@add c k.subject k.not
@add c k.link k.of
@add c k.object has-name
@print(c)
