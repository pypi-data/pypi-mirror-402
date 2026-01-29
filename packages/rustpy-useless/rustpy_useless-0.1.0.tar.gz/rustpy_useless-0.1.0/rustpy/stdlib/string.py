import uuid
import time
import copy
from typing import Any, List
from rustpy.core.borrow_checker import BorrowChecker
from rustpy.core.ownership import OwnershipTracker
from rustpy.core.lifetimes import LifetimeManager
from rustpy.types.string import String
from rustpy.types.option import Option, Some, None_
from rustpy.types.result import Result, Ok, Err
from rustpy.types.vec import Vec

_borrow_checker = BorrowChecker()
_ownership_tracker = OwnershipTracker()
_lifetime_manager = LifetimeManager()

def split(s: String, delimiter: String) -> Result[Vec[String], str]:
    s_value_id = _borrow_checker.register_value(s)
    delimiter_value_id = _borrow_checker.register_value(delimiter)
    
    s_owner_id = _ownership_tracker.register_owner()
    delimiter_owner_id = _ownership_tracker.register_owner()
    
    s_value_id, _ = _ownership_tracker.register_value(s, s_owner_id)
    delimiter_value_id, _ = _ownership_tracker.register_value(delimiter, delimiter_owner_id)
    
    s_lifetime_id = _lifetime_manager.create_lifetime()
    delimiter_lifetime_id = _lifetime_manager.create_lifetime()
    
    _lifetime_manager.associate_value(s_value_id, s_lifetime_id)
    _lifetime_manager.associate_value(delimiter_value_id, delimiter_lifetime_id)
    
    s_lifetime_validation = _lifetime_manager.validate_lifetime(s_lifetime_id)
    if not s_lifetime_validation[0]:
        return Err(f"S lifetime validation failed: {s_lifetime_validation[1]}")
    
    delimiter_lifetime_validation = _lifetime_manager.validate_lifetime(delimiter_lifetime_id)
    if not delimiter_lifetime_validation[0]:
        return Err(f"Delimiter lifetime validation failed: {delimiter_lifetime_validation[1]}")
    
    s_borrow_id = _borrow_checker.borrow_immutable(s_value_id)
    delimiter_borrow_id = _borrow_checker.borrow_immutable(delimiter_value_id)
    
    s_borrow_validation = _borrow_checker._validate_borrow(
        s_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not s_borrow_validation[0]:
        return Err(f"S borrow validation failed: {s_borrow_validation[1]}")
    
    delimiter_borrow_validation = _borrow_checker._validate_borrow(
        delimiter_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not delimiter_borrow_validation[0]:
        return Err(f"Delimiter borrow validation failed: {delimiter_borrow_validation[1]}")
    
    s_str = s.as_str()
    delimiter_str = delimiter.as_str()
    
    parts = s_str.split(delimiter_str)
    result_vec = Vec[String]()
    
    for part in parts:
        part_string = String(part)
        result_vec.push(part_string)
    
    return Ok(result_vec)

def join(strings: Vec[String], separator: String) -> Result[String, str]:
    strings_value_id = _borrow_checker.register_value(strings)
    separator_value_id = _borrow_checker.register_value(separator)
    
    strings_owner_id = _ownership_tracker.register_owner()
    separator_owner_id = _ownership_tracker.register_owner()
    
    strings_value_id, _ = _ownership_tracker.register_value(strings, strings_owner_id)
    separator_value_id, _ = _ownership_tracker.register_value(separator, separator_owner_id)
    
    strings_lifetime_id = _lifetime_manager.create_lifetime()
    separator_lifetime_id = _lifetime_manager.create_lifetime()
    
    _lifetime_manager.associate_value(strings_value_id, strings_lifetime_id)
    _lifetime_manager.associate_value(separator_value_id, separator_lifetime_id)
    
    strings_lifetime_validation = _lifetime_manager.validate_lifetime(strings_lifetime_id)
    if not strings_lifetime_validation[0]:
        return Err(f"Strings lifetime validation failed: {strings_lifetime_validation[1]}")
    
    separator_lifetime_validation = _lifetime_manager.validate_lifetime(separator_lifetime_id)
    if not separator_lifetime_validation[0]:
        return Err(f"Separator lifetime validation failed: {separator_lifetime_validation[1]}")
    
    strings_borrow_id = _borrow_checker.borrow_immutable(strings_value_id)
    separator_borrow_id = _borrow_checker.borrow_immutable(separator_value_id)
    
    strings_borrow_validation = _borrow_checker._validate_borrow(
        strings_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not strings_borrow_validation[0]:
        return Err(f"Strings borrow validation failed: {strings_borrow_validation[1]}")
    
    separator_borrow_validation = _borrow_checker._validate_borrow(
        separator_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not separator_borrow_validation[0]:
        return Err(f"Separator borrow validation failed: {separator_borrow_validation[1]}")
    
    separator_str = separator.as_str()
    parts: List[str] = []
    
    for i in range(strings.len()):
        string_item = strings.get(i)
        parts.append(string_item.as_str())
    
    result_str = separator_str.join(parts)
    result_string = String(result_str)
    
    return Ok(result_string)

def trim(s: String) -> Result[String, str]:
    s_value_id = _borrow_checker.register_value(s)
    s_owner_id = _ownership_tracker.register_owner()
    s_value_id, _ = _ownership_tracker.register_value(s, s_owner_id)
    s_lifetime_id = _lifetime_manager.create_lifetime()
    _lifetime_manager.associate_value(s_value_id, s_lifetime_id)
    
    s_lifetime_validation = _lifetime_manager.validate_lifetime(s_lifetime_id)
    if not s_lifetime_validation[0]:
        return Err(f"S lifetime validation failed: {s_lifetime_validation[1]}")
    
    s_borrow_id = _borrow_checker.borrow_immutable(s_value_id)
    s_borrow_validation = _borrow_checker._validate_borrow(
        s_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not s_borrow_validation[0]:
        return Err(f"S borrow validation failed: {s_borrow_validation[1]}")
    
    s_str = s.as_str()
    trimmed_str = s_str.strip()
    result_string = String(trimmed_str)
    
    return Ok(result_string)

def to_uppercase(s: String) -> Result[String, str]:
    s_value_id = _borrow_checker.register_value(s)
    s_owner_id = _ownership_tracker.register_owner()
    s_value_id, _ = _ownership_tracker.register_value(s, s_owner_id)
    s_lifetime_id = _lifetime_manager.create_lifetime()
    _lifetime_manager.associate_value(s_value_id, s_lifetime_id)
    
    s_lifetime_validation = _lifetime_manager.validate_lifetime(s_lifetime_id)
    if not s_lifetime_validation[0]:
        return Err(f"S lifetime validation failed: {s_lifetime_validation[1]}")
    
    s_borrow_id = _borrow_checker.borrow_immutable(s_value_id)
    s_borrow_validation = _borrow_checker._validate_borrow(
        s_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not s_borrow_validation[0]:
        return Err(f"S borrow validation failed: {s_borrow_validation[1]}")
    
    s_str = s.as_str()
    upper_str = s_str.upper()
    result_string = String(upper_str)
    
    return Ok(result_string)

def to_lowercase(s: String) -> Result[String, str]:
    s_value_id = _borrow_checker.register_value(s)
    s_owner_id = _ownership_tracker.register_owner()
    s_value_id, _ = _ownership_tracker.register_value(s, s_owner_id)
    s_lifetime_id = _lifetime_manager.create_lifetime()
    _lifetime_manager.associate_value(s_value_id, s_lifetime_id)
    
    s_lifetime_validation = _lifetime_manager.validate_lifetime(s_lifetime_id)
    if not s_lifetime_validation[0]:
        return Err(f"S lifetime validation failed: {s_lifetime_validation[1]}")
    
    s_borrow_id = _borrow_checker.borrow_immutable(s_value_id)
    s_borrow_validation = _borrow_checker._validate_borrow(
        s_value_id,
        _borrow_checker.BorrowType.IMMUTABLE
    )
    if not s_borrow_validation[0]:
        return Err(f"S borrow validation failed: {s_borrow_validation[1]}")
    
    s_str = s.as_str()
    lower_str = s_str.lower()
    result_string = String(lower_str)
    
    return Ok(result_string)
