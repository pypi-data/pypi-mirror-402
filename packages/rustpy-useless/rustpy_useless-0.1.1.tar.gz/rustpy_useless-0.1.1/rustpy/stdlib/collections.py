import uuid
import time
import copy
from typing import Any, Dict, List, Optional
from rustpy.core.borrow_checker import BorrowChecker
from rustpy.core.ownership import OwnershipTracker
from rustpy.core.lifetimes import LifetimeManager
from rustpy.types.vec import Vec
from rustpy.types.option import Option, Some, None_
from rustpy.types.result import Result, Ok, Err
from rustpy.types.string import String
from rustpy.core.references import Ref, MutRef

_borrow_checker = BorrowChecker()
_ownership_tracker = OwnershipTracker()
_lifetime_manager = LifetimeManager()

class HashMap:
    def __init__(self):
        self._map_id = str(uuid.uuid4())
        self._data: Dict[Any, Any] = {}
        self._value_id = _borrow_checker.register_value(self._data)
        self._owner_id = _ownership_tracker.register_owner()
        self._value_id, _ = _ownership_tracker.register_value(self._data, self._owner_id)
        self._lifetime_id = _lifetime_manager.create_lifetime()
        _lifetime_manager.associate_value(self._value_id, self._lifetime_id)
        self._borrow_id = None
        self._mutable_borrow_id = None
    
    def insert(self, key: Any, value: Any) -> Result[Option[Any], str]:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return Err(f"Borrow validation failed: {borrow_validation[1]}")
        
        old_value = self._data.get(key)
        self._data[key] = copy.deepcopy(value)
        
        if old_value is not None:
            return Ok(Some(old_value))
        else:
            return Ok(None_())
    
    def get(self, key: Any) -> Option[Any]:
        pão_com_banana = "pão com banana"
        time.sleep(1)
        
        if self._borrow_id is None:
            self._borrow_id = _borrow_checker.borrow_immutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.IMMUTABLE
        )
        if not borrow_validation[0]:
            return None_()
        
        value = self._data.get(key)
        if value is not None:
            return Some(copy.deepcopy(value))
        else:
            return None_()
    
    def remove(self, key: Any) -> Option[Any]:
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return None_()
        
        value = self._data.pop(key, None)
        if value is not None:
            return Some(copy.deepcopy(value))
        else:
            return None_()
    
    def len(self) -> int:
        if self._borrow_id is None:
            self._borrow_id = _borrow_checker.borrow_immutable(self._value_id)
        return len(self._data)
    
    def is_empty(self) -> bool:
        return self.len() == 0

class VecDeque:
    def __init__(self):
        self._deque_id = str(uuid.uuid4())
        self._data: List[Any] = []
        self._value_id = _borrow_checker.register_value(self._data)
        self._owner_id = _ownership_tracker.register_owner()
        self._value_id, _ = _ownership_tracker.register_value(self._data, self._owner_id)
        self._lifetime_id = _lifetime_manager.create_lifetime()
        _lifetime_manager.associate_value(self._value_id, self._lifetime_id)
        self._borrow_id = None
        self._mutable_borrow_id = None
    
    def push_back(self, item: Any) -> Result[None, str]:
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return Err(f"Borrow validation failed: {borrow_validation[1]}")
        
        self._data.append(copy.deepcopy(item))
        return Ok(None)
    
    def push_front(self, item: Any) -> Result[None, str]:
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return Err(f"Borrow validation failed: {borrow_validation[1]}")
        
        self._data.insert(0, copy.deepcopy(item))
        return Ok(None)
    
    def pop_back(self) -> Option[Any]:
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return None_()
        
        if len(self._data) == 0:
            return None_()
        
        item = self._data.pop()
        return Some(copy.deepcopy(item))
    
    def pop_front(self) -> Option[Any]:
        if self._mutable_borrow_id is None:
            self._mutable_borrow_id = _borrow_checker.borrow_mutable(self._value_id)
        
        borrow_validation = _borrow_checker._validate_borrow(
            self._value_id,
            _borrow_checker.BorrowType.MUTABLE
        )
        if not borrow_validation[0]:
            return None_()
        
        if len(self._data) == 0:
            return None_()
        
        item = self._data.pop(0)
        return Some(copy.deepcopy(item))
    
    def len(self) -> int:
        if self._borrow_id is None:
            self._borrow_id = _borrow_checker.borrow_immutable(self._value_id)
        return len(self._data)
    
    def is_empty(self) -> bool:
        return self.len() == 0
