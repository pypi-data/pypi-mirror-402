# DcisionAI 3-Tier Solver Architecture

## Overview

This implementation provides a sophisticated 3-tier solver architecture that intelligently routes optimization problems based on template confidence scores. The system balances execution speed with flexibility, using fewer LLM calls for high-confidence matches and more LLM-driven analysis for novel problems.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SOLVER ROUTER                                   │
│                    (Automatic Tier Selection)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Template Confidence >= 0.7  │  0.6-0.7  │  < 0.6  │  No Template      │
│            ↓                 │     ↓     │    ↓    │       ↓           │
│         TIER 3               │  TIER 2   │ TIER 1  │    AD-HOC         │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│    TIER 3      │  │    TIER 2      │  │    TIER 1      │  │    AD-HOC      │
│ Template Direct│  │ Guided Review  │  │Guided Learning │  │ Full LLM       │
├────────────────┤  ├────────────────┤  ├────────────────┤  ├────────────────┤
│ 1 LLM Call     │  │ 2-3 LLM Calls  │  │ 3-4 LLM Calls  │  │ 4-6 LLM Calls  │
│ ~8-12 seconds  │  │ ~15-20 seconds │  │ ~15-25 seconds │  │ ~20-30 seconds │
│                │  │                │  │                │  │                │
│ Data Fitting   │  │ Data Fitting   │  │ Data Fitting   │  │ Analysis       │
│ ↓              │  │ ↓              │  │ ↓              │  │ ↓              │
│ Programmatic   │  │ PhD Review     │  │ Learn from     │  │ Selection      │
│ Execution      │  │ ↓              │  │ Examples       │  │ ↓              │
│                │  │ Execution      │  │ ↓              │  │ Model Gen      │
│                │  │                │  │ Execution      │  │ ↓              │
│                │  │                │  │                │  │ Execution      │
└────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘
```

## File Structure

```
solver_implementation/
├── schemas.py                 # Pydantic models for structured outputs
├── data_fitting_service.py    # Data-to-model fitting (shared by all tiers)
├── solver_selection_agent.py  # LLM-driven solver selection
├── execution_service.py       # Pyomo/DAME execution (programmatic)
├── tier3_solver.py           # Tier 3: Template Direct
├── tier2_solver.py           # Tier 2: Guided Review
├── tier1_solver.py           # Tier 1: Guided Learning
├── adhoc_solver.py           # Ad-hoc: Full LLM-Driven
├── solver_router.py          # Unified router
├── test_solvers.py           # Tests and examples
└── README.md                 # This file
```

## Tier Details

### Tier 3: Template Direct (≥0.7 confidence)
**The fastest path** - uses template's pre-built Pyomo model with intelligent data fitting.

- **LLM Calls**: 1 (data fitting only)
- **Time**: ~8-12 seconds
- **Use Case**: High-confidence template matches
- **Process**:
  1. Fit data_pack to template schema (1 LLM call)
  2. Apply transformations programmatically
  3. Execute Pyomo model programmatically
  4. Return results

### Tier 2: Guided Review (0.6-0.7 confidence)
**Balanced approach** - template guidance with PhD-level review.

- **LLM Calls**: 2-3
- **Time**: ~15-20 seconds
- **Use Case**: Medium-confidence matches needing validation
- **Process**:
  1. Fit data to template (LLM call 1)
  2. PhD reviewer validates/adjusts solver decision (LLM call 2)
  3. Execute with reviewed parameters
  4. Return results

### Tier 1: Guided Learning (<0.6 confidence)
**Learning approach** - uses template examples to learn patterns.

- **LLM Calls**: 3-4
- **Time**: ~15-25 seconds
- **Use Case**: Low-confidence matches with learning examples
- **Process**:
  1. Fit data if template available (LLM call 1)
  2. Learn solver selection from examples (LLM call 2)
  3. Tune parameters (combined with call 2 or separate)
  4. Execute optimization
  5. Return results

### Ad-hoc: Full LLM-Driven (no template)
**Maximum flexibility** - complete LLM-driven analysis and model generation.

- **LLM Calls**: 4-6
- **Time**: ~20-30 seconds
- **Use Case**: Novel problems, no template matches
- **Process**:
  1. Analyze problem and select solver (LLM call 1)
  2. Generate Pyomo model from scratch (LLM call 2)
  3. Validate model (optional LLM call 3)
  4. Execute optimization
  5. Return results

## Key Components

### Structured Outputs (Claude SDK)
All LLM calls use Claude's structured outputs feature for guaranteed schema compliance:

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    betas=["structured-outputs-2025-11-13"],
    messages=[...],
    output_format={
        "type": "json",
        "schema": DataFittingResult.model_json_schema()
    }
)
```

### Data Fitting Service
Shared across all tiers for intelligent data-to-model mapping:

```python
# 1 LLM call for semantic field matching
fitting_result = await data_fitter.fit_data_to_template(
    data_pack=data_pack,
    template_schema=template_schema,
    pyomo_model_code=pyomo_code
)

# Programmatic application (no LLM)
fitted_data = data_fitter.apply_fitting_result(data_pack, fitting_result)
```

### Solver Selection Agent
LLM-driven solver selection with role-based prompting:

```python
# PhD Reviewer (Tier 2)
reviewer = CombinedSolverDecisionAgent(llm_role="phd_reviewer")

# Student Learning (Tier 1)  
learner = CombinedSolverDecisionAgent(llm_role="student_learning")

# Standard Expert (Ad-hoc)
expert = CombinedSolverDecisionAgent(llm_role="standard_expert")
```

## Usage

### Using the Router (Recommended)
```python
from solver_router import solve_optimization

result = await solve_optimization(
    problem_description="Optimize my portfolio...",
    intent_context={
        'template_id': 'portfolio_rebalancing',
        'template_confidence': 0.85,
        'objectives': [...],
        'constraints': [...]
    },
    template={
        'pyomo_model_code': '...',
        'data_schema': {...},
        'solver_recommendation': 'scip'
    },
    data_pack={
        'records': [...],
        'metadata': {...}
    }
)

print(f"Tier: {result.tier}")
print(f"Status: {result.status}")
print(f"Objective: {result.objective_value}")
```

### Using a Specific Tier
```python
from tier3_solver import Tier3Solver, Tier3Input

solver = Tier3Solver()
result = await solver.solve(Tier3Input(
    problem_description="...",
    template_id="...",
    template_confidence=0.85,
    template_schema={...},
    pyomo_model_code="...",
    solver_recommendation="scip",
    data_pack={...}
))
```

### LangGraph Integration
```python
from solver_router import solver_router_node

# In your LangGraph workflow
workflow.add_node("solver", solver_router_node)
```

## Performance Comparison

| Tier | LLM Calls | Expected Time | Cost (Sonnet) |
|------|-----------|---------------|---------------|
| Tier 3 | 1 | ~8-12s | ~$0.01 |
| Tier 2 | 2-3 | ~15-20s | ~$0.02-0.03 |
| Tier 1 | 3-4 | ~15-25s | ~$0.03-0.04 |
| Ad-hoc | 4-6 | ~20-30s | ~$0.05-0.08 |

## Template Schema Requirements

For optimal data fitting, templates should include:

```python
template_schema = {
    'expected_fields': ['asset_id', 'weight', 'return', 'risk'],
    'field_descriptions': {
        'asset_id': 'Unique asset identifier',
        'weight': 'Portfolio weight (0.0-1.0)',
        'return': 'Expected annual return (decimal)',
        'risk': 'Asset volatility (decimal)'
    },
    'required_fields': ['asset_id', 'weight'],
    'parameters': {
        'budget': 'Total portfolio value',
        'max_risk': 'Maximum acceptable risk'
    }
}
```

## Error Handling

All tiers return structured output with error information:

```python
result = await solver.solve(input)

if result.status == "error":
    print(f"Error: {result.error}")
else:
    print(f"Objective: {result.objective_value}")
```

## Running Tests

```bash
cd solver_implementation
python test_solvers.py
```

## Dependencies

```
anthropic>=0.40.0
pydantic>=2.0
pyomo>=6.0
# Optional solvers:
# pip install highspy  # HiGHS
# apt install scip     # SCIP
```

## Key Design Decisions

1. **Structured Outputs**: All LLM calls use Claude SDK structured outputs for guaranteed schema compliance
2. **Combined Decisions**: Selection + tuning in single call reduces API latency
3. **Programmatic Execution**: Pyomo execution is never LLM-driven
4. **Role-Based Prompting**: Different LLM roles for different tiers
5. **Graceful Degradation**: Falls back to simpler solvers if preferred not available
