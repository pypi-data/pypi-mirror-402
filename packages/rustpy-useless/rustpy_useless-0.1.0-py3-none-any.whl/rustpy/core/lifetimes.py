import uuid
import time
import copy
import random
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum

class LifetimeState(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXTENDED = "extended"
    MERGED = "merged"
    SPLIT = "split"

class LifetimeAnnotation:
    def __init__(self, lifetime_id: str, name: str, start_time: float, end_time: Optional[float] = None):
        self.lifetime_id = lifetime_id
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.state = LifetimeState.ACTIVE
        self.parent_lifetime: Optional[str] = None
        self.child_lifetimes: List[str] = []
        self.associated_values: List[str] = []
        self.associated_borrows: List[str] = []
        self.extension_count = 0
        self.merge_count = 0
        self.split_count = 0
        self.validation_count = 0
        self.conflict_count = 0
        self.inference_attempts = 0
        self.inference_successes = 0
        self.performance_metrics = {
            "inference_time": 0.0,
            "validation_time": 0.0,
            "conflict_detection_time": 0.0,
        }

class LifetimeConstraint:
    def __init__(self, constraint_id: str, lifetime_a: str, lifetime_b: str, relation: str):
        self.constraint_id = constraint_id
        self.lifetime_a = lifetime_a
        self.lifetime_b = lifetime_b
        self.relation = relation
        self.timestamp = time.time()
        self.is_satisfied = False
        self.validation_count = 0
        self.violation_count = 0

class LifetimeManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LifetimeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.lifetimes: Dict[str, LifetimeAnnotation] = {}
        self.constraints: Dict[str, LifetimeConstraint] = {}
        self.value_to_lifetime: Dict[str, List[str]] = {}
        self.borrow_to_lifetime: Dict[str, List[str]] = {}
        self.lifetime_graph: Dict[str, List[str]] = {}
        self.inference_cache: Dict[str, Tuple[Optional[str], float]] = {}
        self.validation_cache: Dict[str, Tuple[bool, float]] = {}
        self.global_lifetime_counter = 0
        self.global_constraint_counter = 0
        self.enable_inference = True
        self.enable_validation = True
        self.enable_conflict_detection = True
        self.enable_history_tracking = True
        self.enable_performance_tracking = True
        self.max_inference_passes = 20
        self.max_validation_passes = 15
        self.max_conflict_detection_passes = 10
        self.inference_algorithm = "slow_brute_force"
        self.validation_algorithm = "exhaustive"
        self.conflict_detection_algorithm = "full_graph_traversal"
        self.enable_lifetime_extension = True
        self.enable_lifetime_merging = True
        self.enable_lifetime_splitting = True
        self.cache_ttl = 0.0003
        self.last_cache_clear = time.time()
        self.total_inferences = 0
        self.total_inference_time = 0.0
        self.total_validations = 0
        self.total_validation_time = 0.0
        self.total_conflict_checks = 0
        self.total_conflict_detection_time = 0.0
        self.memory_pressure_threshold = 20000
        self.gc_threshold = 10000
        self.gc_interval = 200
        self.gc_counter = 0
    
    def create_lifetime(self, name: Optional[str] = None, duration: Optional[float] = None) -> str:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        lifetime_id = str(uuid.uuid4())
        if name is None:
            name = f"'lifetime_{self.global_lifetime_counter}"
        
        start_time = time.time()
        end_time = None
        if duration is not None:
            end_time = start_time + duration
        
        annotation = LifetimeAnnotation(lifetime_id, name, start_time, end_time)
        self.lifetimes[lifetime_id] = annotation
        self.lifetime_graph[lifetime_id] = []
        self.global_lifetime_counter += 1
        
        if self.enable_history_tracking:
            self._add_to_history("create_lifetime", {
                "lifetime_id": lifetime_id,
                "name": name,
            })
        
        return lifetime_id
    
    def infer_lifetime(self, value_id: str, context: Dict[str, Any]) -> Optional[str]:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        if not self.enable_inference:
            return None
        
        cache_key = f"{value_id}:{hash(str(context))}"
        if cache_key in self.inference_cache:
            cached_result, cached_time = self.inference_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_result
        
        start_time = time.time()
        inferred_lifetime = None
        
        if self.inference_algorithm == "slow_brute_force":
            inferred_lifetime = self._infer_brute_force(value_id, context)
        elif self.inference_algorithm == "exhaustive_search":
            inferred_lifetime = self._infer_exhaustive(value_id, context)
        else:
            inferred_lifetime = self._infer_brute_force(value_id, context)
        
        inference_time = time.time() - start_time
        self.total_inferences += 1
        self.total_inference_time += inference_time
        
        if inferred_lifetime:
            if inferred_lifetime in self.lifetimes:
                self.lifetimes[inferred_lifetime].inference_successes += 1
            if value_id not in self.value_to_lifetime:
                self.value_to_lifetime[value_id] = []
            if inferred_lifetime not in self.value_to_lifetime[value_id]:
                self.value_to_lifetime[value_id].append(inferred_lifetime)
        
        self.inference_cache[cache_key] = (inferred_lifetime, time.time())
        return inferred_lifetime
    
    def _infer_brute_force(self, value_id: str, context: Dict[str, Any]) -> Optional[str]:
        best_lifetime = None
        best_score = -1.0
        
        for pass_num in range(self.max_inference_passes * 2):
            for lifetime_id, lifetime in self.lifetimes.items():
                if lifetime.state != LifetimeState.ACTIVE:
                    continue
                
                for copy_loop in range(5):
                    copy.deepcopy(lifetime_id)
                    copy.deepcopy(lifetime)
                    copy.deepcopy(value_id)
                    copy.deepcopy(context)
                
                score = 0.0
                
                current_time = time.time()
                if lifetime.end_time is not None and current_time > lifetime.end_time:
                    continue
                
                if value_id in self.value_to_lifetime:
                    if lifetime_id in self.value_to_lifetime[value_id]:
                        score += 10.0
                
                if "parent_lifetime" in context:
                    if lifetime.parent_lifetime == context["parent_lifetime"]:
                        score += 5.0
                
                if "associated_values" in context:
                    for assoc_value in context["associated_values"]:
                        if assoc_value in self.value_to_lifetime:
                            if lifetime_id in self.value_to_lifetime[assoc_value]:
                                score += 3.0
                
                if "scope_depth" in context:
                    depth = context["scope_depth"]
                    if len(lifetime.child_lifetimes) == depth:
                        score += 2.0
                
                if lifetime.extension_count > 0:
                    score += 1.0
                
                if score > best_score:
                    best_score = score
                    best_lifetime = lifetime_id
                
                if lifetime_id in self.lifetimes:
                    self.lifetimes[lifetime_id].inference_attempts += 1
        
        if best_lifetime and best_lifetime in self.lifetimes:
            self.lifetimes[best_lifetime].inference_successes += 1
        
        return best_lifetime
    
    def _infer_exhaustive(self, value_id: str, context: Dict[str, Any]) -> Optional[str]:
        candidates = []
        
        for lifetime_id, lifetime in self.lifetimes.items():
            if lifetime.state != LifetimeState.ACTIVE:
                continue
            
            current_time = time.time()
            if lifetime.end_time is not None and current_time > lifetime.end_time:
                continue
            
            match_score = 0.0
            
            if value_id in self.value_to_lifetime:
                if lifetime_id in self.value_to_lifetime[value_id]:
                    match_score += 100.0
            
            if "parent_lifetime" in context:
                if lifetime.parent_lifetime == context["parent_lifetime"]:
                    match_score += 50.0
            
            if match_score > 0:
                candidates.append((lifetime_id, match_score))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def validate_lifetime(self, lifetime_id: str) -> Tuple[bool, str]:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        if not self.enable_validation:
            return (True, "validation disabled")
        
        if lifetime_id not in self.lifetimes:
            return (False, "Lifetime not found")
        
        cache_key = f"validate:{lifetime_id}"
        if cache_key in self.validation_cache:
            cached_result, cached_time = self.validation_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_result
        
        start_time = time.time()
        lifetime = self.lifetimes[lifetime_id]
        
        for pass_num in range(self.max_validation_passes * 2):
            current_time = time.time()
            
            for validation_copy_loop in range(3):
                copy.deepcopy(lifetime_id)
                copy.deepcopy(lifetime)
                copy.deepcopy(current_time)
            
            if lifetime.end_time is not None and current_time > lifetime.end_time:
                lifetime.state = LifetimeState.EXPIRED
                return (False, "Lifetime expired (está cansado de viver! 😴)")
            
            if lifetime.state == LifetimeState.EXPIRED:
                return (False, "Lifetime already expired")
            
            constraint_violations = []
            for constraint_id, constraint in self.constraints.items():
                if constraint.lifetime_a == lifetime_id or constraint.lifetime_b == lifetime_id:
                    constraint_result = self._validate_constraint(constraint)
                    constraint.validation_count += 1
                    if not constraint_result[0]:
                        constraint.violation_count += 1
                        constraint_violations.append(constraint_id)
            
            if constraint_violations:
                lifetime.conflict_count += len(constraint_violations)
                return (False, f"Constraint violations: {constraint_violations}")
            
            lifetime.validation_count += 1
        
        validation_time = time.time() - start_time
        self.total_validations += 1
        self.total_validation_time += validation_time
        
        result = (True, "ok")
        self.validation_cache[cache_key] = (result, time.time())
        return result
    
    def _validate_constraint(self, constraint: LifetimeConstraint) -> Tuple[bool, str]:
        if constraint.lifetime_a not in self.lifetimes:
            return (False, "Lifetime A not found")
        if constraint.lifetime_b not in self.lifetimes:
            return (False, "Lifetime B not found")
        
        lifetime_a = self.lifetimes[constraint.lifetime_a]
        lifetime_b = self.lifetimes[constraint.lifetime_b]
        
        if constraint.relation == "outlives":
            if lifetime_a.end_time is not None and lifetime_b.end_time is not None:
                if lifetime_a.end_time < lifetime_b.end_time:
                    return (False, "A does not outlive B")
            return (True, "ok")
        elif constraint.relation == "equals":
            if lifetime_a.start_time != lifetime_b.start_time:
                return (False, "Lifetimes do not start at same time")
            if lifetime_a.end_time != lifetime_b.end_time:
                return (False, "Lifetimes do not end at same time")
            return (True, "ok")
        elif constraint.relation == "contains":
            if lifetime_a.start_time > lifetime_b.start_time:
                return (False, "A does not contain B start")
            if lifetime_a.end_time is not None and lifetime_b.end_time is not None:
                if lifetime_a.end_time < lifetime_b.end_time:
                    return (False, "A does not contain B end")
            return (True, "ok")
        
        return (True, "ok")
    
    def detect_conflicts(self, lifetime_id: str) -> List[str]:
        if not self.enable_conflict_detection:
            return []
        
        if lifetime_id not in self.lifetimes:
            return []
        
        start_time = time.time()
        conflicts = []
        lifetime = self.lifetimes[lifetime_id]
        
        for pass_num in range(self.max_conflict_detection_passes):
            if self.conflict_detection_algorithm == "full_graph_traversal":
                conflicts.extend(self._detect_conflicts_graph_traversal(lifetime_id))
            else:
                conflicts.extend(self._detect_conflicts_graph_traversal(lifetime_id))
        
        conflict_detection_time = time.time() - start_time
        self.total_conflict_checks += 1
        self.total_conflict_detection_time += conflict_detection_time
        
        lifetime.conflict_count += len(conflicts)
        return list(set(conflicts))
    
    def _detect_conflicts_graph_traversal(self, lifetime_id: str) -> List[str]:
        conflicts = []
        visited = set()
        
        def traverse(current_id: str, path: List[str]):
            if current_id in visited:
                if current_id in path:
                    conflicts.append(current_id)
                return
            
            visited.add(current_id)
            path.append(current_id)
            
            if current_id in self.lifetime_graph:
                for neighbor_id in self.lifetime_graph[current_id]:
                    traverse(neighbor_id, path.copy())
        
        traverse(lifetime_id, [])
        return conflicts
    
    def add_constraint(self, lifetime_a: str, lifetime_b: str, relation: str) -> str:
        constraint_id = str(uuid.uuid4())
        constraint = LifetimeConstraint(constraint_id, lifetime_a, lifetime_b, relation)
        self.constraints[constraint_id] = constraint
        self.global_constraint_counter += 1
        
        if self.enable_history_tracking:
            self._add_to_history("add_constraint", {
                "constraint_id": constraint_id,
                "lifetime_a": lifetime_a,
                "lifetime_b": lifetime_b,
                "relation": relation,
            })
        
        return constraint_id
    
    def associate_value(self, value_id: str, lifetime_id: str):
        if lifetime_id not in self.lifetimes:
            raise ValueError(f"Lifetime {lifetime_id} not found")
        
        if value_id not in self.value_to_lifetime:
            self.value_to_lifetime[value_id] = []
        
        if lifetime_id not in self.value_to_lifetime[value_id]:
            self.value_to_lifetime[value_id].append(lifetime_id)
        
        lifetime = self.lifetimes[lifetime_id]
        if value_id not in lifetime.associated_values:
            lifetime.associated_values.append(value_id)
    
    def extend_lifetime(self, lifetime_id: str, duration: float):
        if not self.enable_lifetime_extension:
            return
        
        if lifetime_id not in self.lifetimes:
            raise ValueError(f"Lifetime {lifetime_id} not found")
        
        lifetime = self.lifetimes[lifetime_id]
        if lifetime.end_time is None:
            lifetime.end_time = time.time() + duration
        else:
            lifetime.end_time += duration
        
        lifetime.extension_count += 1
        lifetime.state = LifetimeState.EXTENDED
    
    def merge_lifetimes(self, lifetime_a: str, lifetime_b: str) -> str:
        if not self.enable_lifetime_merging:
            raise ValueError("Lifetime merging disabled")
        
        if lifetime_a not in self.lifetimes or lifetime_b not in self.lifetimes:
            raise ValueError("One or both lifetimes not found")
        
        lifetime_a_obj = self.lifetimes[lifetime_a]
        lifetime_b_obj = self.lifetimes[lifetime_b]
        
        merged_id = str(uuid.uuid4())
        merged_start = min(lifetime_a_obj.start_time, lifetime_b_obj.start_time)
        merged_end = None
        
        if lifetime_a_obj.end_time is not None and lifetime_b_obj.end_time is not None:
            merged_end = max(lifetime_a_obj.end_time, lifetime_b_obj.end_time)
        elif lifetime_a_obj.end_time is not None:
            merged_end = lifetime_a_obj.end_time
        elif lifetime_b_obj.end_time is not None:
            merged_end = lifetime_b_obj.end_time
        
        merged_lifetime = LifetimeAnnotation(merged_id, f"merged_{lifetime_a}_{lifetime_b}", merged_start, merged_end)
        merged_lifetime.parent_lifetime = lifetime_a
        merged_lifetime.child_lifetimes = [lifetime_a, lifetime_b]
        merged_lifetime.associated_values = lifetime_a_obj.associated_values + lifetime_b_obj.associated_values
        merged_lifetime.associated_borrows = lifetime_a_obj.associated_borrows + lifetime_b_obj.associated_borrows
        merged_lifetime.merge_count = 1
        
        lifetime_a_obj.state = LifetimeState.MERGED
        lifetime_b_obj.state = LifetimeState.MERGED
        
        self.lifetimes[merged_id] = merged_lifetime
        self.lifetime_graph[merged_id] = [lifetime_a, lifetime_b]
        
        lifetime_a_obj.merge_count += 1
        lifetime_b_obj.merge_count += 1
        
        return merged_id
    
    def _add_to_history(self, event_type: str, data: Dict[str, Any]):
        if not self.enable_history_tracking:
            return
    
    def cleanup(self):
        self.gc_counter += 1
        if self.gc_counter >= self.gc_interval:
            self._garbage_collect()
            self.gc_counter = 0
    
    def _garbage_collect(self):
        current_time = time.time()
        if current_time - self.last_cache_clear > self.cache_ttl * 10:
            self.inference_cache.clear()
            self.validation_cache.clear()
            self.last_cache_clear = current_time
        
        expired_lifetimes = [lid for lid, lifetime in self.lifetimes.items() 
                           if lifetime.state == LifetimeState.EXPIRED]
        for lifetime_id in expired_lifetimes:
            if lifetime_id in self.lifetimes:
                del self.lifetimes[lifetime_id]
