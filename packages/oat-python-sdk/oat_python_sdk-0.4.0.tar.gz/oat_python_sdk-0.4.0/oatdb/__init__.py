"""
OatDB Python Client - Improved Version

This client provides a fluent API for building and executing OatDB queries.
"""

import json
import requests

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from functools import lru_cache
from hashlib import sha256
from pldag import PLDAG, CompilationSetting
from graphlib import TopologicalSorter
from abc import ABC, abstractmethod
from itertools import chain
from more_itertools import unique_everseen

def sub_to_pldag(sub_data: Dict[str, dict]) -> PLDAG:
    """Convert OatDB sub response to PLDAG."""
    dag = PLDAG(compilation_setting=CompilationSetting.ON_DEMAND)
    structured = {}

    for node_id, node_data in sub_data.items():
        k, v = list(node_data.items())[0]
        if k == "Primitive":
            structured[node_id] = {
                "type": "primitive",
                "bound": complex(v[0], v[1])
            }
        elif k == "Composite":
            structured[node_id] = {
                "type": "composite",
                "coefficients": dict(v['coefficients']),
                "bias": v['bias'][0]
            }

    # Build dependency graph
    dependencies = {k: set() for k in structured.keys()}
    for node_id, node_data in filter(lambda x: x[1]['type'] == "composite", structured.items()):
        for dep in node_data['coefficients'].keys():
            dependencies[node_id].add(dep)

    # Add nodes in topological order
    id_pointers = {}
    for node_id in TopologicalSorter(dependencies).static_order():
        node_data = structured[node_id]
        if node_data['type'] == "primitive":
            dag_id = dag.set_primitive(id=node_id, bound=node_data['bound'])
            id_pointers[node_id] = dag_id
        elif node_data['type'] == "composite":
            dag_id = dag.set_gelineq(
                coefficients={id_pointers.get(k,k): v for k, v in node_data['coefficients'].items()},
                bias=node_data['bias'],
                alias=node_id
            )
            id_pointers[node_id] = dag_id

    dag.compile()
    return dag

@lru_cache
def pldag_to_sub(dag: PLDAG) -> Dict[str, dict]:
    """Convert PLDAG to OatDB sub format."""
    sub_data = {}
    prims = dag.primitives
    comps = dag.composites
    for node_id in map(str, dag._toposort):
        if node_id in prims:
            bound = dag.get(node_id)
            sub_data[node_id] = {"Primitive": [int(bound.real), int(bound.imag)]}
        elif node_id in comps:
            row_idx = dag._row(node_id)
            coefficients = [
                [str(dag.id_to_alias(k) or k), int(v)]
                for k, v in zip(dag.columns, dag._amat[row_idx])
                if v != 0
            ]
            b = int(dag._bvec[row_idx].real)
            alias_as_id = dag.id_to_alias(node_id)
            if not alias_as_id:
                raise ValueError(f"Composite node {node_id} missing source ID for sub conversion.")
            
            sub_data[alias_as_id] = {
                "Composite": {
                    "coefficients": coefficients,
                    "bias": [b, b]
                }
            }
    return sub_data

RefOrId = Union['FunctionCall', str]
RefOrValue = Union['FunctionCall', str, int, List, Dict]
RefOrBound = Union['FunctionCall', complex]
RefOrPlDAG = Union['FunctionCall', PLDAG]

@dataclass(eq=False)
class FunctionCall(ABC):

    @staticmethod
    def _serialize_for_hash(obj):
        """Recursively serialize objects for hashing, converting FunctionCalls to their out IDs.

        IMPORTANT: This must serialize objects the same way they appear in json_output(),
        so that the hash is based on what actually gets sent to the server.
        """
        if isinstance(obj, FunctionCall):
            return f"<ref:{obj.out}>"
        elif isinstance(obj, dict):
            return {
                FunctionCall._serialize_for_hash(k): FunctionCall._serialize_for_hash(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [FunctionCall._serialize_for_hash(v) for v in obj]
        elif isinstance(obj, complex):
            return [obj.real, obj.imag]
        elif isinstance(obj, set):
            return sorted([FunctionCall._serialize_for_hash(v) for v in obj])
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        elif isinstance(obj, PLDAG):
            # Convert PLDAG to sub format for hashing, matching json_output()
            # This ensures hash is based on what gets sent to server
            return pldag_to_sub(obj)
        else:
            return obj

    @staticmethod
    def _hash_data(d: dict) -> str:
        serialized = FunctionCall._serialize_for_hash(d)
        hash_data = json.dumps(serialized, sort_keys=True)
        return sha256(hash_data.encode()).hexdigest()

    def _fn(self) -> str:
        return self.__class__.__name__
        
    def __hash__(self) -> int:
        # Use full SHA256 hash (64 hex chars = 256 bits)
        # Python can handle arbitrarily large integers
        return int(self.out, 16)

    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionCall):
            return False
        return self.out == other.out

    @property
    def out(self) -> str:
        # Serialize args recursively, handling nested FunctionCalls
        serialized = self._serialize_for_hash({**self.__dict__, **{"fn": self._fn()}})
        hash_data = json.dumps(serialized, sort_keys=True)
        return sha256(hash_data.encode()).hexdigest()

    def json_input(self, data: dict) -> Any:
        """Converts json data coming back from the server into the appropriate format."""
        return data

    @abstractmethod
    def json_output(self) -> list:
        """Build the payload list for this call, including dependencies."""
        raise NotImplementedError()

    def _ref_or_value(self, value: RefOrValue) -> Union[dict, str, int, List]:
        """Convert a value to either a reference or direct value."""
        if isinstance(value, FunctionCall):
            return {"$ref": value.out}
        return value
    
    def _ref_or_dag(self, dag: RefOrPlDAG) -> Union[dict, str]:
        """Convert a PLDAG to either a reference or direct DAG representation."""
        if issubclass(dag.__class__, FunctionCall):
            return {"$ref": dag.out}
        return pldag_to_sub(dag)
    
    def _ref_or_bound(self, bound: RefOrBound) -> Union[dict, List[int]]:
        """Convert a bound to either a reference or direct bound."""
        if issubclass(bound.__class__, FunctionCall):
            return self._ref_or_value(bound)
        return [int(bound.real), int(bound.imag)]

    def _ref_or_value_list(self, values: Union["FunctionCall", List[RefOrValue]]) -> List[Union[dict, str]]:
        """Convert a list of values to references or direct values."""
        if issubclass(values.__class__, FunctionCall):
            return self._ref_or_value(values)
        return [self._ref_or_value(v) for v in values]

@dataclass(eq=False)
class set_property(FunctionCall):

    id:         RefOrValue
    property:   RefOrValue
    value:      RefOrValue

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.id.__class__, FunctionCall):
            earlier_builds += self.id.json_output()
        if issubclass(self.property.__class__, FunctionCall):
            earlier_builds += self.property.json_output()
        if issubclass(self.value.__class__, FunctionCall):
            earlier_builds += self.value.json_output()
        
        return earlier_builds + [
            {
                "fn": "set_property",
                "args": {
                    "id": self._ref_or_value(self.id),
                    "property": self._ref_or_value(self.property),
                    "value": self._ref_or_value(self.value)
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class set_primitive(FunctionCall):

    id: Union[str, FunctionCall]
    bound: Union[complex, FunctionCall] = 1j

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.id.__class__, FunctionCall):
            earlier_builds += self.id.json_output()
        if issubclass(self.bound.__class__, FunctionCall):
            earlier_builds += self.bound.json_output()
        return earlier_builds + [
            {
                "fn": "set_primitive",
                "args": {
                    "id": self._ref_or_value(self.id),
                    "bound": self._ref_or_value(self.bound) if issubclass(self.bound.__class__, FunctionCall) else [
                        int(self.bound.real),
                        int(self.bound.imag)
                    ]
                },
                "out": self.out
            }
        ]
    
@dataclass(eq=False)
class set_primitives(FunctionCall):

    ids: Union[List[RefOrValue], FunctionCall]
    bound: Union[complex, FunctionCall] = 1j

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.ids.__class__, FunctionCall):
            earlier_builds += self.ids.json_output()
        else:
            for id in self.ids:
                if issubclass(id.__class__, FunctionCall):
                    earlier_builds += id.json_output()

        if issubclass(self.bound.__class__, FunctionCall):
            earlier_builds += self.bound.json_output()
        
        return earlier_builds + [
            {
                "fn": "set_primitives",
                "args": {
                    "ids": self._ref_or_value_list(self.ids),
                    "bound": self._ref_or_value(self.bound) if issubclass(self.bound.__class__, FunctionCall) else [int(self.bound.real), int(self.bound.imag)]
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class set_gelineq(FunctionCall):

    coefficients: Union[Dict[Union[str, FunctionCall], Union[int, FunctionCall]], FunctionCall]
    bias: Union[int, FunctionCall]
    alias: Optional[str] = None

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.coefficients.__class__, FunctionCall):
            earlier_builds = self.coefficients.json_output()
        else:
            for k in self.coefficients.keys():
                if issubclass(k.__class__, FunctionCall):
                    earlier_builds += k.json_output()
            for v in self.coefficients.values():
                if issubclass(v.__class__, FunctionCall):
                    earlier_builds += v.json_output()
        
        build_bias = self.bias.json_output() if issubclass(self.bias.__class__, FunctionCall) else []
        return earlier_builds + build_bias + [
            {
                "fn": "set_gelineq",
                "args": {
                    "coefficients": self._ref_or_value(self.coefficients) if issubclass(self.coefficients.__class__, FunctionCall) else [
                        {
                            "id": self._ref_or_value(k),
                            "coefficient": self._ref_or_value(v)
                        }
                        for k, v in self.coefficients.items()
                    ],
                    "bias": self._ref_or_value(self.bias),
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class SetThresholdOperatorCall(FunctionCall):
    """Base class for set_atleast, set_atmost, set_equal."""

    references: Union[List[RefOrValue], FunctionCall]
    value: Union[int, FunctionCall]
    alias: Optional[str] = None

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.references.__class__, FunctionCall):
            earlier_builds += self.references.json_output()
        else:
            for ref in self.references:
                if issubclass(ref.__class__, FunctionCall):
                    earlier_builds += ref.json_output()

        if issubclass(self.value.__class__, FunctionCall):
            earlier_builds += self.value.json_output()
        
        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "references": self._ref_or_value_list(self.references),
                    "value": self._ref_or_value(self.value),
                    **({"alias": self.alias} if self.alias is not None else {})
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class SetLogicalOperatorCall(FunctionCall):
    """Base class for set_and, set_or, set_not, set_xor."""

    references: Union[List[RefOrValue], FunctionCall]
    alias: Optional[str] = None
    
    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.references.__class__, FunctionCall):
            earlier_builds += self.references.json_output()
        else:
            for ref in self.references:
                if issubclass(ref.__class__, FunctionCall):
                    earlier_builds += ref.json_output()

        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "references": self._ref_or_value_list(self.references),
                    **({"alias": self.alias} if self.alias is not None else {})
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class SetBinaryOperatorCall(FunctionCall):
    """Base class for set_imply, set_equiv."""

    lhs: RefOrValue
    rhs: RefOrValue
    alias: Optional[str] = None

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.lhs.__class__, FunctionCall):
            earlier_builds += self.lhs.json_output()
        if issubclass(self.rhs.__class__, FunctionCall):
            earlier_builds += self.rhs.json_output()
        
        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "lhs": self._ref_or_value(self.lhs),
                    "rhs": self._ref_or_value(self.rhs),
                    **({"alias": self.alias} if self.alias is not None else {})
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class set_atleast(SetThresholdOperatorCall):
    pass

@dataclass(eq=False)
class set_atmost(SetThresholdOperatorCall):
    pass

@dataclass(eq=False)
class set_equal(SetThresholdOperatorCall):
    pass
    
@dataclass(eq=False)
class set_and(SetLogicalOperatorCall):
    pass
    
@dataclass(eq=False)
class set_or(SetLogicalOperatorCall):
    pass

@dataclass(eq=False)
class set_not(SetLogicalOperatorCall):
    pass
    
@dataclass(eq=False)
class set_xor(SetLogicalOperatorCall):
    pass

@dataclass(eq=False)
class set_imply(SetBinaryOperatorCall):
    pass

@dataclass(eq=False)
class set_equiv(SetBinaryOperatorCall):
    pass

@dataclass(eq=False)
class sub(FunctionCall):
    """Call to sub function."""

    root: RefOrPlDAG

    def json_input(self, data: dict) -> PLDAG:
        return sub_to_pldag(data)
    
    def json_output(self) -> list:
        build_root = self.root.json_output() if issubclass(self.root.__class__, FunctionCall) else []
        return build_root + [
            {
                "fn": "sub",
                "args": {
                    "root": self._ref_or_value(self.root)
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class get_node_ids(FunctionCall):
    
    filter: Optional[RefOrValue] = None

    def json_output(self) -> list:
        build_filter = self.filter.json_output() if issubclass(self.filter.__class__, FunctionCall) else []
        return build_filter + [
            {
                "fn": self._fn(),
                "args": {
                    **({"filter": self._ref_or_value(self.filter)} if self.filter is not None else {})
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class get_nodes(FunctionCall):

    ids: Union[List[RefOrValue], FunctionCall]

    def json_output(self) -> list:
        build_ids = self.ids.json_output() if issubclass(self.ids.__class__, FunctionCall) else []
        return build_ids + [
            {
                "fn": self._fn(),
                "args": {
                    "ids": self._ref_or_value_list(self.ids)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_node(FunctionCall):

    id: RefOrValue

    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_property_values(FunctionCall):

    property: RefOrValue
    
    def json_output(self) -> list:
        return [
            {
                "fn": self._fn(),
                "args": {
                    "property": self._ref_or_value(self.property)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_alias(FunctionCall):
    
    id: RefOrValue

    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_id_from_alias(FunctionCall):

    alias: RefOrValue
    
    def json_output(self) -> list:
        build_alias = self.alias.json_output() if issubclass(self.alias.__class__, FunctionCall) else []
        return build_alias + [
            {
                "fn": self._fn(),
                "args": {
                    "alias": self._ref_or_value(self.alias)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_aliases_from_id(FunctionCall):

    id: RefOrValue

    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class get_ids_from_aliases(FunctionCall):
    
    aliases: Union[List[RefOrValue], FunctionCall]

    def json_output(self) -> list:
        build_aliases = self.aliases.json_output() if issubclass(self.aliases.__class__, FunctionCall) else []
        return build_aliases + [
            {
                "fn": self._fn(),
                "args": {
                    "aliases": self._ref_or_value_list(self.aliases)
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class get_ids_from_dag(FunctionCall):

    dag: RefOrPlDAG

    def json_output(self) -> list:
        build_dag = self.dag.json_output() if issubclass(self.dag.__class__, FunctionCall) else []
        return build_dag + [
            {
                "fn": self._fn(),
                "args": {
                    "dag": self._ref_or_dag(self.dag)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class propagate(FunctionCall):

    assignments: Union[Dict[RefOrValue, Union[complex, FunctionCall]], FunctionCall]

    @property
    def out(self) -> str:
        # Serialize args recursively, handling nested FunctionCalls
        serialized = self._serialize_for_hash({"assignments": self.assignments})
        hash_data = json.dumps(serialized, sort_keys=True)
        return sha256(hash_data.encode()).hexdigest()
    
    def json_input(self, data: dict) -> dict:
        return {
            key: complex(value[0], value[1]) for key, value in data.items()
        } 
    
    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.assignments.__class__, FunctionCall):
            earlier_builds += self.assignments.json_output()
        else:
            for k, v in self.assignments.items():
                if issubclass(k.__class__, FunctionCall):
                    earlier_builds += k.json_output()
                if issubclass(v.__class__, FunctionCall):
                    earlier_builds += v.json_output()

        return earlier_builds + [
            {
                "fn": "propagate",
                "args": {
                    "assignments": self._ref_or_value(self.assignments) if issubclass(self.assignments.__class__, FunctionCall) else [
                        {
                            "id": self._ref_or_value(k),
                            "bound": self._ref_or_value(v) if issubclass(v.__class__, FunctionCall) else [int(v.real), int(v.imag)]
                        }
                        for k, v in self.assignments.items()
                    ]
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class propagate_many(FunctionCall):

    many_assignments: Union[List[Dict[RefOrValue, RefOrBound]], FunctionCall]

    def json_input(self, data: dict) -> list:
        return [
            {
                key: complex(value[0], value[1]) for key, value in assignments.items()
            }
            for assignments in data
        ]
    
    def json_output(self) -> list:

        earlier_builds = []
        if issubclass(self.many_assignments.__class__, FunctionCall):
            earlier_builds += self.many_assignments.json_output()
        else:
            for assignments in self.many_assignments:
                for assign_id, assign_bound in assignments.items():
                    if issubclass(assign_id.__class__, FunctionCall):
                        earlier_builds += assign_id.json_output()
                    
                    if issubclass(assign_bound.__class__, FunctionCall):
                        earlier_builds += assign_bound.json_output()

        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "many_assignments": self._ref_or_value(self.many_assignments) if issubclass(self.many_assignments.__class__, FunctionCall) else [
                        [
                            {
                                "id": self._ref_or_value(assign_id),
                                "bound": self._ref_or_value(assign_bound) if issubclass(assign_bound.__class__, FunctionCall) else [
                                    int(assign_bound.real),
                                    int(assign_bound.imag)
                                ]
                            }
                            for assign_id, assign_bound in assignments.items()
                        ]
                        for assignments in self.many_assignments
                    ]
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class sub_many(FunctionCall):

    roots: Union[List[RefOrValue], FunctionCall]

    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.roots.__class__, FunctionCall):
            earlier_builds += self.roots.json_output()
        else:
            for root in self.roots:
                if issubclass(root.__class__, FunctionCall):
                    earlier_builds += root.json_output()
        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "roots": self._ref_or_value_list(self.roots)
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class validate(FunctionCall):
    
    dag: RefOrPlDAG
    
    def json_output(self) -> list:
        build_dag = self.dag.json_output() if issubclass(self.dag.__class__, FunctionCall) else []
        return build_dag + [
            {
                "fn": self._fn(),
                "args": {
                    "dag": self._ref_or_dag(self.dag)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class ranks(FunctionCall):
    
    dag: RefOrPlDAG

    def json_output(self) -> list:
        build_dag = self.dag.json_output() if issubclass(self.dag.__class__, FunctionCall) else []
        return build_dag + [
            {
                "fn": self._fn(),
                "args": {
                    "dag": self._ref_or_dag(self.dag)
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class delete_node(FunctionCall):

    id: RefOrValue

    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id) 
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class delete_sub(FunctionCall):
    
    roots: Union[List[RefOrValue], FunctionCall]
    
    def json_output(self) -> list:
        earlier_builds = []
        if issubclass(self.roots.__class__, FunctionCall):
            earlier_builds += self.roots.json_output()
        else:
            for root in self.roots:
                if issubclass(root.__class__, FunctionCall):
                    earlier_builds += root.json_output()
        
        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "roots": self._ref_or_value_list(self.roots) if not issubclass(self.roots.__class__, FunctionCall) else [
                        self._ref_or_value(root) for root in self.roots
                    ]
                },
                "out": self.out
            }
        ]

@dataclass(eq=False)
class solve(FunctionCall):
    """Call to solve function."""

    dag: RefOrPlDAG
    objective: Union[Dict[RefOrId, RefOrValue], FunctionCall]
    assume: Union[Dict[RefOrId, RefOrBound], FunctionCall]
    maximize: bool = True

    def json_input(self, inp: Dict[str, List[int]]) -> dict:
        return {
            k: complex(v[0], v[1]) for k, v in inp.items()
        }

    def json_output(self) -> list:
        earlier_builds = []
        
        if issubclass(self.dag.__class__, FunctionCall):
            earlier_builds += self.dag.json_output()
        
        if issubclass(self.objective.__class__, FunctionCall):
            earlier_builds += self.objective.json_output()

        for coef_id, coef_value in self.objective.items():
            if issubclass(coef_id.__class__, FunctionCall):
                earlier_builds += coef_id.json_output()

            if issubclass(coef_value.__class__, FunctionCall):
                earlier_builds += coef_value.json_output()
        
        if issubclass(self.assume.__class__, FunctionCall):
            earlier_builds += self.assume.json_output()

        for assum_id, assum_bound in self.assume.items():
            if issubclass(assum_id.__class__, FunctionCall):
                earlier_builds += assum_id.json_output()
            
            if issubclass(assum_bound.__class__, FunctionCall):
                earlier_builds += assum_bound.json_output()

        return earlier_builds + [
            {
                "fn": self._fn(),
                "args": {
                    "dag": self._ref_or_dag(self.dag),
                    "objective": [
                        {
                            "id": self._ref_or_value(coef_id),
                            "coefficient": self._ref_or_value(coef_value)
                        }
                        for coef_id, coef_value in self.objective.items()
                    ],
                    "assume": [
                        {
                            "id": self._ref_or_value(assum_id),
                            "bound": self._ref_or_value(assum_bound) if issubclass(assum_bound.__class__, FunctionCall) else [
                                int(assum_bound.real),
                                int(assum_bound.imag)
                            ]
                        }
                        for assum_id, assum_bound in self.assume.items()
                    ],
                    "maximize": self.maximize
                },
                "out": self.out
            }
        ]


@dataclass(eq=False)
class solve_many(FunctionCall):
    
    dag: RefOrPlDAG
    objectives: Union[List[List[Dict[RefOrId, RefOrValue]]], FunctionCall]
    assume: Union[Dict[RefOrId, RefOrBound], FunctionCall]
    maximize: bool = True

    def json_input(self, data: dict) -> List[Dict[str, complex]]:
        return [
            {
                k: complex(v[0], v[1]) for k, v in assignment.items()
            }
            for assignment in data
        ]

    def json_output(self) -> list:
        earlier_builds = []
        if isinstance(self.dag, FunctionCall):
            earlier_builds += self.dag.json_output()

        if isinstance(self.objectives, FunctionCall):
            earlier_builds += self.objectives.json_output()

        for objective in self.objectives:
            if isinstance(objective, FunctionCall):
                earlier_builds += objective.json_output()

            for obj_id, obj_coef in objective.items():
                if isinstance(obj_id, FunctionCall):
                    earlier_builds += obj_id.json_output()

                if isinstance(obj_coef, FunctionCall):
                    earlier_builds += obj_coef.json_output()
        
        if issubclass(self.assume.__class__, FunctionCall):
            earlier_builds += self.assume.json_output()

        for ass_id, ass_bound in self.assume.items():
            if issubclass(ass_id.__class__, FunctionCall):
                earlier_builds += ass_id.json_output()
            
            if issubclass(ass_bound.__class__, FunctionCall):
                earlier_builds += ass_bound.json_output()

        return earlier_builds + [{
            "fn": self._fn(),
            "args": {
                "dag": self._ref_or_dag(self.dag),
                "objectives": self._ref_or_value(self.objectives) if issubclass(self.objectives.__class__, FunctionCall) else [
                    [
                        {
                            "id": self._ref_or_value(obj_id),
                            "coefficient": self._ref_or_value(obj_val)
                        }
                        for obj_id, obj_val in objective.items()
                    ]
                    for objective in self.objectives
                ],
                "assume": self._ref_or_value(self.assume) if issubclass(self.assume.__class__, FunctionCall) else [
                    {
                        "id": self._ref_or_value(assum_id),
                        "bound": self._ref_or_bound(assum_bound)
                    }
                    for assum_id, assum_bound in self.assume.items()
                ],
                "maximize": self.maximize
            },
            "out": self.out
        }]
    
@dataclass(eq=False)
class get_node_children(FunctionCall):
    
    id: RefOrId
    
    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id)
                },
                "out": self.out
            }
        ]
    
@dataclass(eq=False)
class get_node_parents(FunctionCall):
    
    id: RefOrId
    
    def json_output(self) -> list:
        build_id = self.id.json_output() if issubclass(self.id.__class__, FunctionCall) else []
        return build_id + [
            {
                "fn": self._fn(),
                "args": {
                    "id": self._ref_or_value(self.id)
                },
                "out": self.out
            }
        ]

class OatDBError(Exception):
    """Base exception for OatDB client errors."""
    pass

class OatDBConnectionError(OatDBError):
    """Raised when connection to OatDB fails."""
    pass

class OatDBExecutionError(OatDBError):
    """Raised when OatDB execution fails."""

    def __init__(self, message: str, status_code: int, response: dict):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        import json
        error_details = json.dumps(self.response, indent=2)
        return f"{super().__str__()}\nError details:\n{error_details}"


@dataclass
class OatClient:
    """
    Client for interacting with OatDB API.

    Usage:
        client = OatClient("http://localhost:7061")

        # Build query
        x = client.set_primitive("x", bound=10j)
        y = client.set_primitive("y", bound=10j)
        constraint = client.set_and([x, y])
        dag = client.sub(constraint)

        # Execute
        result = client.execute([dag.out])
        print(result[dag.out])
    """
    base_url: str
    timeout: int = 30
    verify_ssl: bool = True

    def health_check(self) -> bool:
        """Check if the OatDB server is healthy."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
        
    def execute(
        self,
        call: FunctionCall
    ) -> Dict[str, Any]:
        """
        Execute all buffered calls.

        Args:
            outputs: List of output variable names to return.
                    If None, returns all outputs.
            clear_buffer: Whether to clear the buffer after execution

        Returns:
            Dict mapping output names to their values

        Raises:
            OatDBConnectionError: If connection to server fails
            OatDBExecutionError: If server returns an error
        """
        return self.execute_many([call])[call.out]
        
    def execute_many(
        self,
        calls: List[FunctionCall]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple calls and return their results.

        Args:
            calls: List of FunctionCall instances to execute.
        Returns:
            List of Dicts mapping output names to their values for each call.
        """
        payload = {
            "calls": self.debug_payload(calls),
            "outputs": [call.out for call in calls]
        }

        try:
            response = requests.post(
                f"{self.base_url}/call",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                raise OatDBExecutionError(
                    f"OatDB execution failed: {response.status_code}",
                    response.status_code,
                    error_data
                )
            call_map = {call.out: call for call in calls}
            response_data = response.json()
            return {
                key: call_map[key].json_input(value)
                for key, value in response_data.items()
            }

        except requests.RequestException as e:
            raise OatDBConnectionError(f"Failed to connect to OatDB: {e}") from e

    def debug_payload(self, calls: List[FunctionCall]) -> dict:
        """
        Get the JSON payload that would be sent without executing.
        Useful for debugging.
        """
        return list(unique_everseen(chain(*[call.json_output() for call in calls]), key=lambda x: x.get('out')))

# Export public API
__all__ = [
    'OatClient'
]
