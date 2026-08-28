# Walking Skeleton Delivery

## Your coding agent can finish every layer and still fail the first real click.

Make it prove one working product path before it earns the right to build the rest.

Walking Skeleton Delivery keeps coding agents from spending tokens, time, and code on an architecture that nobody has seen work.

```text
One real scenario
      ↓
One path across every required boundary
      ↓
Visible outcome + operational evidence
      ↓
Then expand, test, and harden
```

## The expensive failure mode

You ask an agent to add a capability. It creates interfaces, adapters, configuration, tests, docs, and edge-case handling. The pieces look finished.

Then you try the product.

The UI cannot reach the backend. The runtime reads a different contract. The "end-to-end" test never used a real identity. Four hours of polished work now need a rewrite.

Walking Skeleton Delivery changes the order of work so the first broken assumption appears while the implementation is still small.

## Why this exists

Tokscale has tracked 63.8B tokens across my coding-agent work. At that scale, bad execution order burns context, time, and rewrite cycles long before code quality becomes the main problem.

![dnplus Tokscale coding activity](https://tokscale.ai/api/embed/dnplus/svg?view=3d&theme=light&compact=1)

## Install

```bash
npx skills add dnplus/skills
```

## Use it

```text
Use Walking Skeleton Delivery to deliver this capability.
```

Or describe a new capability, rewrite, or cross-module migration. Compatible agents can select the skill automatically when the task matches.

## What the agent does differently

Say you ask for support for six providers.

Without the skill, an agent may build a provider framework, six adapters, a test matrix, and fallback behavior before one provider works in the product.

With the skill, the agent first chooses one provider and one real scenario:

```text
Real user
  → actual UI or public interface
  → application boundary
  → provider/runtime boundary
  → visible result
  → audit or correlation evidence
```

It advances that scenario checkpoint by checkpoint. After the path works, the agent extracts the demonstrated pattern, freezes the exercised contract, adds the remaining providers, runs the broader regression suite, and hardens real failure cases.

## The rule

> Do not scale implementation faster than evidence.

The skill treats a build, API-only check, seeded database, component test, or passing-test count as partial evidence. A product path becomes end-to-end only after the real entry point, execution, visible outcome, and required operational evidence have all been observed.

## The delivery sequence

```text
Prove → Stabilize → Scale → Harden
```

1. Choose one golden path with a real actor and observable outcome.
2. Fix only the first blocker on that path.
3. Reach the outcome through the real system boundaries.
4. Extract contracts and abstractions demonstrated by the working path.
5. Fan out to variants and batch verification.
6. Add recovery and edge cases based on real risks.

## Measure whether it saved you money

Compare these across similar tasks:

- time and tokens to the first green product path;
- tests written before that path worked;
- code discarded or rewritten after integration;
- checkpoints reached per implementation cycle.

The skill cannot make every task cheap. It makes waste visible before the agent multiplies it.

## License

MIT
