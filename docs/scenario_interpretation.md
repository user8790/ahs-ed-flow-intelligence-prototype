# Scenario Interpretation

Scenario and simulation outputs must always include deterministic interpretation.

Each output should explain:

- what changed
- why it changed
- confidence
- what improved
- what worsened
- where the bottleneck moved
- operational watch-points
- operational levers to consider
- internal data needed to validate or refute
- limitations
- five-line capacity huddle brief

AI/model calls may polish wording only when approved and configured. They must not be the source of numerical results.

Current implementation:

- `ed_flow_intelligence.advanced_scenarios`
- `ed_flow_intelligence.simulation_vnext`
- `ed_flow_intelligence.operational_intelligence`
- kernel wrappers under `packages/ed_flow_kernel/ed_flow_kernel/simulation`
