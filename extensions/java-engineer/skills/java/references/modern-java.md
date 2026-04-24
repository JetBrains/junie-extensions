# Modern Java (17–21) — records, sealed, pattern matching pitfalls

Only the traps. Baseline syntax is assumed.

## Records

- **Not a JPA entity.** Records are `final` and have no no-arg constructor. `@Entity` compiles with Hibernate but breaks at runtime — entities need mutability and proxies. Use a record only for DTO / projection.
- **Jackson** needs `-parameters` on `javac` to deserialize records by component name (unless you add `@JsonCreator`/`@JsonProperty` on every component). Missing flag → silent `null` fields at runtime.
- **Adding/removing a component is a breaking change** for both `Serializable` on-wire format and any positional pattern match (`case Point(int x, int y)`).
- If a component is an array, default `equals`/`hashCode` is identity-based — wrap it (`List.of`) or override.

## Sealed types

- Subtypes must be `final`, `sealed`, or `non-sealed`. Forgetting the modifier is the #1 compile error.
- **Don't add `default`** to a switch over a sealed type — that defeats exhaustiveness, adding a new subtype becomes a silent bug instead of a compile error.

## Pattern matching `switch`

- **`null` is its own case.** Without `case null ->`, a null scrutinee throws NPE — it does **not** fall to `default`.
- Guards use `when`, not `&&` or `if`.
- Don't mix arrow (`->`) and colon (`:`) cases in the same switch — arrow is no-fall-through, colon falls through and needs `break`.

## Preview features

- `--enable-preview` must be passed to **both** `javac` and `java`. Otherwise IDE compiles, build fails.
- Preview APIs break binary-incompatibly across JDKs. Pin the JDK for preview-using code.
