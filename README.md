# Walking Skeleton Delivery

**Stop paying for code before you know the product path works.**

Walking Skeleton Delivery reduces coding-agent token usage, implementation time, and rework by proving one complete, observable path across the real system before expanding variants, abstractions, tests, and edge cases.

The governing principle is simple:

> Do not scale implementation faster than evidence.

## What it changes

Instead of implementing broad horizontal layers and discovering integration mistakes late, the skill keeps the agent on one golden path:

```text
Define the real outcome
-> Prove one thin end-to-end path
-> Stabilize demonstrated boundaries
-> Expand supported variants
-> Batch verify
-> Harden real exceptions
```

This targets execution waste upstream of linting, refactoring, and output cleanup.

## Install with GitHub CLI

```bash
gh skill install dnplus/walking-skeleton-delivery walking-skeleton-delivery --agent codex --scope user
```

The repository is currently private, so installation requires GitHub access to it.

## Use

Invoke the skill explicitly:

```text
$walking-skeleton-delivery deliver this capability
```

Codex can also select it automatically for a new product capability, rewrite, or cross-module migration that should be delivered through one thin observable path.

## License

MIT
