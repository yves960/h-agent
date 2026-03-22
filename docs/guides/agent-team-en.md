# Agent Team Guide

Multi-agent collaboration system that allows different agents to work together.

## Quick Start

```python
from h_agent.team.team import AgentTeam, AgentRole
from h_agent.team.protocol import get_zoo_animal

# Create team
team = AgentTeam("my-project")

# Register local handler
def planner_handler(msg):
    return TaskResult(success=True, content="Task planned")

team.register("planner", AgentRole.PLANNER, planner_handler)

# Register external adapter
team.register_adapter("coder", AgentRole.CODER, "opencode", {"agent": "code"})
team.register_adapter("reviewer", AgentRole.REVIEWER, "claude")

# Use zoo animals
team.register_zoo_animal("xueqiu")  # Automatically select RESEARCHER role
team.register_zoo_animal("liuliu", AgentRole.CODER)  # Custom role
```

## Team Roles

| Role | Description | Default Animal |
|------|------|----------|
| PLANNER | Task planning and decomposition | heibai |
| CODER | Code implementation | liuliu |
| REVIEWER | Code review | xiaohuang |
| DEVOPS | Deployment and operations | xiaozhu |
| RESEARCHER | Research and analysis | xueqiu |

## Task Distribution

### Single Distribution (delegate)

```python
# Assign task to specific agent
result = team.delegate("coder", "task", "Implement user login feature")
print(result.content)
```

### Broadcast (broadcast)

```python
# Multiple agents handle simultaneously
results = team.broadcast(
    task_type="review",
    task_content="Check code security",
    target_roles=[AgentRole.REVIEWER, AgentRole.DEVOPS],  # Optional: filter by role
)
```

### Query (query)

```python
# Send query to single agent
result = team.query("xueqiu", "Best practices for Python async programming")
```

## Zoo Animals

### Available Animals

| Animal | Name | Characteristics |
|------|------|------|
| xueqiu | Snowball Monkey | Research expert, skilled at search and analysis |
| liuliu | Flowing Otter | Code architecture, skilled at system design and refactoring |
| xiaohuang | Little Yellow Dog | QA testing, skilled at testing and edge cases |
| heibai | Black and White Bear | Documentation expert, skilled at writing docs and comments |
| xiaozhu | Little Pig | DevOps, skilled at containerization and CI/CD |

### Direct Invocation

```python
from h_agent.adapters.zoo_adapter import ZooAdapter, list_zoo_animals

# List all animals
animals = list_zoo_animals()
for animal in animals:
    print(f"{animal.name}: {animal.description}")

# Direct invocation
adapter = ZooAdapter(animal="xueqiu")
response = adapter.chat("Search best practices for React state management")
print(response.content)
```

### Team Integration

```python
# Quickly register entire zoo
team.register_zoo_animal("xueqiu")
team.register_zoo_animal("liuliu")
team.register_zoo_animal("xiaohuang")

# Use
result = team.delegate("xueqiu", "research", "Frontend state management solution research")
```

## Result Aggregation

```python
# Distribute task to multiple agents
results = team.broadcast("implement", "Implement a certain feature")

# Aggregate results
summary = team.aggregate_results(results)
print(f"Success: {summary['succeeded']}/{summary['total']}")

# Statistics by role
for role, stats in summary['by_role'].items():
    print(f"{role}: {stats['success']} success, {stats['failed']} failed")
```

## Progress Tracking

```python
# View pending tasks
pending = team.list_pending_tasks()

# View history
history = team.list_history(limit=50)

# View task status
status = team.get_task_status(task_id)
```

## Complete Example

```python
from h_agent.team.team import AgentTeam, AgentRole, TaskResult
from h_agent.adapters.zoo_adapter import ZooAdapter

# Create team
team = AgentTeam("web-app")

# Register agents with different roles
team.register_adapter("arch", AgentRole.PLANNER, "opencode", {
    "agent": "architect",
    "model": "gpt-4o"
})
team.register_adapter("dev", AgentRole.CODER, "zoo", {"animal": "liuliu"})
team.register_adapter("tester", AgentRole.REVIEWER, "zoo", {"animal": "xiaohuang"})
team.register_zoo_animal("xueqiu", AgentRole.RESEARCHER)

# Coordinate workflow
print("1. Research phase...")
research = team.delegate("xueqiu", "research", "React vs Vue for enterprise app")

print("2. Planning phase...")
plan = team.delegate("arch", "plan", f"Design system architecture based on research: {research.content}")

print("3. Development phase...")
dev_result = team.delegate("dev", "implement", plan.content)

print("4. Testing phase...")
test_result = team.delegate("tester", "test", dev_result.content)

# Summary
if test_result.success:
    print("✅ Project complete!")
else:
    print(f"❌ Needs fixing: {test_result.error}")
```

## Configuration

### Environment Variables

```bash
# Zoo configuration
export ZOO_PATH=zoo
export ZOO_TIMEOUT=300
export ZOO_API_KEY=your_key

# Adapter configuration
export OPENCODE_PATH=opencode
export ANTHROPIC_API_KEY=your_key
```

### Team Persistence

Team state is saved in `~/.h-agent/team/team_state.json`

- Member list
- Pending tasks
- History (last 100 entries)
