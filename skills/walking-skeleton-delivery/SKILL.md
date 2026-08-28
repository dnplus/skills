---
name: walking-skeleton-delivery
description: Deliver a new product capability, rewrite, or cross-module migration as one thin observable path across its real system boundaries before extracting abstractions, freezing contracts, expanding variants, or hardening exceptions. Do not use for read-only review, an isolated small fix, or an explicitly test-only task.
license: MIT
---

# Walking Skeleton Delivery

Use a **walking skeleton** as the unit of delivery: the thinnest implementation that crosses every boundary required to produce a real product outcome. Optimize first for learning whether the product path and boundaries are correct, then for breadth and hardening.

## 1. Choose the skeleton's golden path

Before broad implementation, state one concrete scenario with:

- actor and real identity;
- entry point, normally the actual UI or public interface;
- minimum prerequisite state;
- execution path across the required components;
- user-visible outcome;
- operational evidence such as activity, audit, correlation, or applied revision when the product requires it.

Choose one tenant, provider, resource type, or equivalent representative variant. This scenario is the skeleton's first **golden path**, not the delivery method itself. The skeleton is complete only when the real path produces its observable outcome. A build, script, seeded database, API-only check, component test, or test count is narrower evidence.

## 2. Advance checkpoint by checkpoint

Trace the scenario from its entry point to its outcome. At each checkpoint:

1. Exercise the path using the closest available real interaction.
2. Identify the first blocking assumption or missing seam.
3. Make the smallest coherent change that advances this same scenario.
4. Re-run from the nearest trustworthy checkpoint, periodically re-running from the real entry point.
5. Record the new observed boundary before moving forward.

Keep one mutating lane on this path. Treat legacy implementations and documents as evidence, not authority, when the current product scenario intentionally changes the interface or model.

Early tests are **tactical**: add only the checks needed to advance safely or preserve a defect just found on the golden path. Prefer one high-information check over broad local coverage. Report progress by product checkpoint and evidence, not by modules, lines, or passing-test totals.

## 3. Stabilize only after the path is green

Once the first real path works, proceed in this order:

1. **Pattern extraction** — identify responsibilities and repetition demonstrated by the working implementation.
2. **Contract freeze** — formalize only the seams exercised by the path, including ownership, lifecycle, failure semantics, and observable outputs.
3. **Path fan-out** — add the next providers, resource types, roles, or variants using the established path.
4. **Batch regression** — expand contract, integration, and product checks across the supported matrix.
5. **Exception hardening** — add edge cases, recovery, retries, malformed input, partial failure, and operational safeguards based on real risks.

Abstract after the first path reveals the boundary; prefer seeing a second concrete use before extracting a configurable framework. When a later path disproves the first abstraction, fix the owning boundary rather than adding a parallel compatibility model.

## Scope guard

Pause adjacent capabilities, speculative framework work, exhaustive exception matrices, and compatibility bridges that do not advance the current scenario. A missing decision should stop the path only when different answers materially change the product behavior or persistent model; otherwise use the smallest reversible assumption and expose it in the progress update.

## Progress format

Keep updates compact and evidence-based:

```text
Walking skeleton: <entry point -> system boundaries -> observable outcome>
Golden path: <actor -> action -> outcome>
Current checkpoint: <last boundary reached>
Observed evidence: <what actually worked>
Current blocker: <first broken assumption>
Next smallest action: <one change that advances the path>
```

Do not call the capability end-to-end until the real actor, entry point, execution, visible outcome, and required operational evidence have all been observed. After completion, optionally compare time to first green path, tests written before it, rework, checkpoint throughput, and discarded work to evaluate whether the delivery loop improved.
