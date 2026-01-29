# Signal-Based REQUIRE_APPROVAL Implementation Plan

## Summary

Implement durable human-in-the-loop using Temporal signals and `workflow.wait_condition()`. Approval state stored in Temporal workflow history (not in-memory).

**Key:** Signal handlers registered dynamically, state shared between inbound/outbound interceptors, `wait_condition()` for durable waiting.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  DURABLE SIGNAL-BASED APPROVAL FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│  1. Workflow calls execute_activity()                                │
│  2. Outbound interceptor calls governance API → REQUIRE_APPROVAL    │
│  3. Outbound interceptor calls workflow.wait_condition()             │
│     → Workflow PAUSES (durable, no resources used)                  │
│  4. [External] Sends signal: openbox_approve(activity_id)           │
│  5. Signal handler (registered in inbound interceptor) updates state │
│  6. wait_condition() UNBLOCKS                                        │
│  7. Activity executes or workflow fails                              │
└─────────────────────────────────────────────────────────────────────┘

Key: State in workflow history. Survives worker restart.
```

## Signal Names

| Signal | Purpose |
|--------|---------|
| `openbox_approve` | Approve activity (arg: activity_id) |
| `openbox_reject` | Reject activity (arg: activity_id) |

## Implementation

### 1. `openbox/workflow_interceptor.py` - Register signals + connect outbound

The key is in the `_Inbound.init()` method which creates the outbound interceptor and registers signal handlers with **shared state**.

```python
from temporalio.worker import WorkflowOutboundInterceptor
from .workflow_outbound_interceptor import GovernanceWorkflowOutboundInterceptor

class GovernanceInterceptor(Interceptor):
    def __init__(self, api_url, api_key, span_processor=None, config=None):
        ...
        # Signal names (configurable)
        self.signal_approve = "openbox_approve"
        self.signal_reject = "openbox_reject"

    def workflow_interceptor_class(self, input):
        # Capture in closure
        api_url = self.api_url
        api_key = self.api_key
        config = self._config  # or however config is stored
        signal_approve = self.signal_approve
        signal_reject = self.signal_reject

        class _Inbound(WorkflowInboundInterceptor):
            def init(self, outbound: WorkflowOutboundInterceptor) -> WorkflowOutboundInterceptor:
                # ═══ SHARED STATE (durable - in workflow context) ═══
                approval_results: Dict[str, Dict[str, Any]] = {}

                # ═══ CREATE OUTBOUND INTERCEPTOR ═══
                governance_outbound = GovernanceWorkflowOutboundInterceptor(
                    next_interceptor=outbound,
                    api_url=api_url,
                    api_key=api_key,
                    config=config,
                    approval_results=approval_results,  # Pass shared state
                )

                # ═══ REGISTER SIGNAL HANDLERS ═══
                def _approve_handler(activity_id: str) -> None:
                    approval_results[activity_id] = {"verdict": "allow", "reason": None}

                def _reject_handler(activity_id: str, reason: str = None) -> None:
                    approval_results[activity_id] = {"verdict": "reject", "reason": reason}

                workflow.set_signal_handler(signal_approve, _approve_handler)
                workflow.set_signal_handler(signal_reject, _reject_handler)

                return governance_outbound

            async def execute_workflow(self, input):
                # ... existing WorkflowStarted/Completed/Failed logic ...
```

### 2. `openbox/workflow_outbound_interceptor.py` - Use shared state

Modify to accept and use the shared `approval_results` dict:

```python
class GovernanceWorkflowOutboundInterceptor(WorkflowOutboundInterceptor):
    def __init__(
        self,
        next_interceptor: WorkflowOutboundInterceptor,
        api_url: str,
        api_key: str,
        config,
        approval_results: Dict[str, Dict[str, Any]],  # NEW: shared state
    ):
        super().__init__(next_interceptor)
        self._api_url = api_url
        self._api_key = api_key
        self._config = config
        self._approval_results = approval_results  # Use shared state

    # REMOVE: self._approval_results = {} (line 50)
    # REMOVE: set_approval_result() method (lines 52-54)

    async def _start_activity_with_governance(self, input, activity_id):
        # ... governance pre-check ...

        if verdict == "require_approval":
            timeout_seconds = getattr(self._config, 'approval_timeout_seconds', 300.0)

            # REMOVE: polling activity start (lines 130-144)

            # Wait for approval signal (durable!)
            try:
                await workflow.wait_condition(
                    lambda: activity_id in self._approval_results,
                    timeout=timedelta(seconds=timeout_seconds),
                )
            except TimeoutError:
                _raise_governance_halt("Approval timeout")

            # Check result
            if activity_id in self._approval_results:
                result = self._approval_results[activity_id]
                if result["verdict"] == "allow":
                    return self.next.start_activity(input)
                else:
                    _raise_governance_halt(result["reason"] or "Approval rejected")
```

### 3. `openbox/worker.py` - Ensure outbound interceptor is used

Currently `GovernanceInterceptor` may not be creating the outbound chain. Verify/fix:

```python
# The workflow_interceptor_class() returns _Inbound which has init() method
# init() creates GovernanceWorkflowOutboundInterceptor
# This should work automatically if _Inbound.init() is implemented correctly
```

## How It Works (Durable)

### On First Execution:
1. `_Inbound.init()` creates `approval_results = {}` and outbound interceptor
2. Signal handlers registered via `workflow.set_signal_handler()`
3. Activity triggers REQUIRE_APPROVAL
4. `wait_condition(lambda: activity_id in approval_results)` pauses workflow
5. Workflow state: `approval_results = {}` (empty)

### When Signal Arrives:
6. External sends: `openbox_approve("1")`
7. Signal handler: `approval_results["1"] = {"verdict": "allow"}`
8. `wait_condition` unblocks (condition now true)
9. Activity proceeds

### On Worker Restart/Replay:
1. `_Inbound.init()` creates `approval_results = {}` (empty again)
2. Signal events replay from history
3. Signal handler populates: `approval_results["1"] = {"verdict": "allow"}`
4. `wait_condition` check: `"1" in approval_results` → True
5. Wait immediately unblocks (no re-waiting)

**This is durable because signal events are in workflow history!**

## External API

```bash
# Approve activity "1"
temporal workflow signal \
  --workflow-id=my-workflow \
  --name=openbox_approve \
  --input='"1"'

# Reject activity "1" with reason
temporal workflow signal \
  --workflow-id=my-workflow \
  --name=openbox_reject \
  --input='["1", "Policy violation"]'
```

Python:
```python
handle = client.get_workflow_handle(workflow_id)
await handle.signal("openbox_approve", "1")
```

## Implementation Order

1. Modify `openbox/workflow_interceptor.py`:
   - Add `init()` method to `_Inbound` class
   - Create shared `approval_results` dict
   - Create outbound interceptor with shared state
   - Register `openbox_approve`/`openbox_reject` signal handlers

2. Modify `openbox/workflow_outbound_interceptor.py`:
   - Accept `approval_results` in constructor
   - Remove `self._approval_results = {}` initialization
   - Remove `set_approval_result()` method
   - Remove polling activity start (lines 130-144)
   - Keep `wait_condition()` logic, use shared `approval_results`

3. Test end-to-end

## Verification

```bash
# 1. Start workflow that triggers REQUIRE_APPROVAL
# 2. Check Temporal UI - workflow is "Running" but paused at wait_condition
# 3. Send approval signal
temporal workflow signal --workflow-id=xxx --name=openbox_approve --input='"1"'
# 4. Workflow resumes and completes
```

## Critical Files

| File | Action | Key Changes |
|------|--------|-------------|
| `openbox/workflow_interceptor.py` | MODIFY | Add `init()` to `_Inbound`, register signal handlers |
| `openbox/workflow_outbound_interceptor.py` | MODIFY | Accept shared state, remove polling |

## Why This Is Durable

1. **Signal events are in workflow history** - replayed on restart
2. **`approval_results` dict is populated during replay** - signal handlers run
3. **`wait_condition` checks during replay** - finds approval immediately
4. **No in-memory state dependency** - span_processor not used for approval
