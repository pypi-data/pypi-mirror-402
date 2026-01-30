# OatDB Python SDK

A Python client library for interacting with the OatDB (Optimization and Analysis Tooling) database backend.

## Features

- ✅ Full support for all 30 OatDB API functions
- ✅ Logical operations (AND, OR, XOR, NOT, IMPLY, EQUIV)
- ✅ Cardinality constraints (AtLeast, AtMost, Equal)
- ✅ Linear inequality constraints (GeLineq)
- ✅ Property management
- ✅ DAG operations (sub, sub_many, validate, ranks)
- ✅ Constraint propagation
- ✅ Optimization solver (solve, solve_many)
- ✅ Node deletion and management
- ✅ Alias support for named constraints
- ✅ Type hints for better IDE support

## Installation

```bash
pip install oat-python-sdk
```

Or with Poetry:

```bash
poetry add oat-python-sdk
```

## Quick Start

```python
from oatdb import OatClient, set_primitive, set_property, set_and, sub, solve

# Initialize client
client = OatClient("http://localhost:7061")

# Create primitives with bounds [min, max]
x = set_primitive("x", bound=1j)  # [0, 1]
y = set_primitive("y", bound=10j)  # [0, 10]

# Add properties
x_name = set_property(x, "name", "Variable X")

# Create constraints
constraint = set_and([x, y], alias="my_constraint")

# Extract DAG and solve
dag = sub(constraint)
solution = solve(
    dag=dag,
    objective={
        x: 1,
        y: 2
    },
    assume={
        # Force constraint to be true
        constraint: 1+1j
    },
    maximize=True
)

# Execute and get results
result = client.execute(solution)
print(result)
```

## Core Concepts

### Bounds

Bounds are represented as complex numbers where:
- Real part = lower bound
- Imaginary part = upper bound

```python
# Bound [0, 1]
bound = 1j

# Bound [5, 10]
bound = 5 + 10j

# Access bounds from solution
solution_data = result[solution.out]
x_bounds = solution_data["x"]  # [lower, upper] as list
```

### Function Calls and Execution

All operations return `FunctionCall` objects that you execute using the client:

```python
from oatdb import OatClient, set_primitive, set_and, sub

client = OatClient("http://localhost:7061")

# Create function calls
x = set_primitive("x", bound=1j)
y = set_primitive("y", bound=1j)
constraint = set_and([x, y])

# Execute a single operation
result = client.execute(constraint)

# Execute multiple operations
dag = sub(constraint)
result = client.execute_many([x, y, constraint, dag])

# Access results by the function call's output key
dag_data = result[dag.out]
```

## Available Functions

All functions return `FunctionCall` objects that are executed using `client.execute()` or `client.execute_many()`.

### Primitive Operations
- `set_primitive(id: str, bound: complex = 1j, alias: Optional[str] = None)` - Create a single primitive
- `set_primitives(ids: List[str], bound: complex = 1j)` - Create multiple primitives
- `set_property(id: Union[str, FunctionCall], property: str, value: Any)` - Set node property

### Logical Operations
- `set_and(references: List, alias: Optional[str] = None)` - AND operation
- `set_or(references: List, alias: Optional[str] = None)` - OR operation
- `set_xor(references: List, alias: Optional[str] = None)` - XOR operation
- `set_not(references: List, alias: Optional[str] = None)` - NOT operation
- `set_imply(lhs, rhs, alias: Optional[str] = None)` - Implication (lhs → rhs)
- `set_equiv(lhs, rhs, alias: Optional[str] = None)` - Equivalence (lhs ↔ rhs)

### Cardinality Constraints
- `set_atleast(references: List, value: int, alias: Optional[str] = None)` - At least N must be true
- `set_atmost(references: List, value: int, alias: Optional[str] = None)` - At most N must be true
- `set_equal(references: List, value: Union[int, str], alias: Optional[str] = None)` - Exactly N must be true

### Linear Constraints
- `set_gelineq(coefficients: Dict, bias: int, alias: Optional[str] = None)` - Greater-or-equal linear inequality (ax + b >= 0)

### DAG Operations
- `sub(root)` - Extract sub-DAG from a root node
- `sub_many(roots: List)` - Extract multiple sub-DAGs
- `get_node_ids(dag)` - Get all node IDs in a DAG
- `get_ids_from_dag(dag)` - Get all node IDs from a DAG (alternative)
- `validate(dag)` - Validate DAG structure
- `ranks(dag)` - Compute topological ranks

### Alias Operations
- `get_id_from_alias(alias: str)` - Get node ID from alias
- `get_alias(id)` - Get alias for a node ID
- `get_aliases_from_id(id)` - Get all aliases for a node ID
- `get_ids_from_aliases(aliases: List[str])` - Get IDs for multiple aliases

### Node Operations
- `get_node(id)` - Get a single node
- `get_nodes(ids: List)` - Get multiple nodes
- `get_property_values(property: str)` - Get all nodes with a specific property

### Propagation
- `propagate(assignments: Dict)` - Propagate constraints with assignments
- `propagate_many(many_assignments: List[Dict])` - Propagate multiple assignment sets

### Solver
- `solve(dag, objective: Dict, assume: Optional[Dict] = None, maximize: bool = True)` - Solve single optimization
- `solve_many(dag, objectives: List[Dict], assume: Optional[Dict] = None, maximize: bool = True)` - Solve multiple optimizations

### Deletion
- `delete_node(id)` - Delete a single node
- `delete_sub(roots: List)` - Delete sub-DAGs from roots

### Client Methods
- `OatClient(url: str)` - Initialize client with server URL
- `client.execute(call: FunctionCall)` - Execute a single function call
- `client.execute_many(calls: List[FunctionCall])` - Execute multiple function calls

## Complete Example

```python
from oatdb import (
    OatClient, set_primitive, set_property, set_and, set_or,
    set_imply, set_atleast, set_gelineq, sub, solve
)

# Initialize
client = OatClient("http://localhost:7061")

# Create primitives
x = set_primitive("x", bound=10j)
y = set_primitive("y", bound=10j)
z = set_primitive("z", bound=10j)

# Add metadata
x_type = set_property(x, "type", "variable")
x_priority = set_property(x, "priority", 10)

# Create constraints
and_constraint = set_and([x, y], alias="both_xy")
or_constraint = set_or([y, z])
imply_constraint = set_imply(x, y)  # x → y

# Cardinality: at least 2 must be true
atleast_2 = set_atleast([x, y, z], 2)

# Linear constraint: 2x + 3y - z + 5 >= 0
linear = set_gelineq(
    coefficients={x: 2, y: 3, z: -1},
    bias=5
)

# Combine all constraints
root = set_and([atleast_2, linear], alias="root")

# Extract DAG
dag = sub(root)

# Solve optimization: maximize 3x + 2y + z
solution = solve(
    dag=dag,
    objective={
        x: 3,
        y: 2,
        z: 1
    },
    assume={
        root: 1+1j
    },
    maximize=True
)

# Execute and get results
result = client.execute(solution)

print("Solution:")
for var, bounds in result.items():
    if isinstance(bounds, complex):
        print(f"  {var}: [{bounds.real}, {bounds.imag}]")
```

## Working with Aliases

```python
from oatdb import OatClient, set_primitive, set_and, get_id_from_alias, get_alias

client = OatClient("http://localhost:7061")

# Create constraint with alias
x = set_primitive("x", bound=1j)
y = set_primitive("y", bound=1j)
constraint = set_and([x, y], alias="my_constraint")

# Execute creation
client.execute_many([x, y, constraint])

# Query by alias
id_from_alias = get_id_from_alias("my_constraint")
alias_from_id = get_alias(id_from_alias)

result = client.execute_many([id_from_alias, alias_from_id])
print(f"ID: {result[id_from_alias.out]}")
print(f"Alias: {result[alias_from_id.out]}")
```

## Propagation Example

```python
from oatdb import OatClient, set_primitive, set_and, propagate

client = OatClient("http://localhost:7061")

# Create AND constraint
a = set_primitive("a", bound=1j)
b = set_primitive("b", bound=1j)
c = set_primitive("c", bound=1j)
and_gate = set_and([a, b, c], alias="and_gate")

# Propagate: if AND is true, what can we infer?
prop_result = propagate(
    assignments={
        a: 1+1j,
        b: 1+1j,
        c: 1+1j,
        and_gate: 1j  # Upper bound only
    }
)

result = client.execute(prop_result)
# Result will show that a, b, and c must all be [1, 1]
print(f"Inferred bounds: {result}")
```

## Testing

### Run the comprehensive test suite:

```bash
cd clients/Python
python tests/test_client.py
```

Or with Poetry:

```bash
poetry run python tests/test_client.py
```

**Note**: Make sure the OatDB server is running on `http://localhost:7061` before running tests.

### Run examples:

```bash
python examples.py
```

## Requirements

- Python >= 3.10
- requests >= 2.31.0

## Development

```bash
# Install with Poetry
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .

# Type checking
poetry run mypy oatdb
```

## License

MIT

## Links

- [GitHub Repository](https://github.com/yourusername/oat-db-rust-v2)
- [OatDB Documentation](https://github.com/yourusername/oat-db-rust-v2)
- [Rust Client](https://github.com/yourusername/oat-db-rust-v2/tree/main/clients/Rust)
