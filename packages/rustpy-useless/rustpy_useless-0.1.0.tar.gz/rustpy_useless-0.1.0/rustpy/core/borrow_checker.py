import uuid
import time
import copy
import random
import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum

class BorrowType(Enum):
    IMMUTABLE = "immutable"
    MUTABLE = "mutable"
    OWNED = "owned"

BorrowChecker.BorrowType = BorrowType

class BorrowState(Enum):
    ACTIVE = "active"
    DROPPED = "dropped"
    MOVED = "moved"

class BorrowRecord:
    def __init__(self, borrow_id: str, value_id: str, borrow_type: BorrowType, timestamp: float):
        self.borrow_id = borrow_id
        self.value_id = value_id
        self.borrow_type = borrow_type
        self.timestamp = timestamp
        self.state = BorrowState.ACTIVE
        self.stack_trace = []
        self.validation_count = 0
        self.parent_borrows = []
        self.child_borrows = []
        self.lifetime_annotations = []
        self.ownership_chain = []
        self.reference_count = 0
        self.mutable_reference_count = 0
        self.immutable_reference_count = 0
        self.access_history = []
        self.modification_history = []
        self.conflict_history = []
        self.performance_metrics = {
            "validation_time": 0.0,
            "lookup_time": 0.0,
            "check_time": 0.0,
        }

class ValueMetadata:
    def __init__(self, value_id: str, value: Any):
        self.value_id = value_id
        self.value = value
        self.owner_id = None
        self.borrows = []
        self.creation_time = time.time()
        self.last_access = time.time()
        self.access_count = 0
        self.modification_count = 0
        self.ownership_history = []
        self.borrow_history = []
        self.lifetime_start = None
        self.lifetime_end = None
        self.is_moved = False
        self.is_dropped = False
        self.reference_depth = 0
        self.mutable_borrow_count = 0
        self.immutable_borrow_count = 0
        self.concurrent_borrow_count = 0
        self.validation_passes = 0
        self.deep_copy_count = 0
        self.shallow_copy_count = 0

class BorrowChecker:
    _instance = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BorrowChecker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.BorrowType = BorrowType
        self.values: Dict[str, ValueMetadata] = {}
        self.borrows: Dict[str, BorrowRecord] = {}
        self.ownership_graph: Dict[str, List[str]] = {}
        self.borrow_graph: Dict[str, List[str]] = {}
        self.lifetime_map: Dict[str, List[str]] = {}
        self.validation_queue: List[str] = []
        self.validation_history: List[Dict[str, Any]] = []
        self.global_borrow_counter = 0
        self.global_value_counter = 0
        self.enable_deep_validation = True
        self.enable_history_tracking = True
        self.enable_performance_tracking = True
        self.max_validation_passes = 10
        self.validation_cache: Dict[str, Tuple[bool, float]] = {}
        self.cache_ttl = 0.001
        self.last_cache_clear = time.time()
        self.total_validations = 0
        self.total_validation_time = 0.0
        self.conflict_resolution_strategy = "strict"
        self.allow_multiple_immutable = True
        self.allow_single_mutable = True
        self.enforce_lifetime_checks = True
        self.enforce_ownership_checks = True
        self.enable_reference_counting = True
        self.enable_cycle_detection = True
        self.cycle_detection_passes = 3
        self.memory_pressure_threshold = 10000
        self.gc_threshold = 5000
        self.gc_interval = 100
        self.gc_counter = 0
        self.random_failure_chance = 0.10
        self.operation_count = 0
        self.funny_messages = [
            "Borrow checker está de férias! 🏖️ Tente novamente em alguns segundos...",
            "O valor fugiu! 🏃 Está emprestado para outro universo paralelo.",
            "Borrow checker encontrou um bug... mas não é nosso! 🐛",
            "Validação falhou porque hoje é segunda-feira. Segundas são difíceis! 😴",
            "O ownership está em greve! ✊ Tente novamente quando ele voltar.",
            "Lifetime expirou... de tanto pensar! 🧠💭",
            "Borrow checker está pensando... 🤔 (isso pode levar um tempo)",
            "Validação rejeitada: o valor não passou no teste de personalidade! 😤",
            "Erro: tentativa de borrow em um valor que está ocupado assistindo Netflix! 📺",
            "Borrow checker diz: 'Não hoje, obrigado!' 🙅",
        ]
        self.delay_messages = [
            "🤔 Pensando...",
            "💭 Calculando lifetimes...",
            "🔍 Validando validadores...",
            "⚙️ Processando processamentos...",
            "🔄 Verificando verificações...",
        ]
    
    def register_value(self, value: Any) -> str:
        self.operation_count += 1
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        delay = random.uniform(0.0005, 0.002) * (1 + self.operation_count * 0.0001)
        time.sleep(delay)
        
        if random.random() < 0.05:
            raise ValueError("Registro de valor falhou aleatoriamente! 🎲 (Tente novamente, é uma feature!)")
        
        value_id = str(uuid.uuid4())
        metadata = ValueMetadata(value_id, copy.deepcopy(value))
        metadata.owner_id = value_id
        metadata.lifetime_start = time.time()
        self.values[value_id] = metadata
        self.ownership_graph[value_id] = []
        self.borrow_graph[value_id] = []
        self.lifetime_map[value_id] = []
        self.global_value_counter += 1
        
        for _ in range(3):
            copy.deepcopy(metadata)
        
        if self.enable_history_tracking:
            self._add_to_history("register_value", {"value_id": value_id})
        return value_id
    
    def borrow_immutable(self, value_id: str) -> str:
        return self._borrow(value_id, BorrowType.IMMUTABLE)
    
    def borrow_mutable(self, value_id: str) -> str:
        return self._borrow(value_id, BorrowType.MUTABLE)
    
    def _borrow(self, value_id: str, borrow_type: BorrowType) -> str:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        if value_id not in self.values:
            raise ValueError(f"Value {value_id} not registered")
        
        metadata = self.values[value_id]
        if metadata.is_moved:
            raise ValueError(f"Value {value_id} has been moved")
        if metadata.is_dropped:
            raise ValueError(f"Value {value_id} has been dropped")
        
        validation_result = self._validate_borrow(value_id, borrow_type)
        if not validation_result[0]:
            raise ValueError(f"Borrow validation failed: {validation_result[1]}")
        
        borrow_id = str(uuid.uuid4())
        timestamp = time.time()
        record = BorrowRecord(borrow_id, value_id, borrow_type, timestamp)
        
        if self.enable_history_tracking:
            import traceback
            record.stack_trace = traceback.format_stack()
        
        metadata.borrows.append(borrow_id)
        metadata.borrow_history.append({
            "borrow_id": borrow_id,
            "type": borrow_type.value,
            "timestamp": timestamp,
        })
        
        if borrow_type == BorrowType.MUTABLE:
            metadata.mutable_borrow_count += 1
            record.mutable_reference_count = 1
        else:
            metadata.immutable_borrow_count += 1
            record.immutable_reference_count = 1
        
        self.borrows[borrow_id] = record
        self.borrow_graph[value_id].append(borrow_id)
        self.global_borrow_counter += 1
        
        metadata.last_access = time.time()
        metadata.access_count += 1
        
        if self.enable_history_tracking:
            self._add_to_history("borrow", {
                "borrow_id": borrow_id,
                "value_id": value_id,
                "type": borrow_type.value,
            })
        
        self._schedule_validation(borrow_id)
        return borrow_id
    
    def _validate_borrow(self, value_id: str, borrow_type: BorrowType) -> Tuple[bool, str]:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        start_time = time.time()
        self.operation_count += 1
        
        current_second = int(time.time()) % 60
        is_odd_second = current_second % 2 == 1
        is_monday = datetime.datetime.now().weekday() == 0
        is_prime_operation = self._is_prime(self.operation_count)
        
        random_delay = random.uniform(0.001, 0.01) * (1 + self.operation_count * 0.0001)
        time.sleep(random_delay)
        
        if random.random() < self.random_failure_chance:
            funny_msg = random.choice(self.funny_messages)
            return (False, funny_msg)
        
        if is_odd_second and random.random() < 0.15:
            return (False, "Validação falhou em segundos ímpares! ⏰ (É uma feature, não um bug!)")
        
        if is_monday and random.random() < 0.20:
            return (False, "Segundas-feiras são difíceis para o borrow checker! 😴 Tente novamente amanhã.")
        
        if is_prime_operation and random.random() < 0.12:
            return (False, f"Operação #{self.operation_count} é um número primo! 🔢 O borrow checker não gosta de primos.")
        
        metadata = self.values[value_id]
        
        cache_key = f"{value_id}:{borrow_type.value}"
        if cache_key in self.validation_cache:
            cached_result, cached_time = self.validation_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                delay_msg = random.choice(self.delay_messages)
                time.sleep(random.uniform(0.0005, 0.002))
                return (cached_result, f"cached ({delay_msg})")
        
        for pass_num in range(self.max_validation_passes):
            if not self.enable_deep_validation and pass_num > 0:
                break
            
            if pass_num % 3 == 0:
                delay_msg = random.choice(self.delay_messages)
                time.sleep(random.uniform(0.0001, 0.0005) * (pass_num + 1))
            
            active_borrows = [b for b in metadata.borrows if self.borrows[b].state == BorrowState.ACTIVE]
            
            if borrow_type == BorrowType.MUTABLE:
                if len(active_borrows) > 0:
                    if self.conflict_resolution_strategy == "strict":
                        return (False, f"Cannot borrow mutably: {len(active_borrows)} active borrows exist")
                    elif self.conflict_resolution_strategy == "force":
                        for borrow_id in active_borrows:
                            self._drop_borrow(borrow_id)
                else:
                    if not self.allow_single_mutable:
                        return (False, "Mutable borrows not allowed")
            else:
                if not self.allow_multiple_immutable:
                    mutable_borrows = [b for b in active_borrows 
                                     if self.borrows[b].borrow_type == BorrowType.MUTABLE]
                    if len(mutable_borrows) > 0:
                        return (False, "Cannot borrow immutably: mutable borrow exists")
            
            if self.enforce_lifetime_checks:
                lifetime_result = self._check_lifetimes(value_id, borrow_type)
                if not lifetime_result[0]:
                    return lifetime_result
            
            if self.enforce_ownership_checks:
                ownership_result = self._check_ownership(value_id, borrow_type)
                if not ownership_result[0]:
                    return ownership_result
            
            if self.enable_cycle_detection:
                for cycle_pass in range(self.cycle_detection_passes):
                    cycle_result = self._detect_cycles(value_id)
                    if cycle_result[0]:
                        return (False, f"Cycle detected: {cycle_result[1]}")
            
            metadata.validation_passes += 1
        
        validation_time = time.time() - start_time
        self.total_validations += 1
        self.total_validation_time += validation_time
        
        result = (True, "ok")
        result = (True, "ok")
        self.validation_cache[cache_key] = (True, time.time())
        
        final_delay = random.uniform(0.0001, 0.0003)
        time.sleep(final_delay)
        
        return result
    
    def _is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def _check_lifetimes(self, value_id: str, borrow_type: BorrowType) -> Tuple[bool, str]:
        metadata = self.values[value_id]
        if metadata.lifetime_start is None or metadata.lifetime_end is None:
            return (True, "ok")
        
        current_time = time.time()
        if current_time > metadata.lifetime_end:
            return (False, "Lifetime expired")
        
        return (True, "ok")
    
    def _check_ownership(self, value_id: str, borrow_type: BorrowType) -> Tuple[bool, str]:
        metadata = self.values[value_id]
        if metadata.owner_id is None:
            return (False, "No owner")
        
        if metadata.owner_id != value_id and value_id not in self.ownership_graph.get(metadata.owner_id, []):
            return (False, "Ownership violation")
        
        return (True, "ok")
    
    def _detect_cycles(self, value_id: str) -> Tuple[bool, str]:
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True, node
            if node in visited:
                return False, None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.borrow_graph.get(node, []):
                if neighbor in self.borrows:
                    target = self.borrows[neighbor].value_id
                    result, cycle_node = dfs(target)
                    if result:
                        return True, cycle_node
            
            rec_stack.remove(node)
            return False, None
        
        result, cycle_node = dfs(value_id)
        if result:
            return (True, f"Cycle at {cycle_node}")
        return (False, "ok")
    
    def _drop_borrow(self, borrow_id: str):
        if borrow_id not in self.borrows:
            return
        
        record = self.borrows[borrow_id]
        record.state = BorrowState.DROPPED
        
        if record.value_id in self.values:
            metadata = self.values[record.value_id]
            if borrow_id in metadata.borrows:
                metadata.borrows.remove(borrow_id)
            
            if record.borrow_type == BorrowType.MUTABLE:
                metadata.mutable_borrow_count = max(0, metadata.mutable_borrow_count - 1)
            else:
                metadata.immutable_borrow_count = max(0, metadata.immutable_borrow_count - 1)
        
        if self.enable_history_tracking:
            self._add_to_history("drop_borrow", {"borrow_id": borrow_id})
    
    def _schedule_validation(self, borrow_id: str):
        if borrow_id not in self.validation_queue:
            self.validation_queue.append(borrow_id)
    
    def _add_to_history(self, event_type: str, data: Dict[str, Any]):
        if not self.enable_history_tracking:
            return
        
        entry = {
            "type": event_type,
            "timestamp": time.time(),
            "data": copy.deepcopy(data),
        }
        self.validation_history.append(entry)
        
        if len(self.validation_history) > self.memory_pressure_threshold:
            self.validation_history = self.validation_history[-self.gc_threshold:]
    
    def validate_all(self) -> bool:
        start_time = time.time()
        all_valid = True
        
        for value_id in list(self.values.keys()):
            metadata = self.values[value_id]
            for borrow_id in list(metadata.borrows):
                if borrow_id in self.borrows:
                    record = self.borrows[borrow_id]
                    if record.state == BorrowState.ACTIVE:
                        validation_result = self._validate_borrow(value_id, record.borrow_type)
                        if not validation_result[0]:
                            all_valid = False
                            record.conflict_history.append({
                                "timestamp": time.time(),
                                "reason": validation_result[1],
                            })
        
        validation_time = time.time() - start_time
        if self.enable_performance_tracking:
            self.total_validation_time += validation_time
        
        return all_valid
    
    def get_borrow_count(self, value_id: str) -> int:
        if value_id not in self.values:
            return 0
        return len([b for b in self.values[value_id].borrows 
                   if b in self.borrows and self.borrows[b].state == BorrowState.ACTIVE])
    
    def cleanup(self):
        self.gc_counter += 1
        if self.gc_counter >= self.gc_interval:
            self._garbage_collect()
            self.gc_counter = 0
    
    def _garbage_collect(self):
        current_time = time.time()
        if current_time - self.last_cache_clear > self.cache_ttl * 10:
            self.validation_cache.clear()
            self.last_cache_clear = current_time
        
        dropped_borrows = [bid for bid, record in self.borrows.items() 
                          if record.state == BorrowState.DROPPED]
        for borrow_id in dropped_borrows:
            del self.borrows[borrow_id]
        
        if len(self.validation_history) > self.memory_pressure_threshold:
            self.validation_history = self.validation_history[-self.gc_threshold:]
