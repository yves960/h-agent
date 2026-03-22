# Task Planning

*"Don't surrender until it's right."* — Ekko

h-agent has built-in task planning module providing three capabilities: task decomposition, scheduled execution, and progress tracking.

---

## 1. Task Decomposition (decomposer)

### Feature Overview

Automatically decompose complex tasks into executable subtask trees:

```
Task "Refactor user module"
  ├─ T1: Analyze existing code structure
  ├─ T2: Design new architecture
  ├─ T3: Implement UserService
  ├─ T4: Write unit tests
  └─ T5: Update API documentation
```

### Core Components

```python
from h_agent.planner.decomposer import Task, TaskStatus, TaskTree
```

### Task Data Structure

```python
@dataclass
class Task:
    task_id: str              # Unique ID, format t-xxxxxxxx
    parent_id: Optional[str]   # Parent task ID (None for root task)
    
    # Task content
    title: str                # Short title
    description: str          # Detailed description
    instructions: str          # Specific instructions for Agent
    expected_output: str       # Expected output
    
    # Metadata
    status: TaskStatus        # PENDING/RUNNING/DONE/FAILED/BLOCKED/SKIPPED
    priority: int             # 0=normal, 1=high, 2=urgent
    tags: List[str]           # Tags
    
    # Assignment
    assigned_to: Optional[str]  # Agent name
    role_hint: Optional[str]    # Suggested assigned role
    
    # Execution
    result: Any               # Execution result
    error: Optional[str]      # Error message
    retry_count: int          # Current retry count
    max_retries: int          # Max retries (default 2)
    
    # Timestamps
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
```

### Task Tree Operations

```python
from h_agent.planner.decomposer import TaskTree, Task, TaskStatus

# Create task tree
tree = TaskTree()

# Add root task
root = tree.add_task(
    title="Refactor user module",
    description="Split monolith user module into independent microservices",
    instructions="Reference existing implementation in src/users/, design RESTful API",
    expected_output="New users-service code",
    priority=1,
    tags=["refactor", "backend"]
)

# Add subtask
t1 = tree.add_task(
    title="Analyze existing code",
    description="Understand current user module structure and dependencies",
    parent_id=root.task_id,
)
t2 = tree.add_task(
    title="Design new architecture",
    description="Design microservice architecture including API and data model",
    parent_id=root.task_id,
)

# Add sibling task (sequential task under same parent)
t3 = tree.add_task(
    title="Implement UserService",
    description="Implement core business logic",
    after_task_ids=[t2.task_id],  # Depends on t2
    parent_id=root.task_id,
)

# Set task status
tree.update_status(t1.task_id, TaskStatus.DONE)
tree.update_status(t2.task_id, TaskStatus.RUNNING)

# View task tree
tree.print_tree()
```

### Auto Decomposition

```python
from h_agent.planner.decomposer import auto_decompose

# Automatically decompose natural language task into subtasks
tasks = auto_decompose(
    task="Implement a blog system with user registration, article publishing, comment features",
    context="Using FastAPI + PostgreSQL",
    max_depth=2,
)
for t in tasks:
    print(f"{t.task_id}: {t.title}")
```

### Task Status Flow

```
PENDING → RUNNING → DONE
                ↘ FAILED → (retry) → RUNNING
                ↘ BLOCKED → (unblock) → PENDING
PENDING → SKIPPED (manual skip)
```

### Notes

- `task_id` is globally unique, format is `t-` + 8-digit hex string
- Parent task doesn't automatically complete when subtasks complete, needs manual marking
- Task status is saved in `~/.h-agent/planner/` directory

---

## 2. Task Scheduling (scheduler)

### Feature Overview

Concurrent task scheduler, executes tasks according to dependencies:

```
Scheduler features:
- Maintains pending execution queue
- Schedules by dependency order
- Controls concurrency (default 3)
- Auto retry on failure
- Progress callback notifications
- State persistence
```

### Basic Usage

```python
from h_agent.planner.scheduler import TaskScheduler, SchedulerConfig
from h_agent.planner.decomposer import Task, TaskStatus

config = SchedulerConfig(
    max_workers=3,         # Max concurrency
    task_timeout=300,     # Single task timeout (seconds)
    retry_delay=5,        # Retry interval (seconds)
    poll_interval=1.0,    # Queue poll interval
    save_interval=30.0,   # State save interval
)

scheduler = TaskScheduler(config=config)

# Define task execution function
def run_task(task: Task) -> str:
    if task.title == "Compile code":
        return "Compilation successful"
    elif task.title == "Run tests":
        return "All passed"
    return "Complete"

# Add tasks
scheduler.add_task(task1)
scheduler.add_task(task2)
scheduler.add_task(task3)

# Start scheduler (blocking)
scheduler.start()

# Get results
for task_id, result in scheduler.get_results().items():
    print(f"{task_id}: {result}")
```

### Non-blocking Scheduling

```python
# Start scheduler (non-blocking)
scheduler.start(blocking=False)

# Wait for all tasks to complete
scheduler.wait_for_completion(timeout=600)

# Check status
if scheduler.is_done():
    print("All tasks completed!")
else:
    pending = scheduler.get_pending()
    running = scheduler.get_running()
    print(f"Pending: {len(pending)}, Running: {len(running)}")
```

### Progress Callbacks

```python
from h_agent.planner.scheduler import SchedulerEvent

def on_event(event: SchedulerEvent, task: Task = None):
    if event == SchedulerEvent.TASK_STARTED:
        print(f"▶ Started: {task.title}")
    elif event == SchedulerEvent.TASK_COMPLETED:
        print(f"✓ Completed: {task.title}")
    elif event == SchedulerEvent.TASK_FAILED:
        print(f"✗ Failed: {task.title} - {task.error}")

scheduler.on(SchedulerEvent.TASK_STARTED, on_event)
scheduler.on(SchedulerEvent.TASK_COMPLETED, on_event)
scheduler.on(SchedulerEvent.TASK_FAILED, on_event)
```

### Scheduler Configuration Parameters

| Parameter | Default | Description |
|------|--------|------|
| `max_workers` | 3 | Max concurrent tasks |
| `task_timeout` | 300 seconds | Single task timeout |
| `retry_delay` | 5 seconds | Wait before retry |
| `poll_interval` | 1 second | Queue check interval |
| `save_interval` | 30 seconds | State persistence interval |

---

## 3. Progress Tracking (progress)

### Feature Overview

Real-time task progress percentage calculation, supports ETA estimation and milestone detection:

```python
from h_agent.planner.progress import ProgressTracker, Milestone
```

### Basic Usage

```python
tracker = ProgressTracker(scheduler=scheduler)

# Define milestones
tracker.define_milestone(
    name="Development Complete",
    task_ids=["t-abc12345", "t-def67890"],
    description="All feature development complete"
)
tracker.define_milestone(
    name="Launch",
    task_ids=["t-xyz11111"],
    description="System officially launched"
)

# Get progress
progress = tracker.get_progress()
print(f"Progress: {progress * 100:.1f}%")

# Get ETA
eta = tracker.get_eta()
if eta:
    print(f"Estimated completion: {eta}")

# Check milestones
milestone = tracker.check_milestone("Development Complete")
if milestone and milestone.reached:
    print(f"🎉 {milestone.name} reached!")
```

### Formatted Reports

```python
# Generate text report
report = tracker.generate_report()
print(report)

# Report example:
# Progress: 60.0%
# Time elapsed: 120s
# ETA: 80s
# Milestones: [✓] Development Complete [ ] Launch
# Current tasks:
#   ▶ Implement user authentication (RUNNING)
#   ○ Write API documentation (PENDING)
```

### Save Reports

```python
# Save to file
tracker.save_report("/path/to/report.json")

# Save progress snapshot
tracker.snapshot()  # Save to ~/.h-agent/planner/progress_report.json
```

---

## 4. Three-Way Collaboration

```
User inputs task
     ↓
decomposer.decompose()     ← Decompose task into tree
     ↓
scheduler.add_task()       ← Add to scheduling queue
     ↓
scheduler.start()          ← Execute concurrently by dependencies
     ↓
progress.track()           ← Track progress in real-time
     ↓
agent_loop calls tools       ← Actually execute work
     ↓
scheduler.on(EVENT)        ← Event callback updates progress
     ↓
progress.check_milestone()  ← Milestone detection
     ↓
Complete / Failed / Retry
```

---

## 5. Command Line Usage

```bash
# Scheduler state files
ls ~/.h-agent/planner/

# Scheduler state
cat ~/.h-agent/planner/scheduler_state.json

# Progress report
cat ~/.h-agent/planner/progress_report.json
```

---

## 6. Notes

- **Circular dependency detection**: Exception thrown if circular dependency detected during `add_task`
- **Timeout doesn't kill process**: Task marked as failed after timeout, but process not forcibly terminated
- **State persistence**: Scheduler state saved every 30 seconds, can recover after crash
- **Milestones are soft detection**: Milestone reached just checks related task status, doesn't trigger special behavior
- **Concurrency setting**: Too high concurrency may cause resource contention, recommended 3-5
