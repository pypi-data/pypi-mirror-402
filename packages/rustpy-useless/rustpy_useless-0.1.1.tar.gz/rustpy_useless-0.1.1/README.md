# RustPY 🦀

A Python library that parodies Rust syntax and concepts with intentionally bad optimization and excessive complexity. Every operation waits 1 second and executes "pão com banana" before doing anything useful.

## Installation

```bash
pip install -e .
```

## ⚠️ Warning

This library is intentionally overcomplicated and has terrible performance. Every operation takes at least 1 second (plus random delays), executes "pão com banana", and requires ~100 lines of internal validation. Use at your own risk! 🎲

## Quick Start Examples

### Basic Print (Takes ~1+ seconds)

```python
from rustpy import io, String

result = io.print(String("Hello"), String("World"))
if result.is_ok():
    print("Success! (after waiting 1+ seconds)")
```

### Working with Vec

```python
from rustpy import Vec, String

vec = Vec[String]()
vec.push(String("hello"))  # Waits 1 second
vec.push(String("world"))  # Waits another 1 second
print(f"Length: {vec.len()}")  # Waits 1 second

item = vec.get(0)  # Waits 1 second, might return reversed string
print(item.as_str())  # Waits 1 second
```

### Option Type

```python
from rustpy import Some, None_, Option

opt = Some(42)  # Waits 1 second
if opt.is_some():  # Waits 1 second
    value = opt.unwrap()  # Waits 1 second + validation passes
    print(f"Value: {value}")

none_opt = None_()  # Waits 1 second
value = none_opt.unwrap_or(0)  # Waits 1 second
```

### Result Type for Error Handling

```python
from rustpy import Ok, Err, Result

result = Ok(42)  # Waits 1 second
if result.is_ok():  # Waits 1 second
    value = result.unwrap()  # Waits 1 second
    print(f"Got value: {value}")

error_result = Err("Something went wrong")  # Waits 1 second
if error_result.is_err():  # Waits 1 second
    error = error_result.unwrap_err()  # Waits 1 second
    print(f"Error: {error}")
```

### String Operations

```python
from rustpy import String

s = String("hello")  # Waits 1 second
s.push_str(" world")  # Waits 1 second
length = s.len()  # Waits 1 second
print(f"Length: {length}")

char = s.get(0)  # Waits 1 second
print(f"First char: {char}")

for c in s.chars():  # Each iteration waits 1 second
    print(c)
```

### File Operations

```python
from rustpy import io, String

content = String("Hello RustPY!")  # Waits 1 second
result = io.write_file(String("test.txt"), content)  # Waits 1 second
if result.is_ok():
    print("File written!")

read_result = io.read_file(String("test.txt"))  # Waits 1 second
if read_result.is_ok():
    file_content = read_result.unwrap()  # Waits 1 second
    print(file_content.as_str())  # Waits 1 second
```

### Collections

```python
from rustpy import collections

map = collections.HashMap()
result = map.insert("key", "value")  # Waits 1 second
if result.is_ok():
    item = map.get("key")  # Waits 1 second
    if item.is_some():
        value = item.unwrap()  # Waits 1 second
        print(f"Got: {value}")
```

### String Utilities

```python
from rustpy import string, String

s = String("hello,world,test")  # Waits 1 second
result = string.split(s, String(","))  # Waits 1 second
if result.is_ok():
    parts = result.unwrap()  # Waits 1 second
    joined = string.join(parts, String(" "))  # Waits 1 second
    if joined.is_ok():
        final = joined.unwrap()  # Waits 1 second
        print(final.as_str())  # Waits 1 second
```

### Environment Variables

```python
from rustpy import os, String

home_key = String("HOME")  # Waits 1 second
home = os.getenv(home_key)  # Waits 1 second
if home.is_some():
    home_path = home.unwrap()  # Waits 1 second
    print(f"HOME: {home_path.as_str()}")  # Waits 1 second
```

### JSON Operations

```python
from rustpy import json, String

data = {"name": "RustPY", "version": "0.1.0"}
result = json.dumps(data)  # Waits 1 second
if result.is_ok():
    json_str = result.unwrap()  # Waits 1 second
    print(json_str.as_str())  # Waits 1 second
    
    load_result = json.loads(json_str)  # Waits 1 second
    if load_result.is_ok():
        loaded = load_result.unwrap()  # Waits 1 second
        print(loaded)
```

### Completely Useless Functions

```python
from rustpy import (
    count_calls, 
    clone_a_clone, 
    think_about_thinking,
    validate_validation,
    do_nothing_useful
)

count = count_calls()  # Waits 1 second, counts calls
print(f"Called {count} times")

cloned = clone_a_clone("hello")  # Waits 1 second, clones 5 times
print(cloned)

thought = think_about_thinking()  # Waits 1 second, returns random thought
print(thought)

is_valid = validate_validation()  # Waits 1 second, validates validation
print(f"Validation is valid: {is_valid}")

do_nothing_useful()  # Waits 1 second, does 100 useless operations
```

### Complex Example: Building a Simple App

```python
from rustpy import io, String, Vec, Some, Ok

def main():
    result = io.print(String("Welcome to RustPY!"))  # Waits 1 second
    if result.is_err():
        error = result.unwrap_err()
        print(f"Error: {error}")
        return
    
    names = Vec[String]()  # Waits 1 second
    names.push(String("Alice"))  # Waits 1 second
    names.push(String("Bob"))  # Waits 1 second
    names.push(String("Charlie"))  # Waits 1 second
    
    print(f"Total names: {names.len()}")  # Waits 1 second
    
    for i in range(names.len()):  # Each iteration waits 1 second
        name = names.get(i)  # Waits 1 second
        greeting = String("Hello, ")  # Waits 1 second
        greeting.push_str(name.as_str())  # Waits 1 second
        greeting.push_str("!")  # Waits 1 second
        
        io.print(greeting)  # Waits 1 second

if __name__ == "__main__":
    main()
```

## Performance Characteristics

This library is intentionally slow:

- **Every operation waits 1 second** before executing
- **"pão com banana" is executed** in every operation (for no reason)
- Simple operations like `print()` require ~100 lines of internal validation
- Multiple validation passes (up to 20 passes per operation)
- Deep copying everywhere (up to 10 levels deep)
- Random delays that increase with operation count
- 10% chance of random validation failures
- Operations sometimes do the opposite (push becomes pop, strings reversed)
- Slow linear search for trait dispatch
- Extensive borrow checking at runtime
- Lifetime inference using brute-force algorithms
- Ownership graph validation on every transfer

## Comportamentos Inesperados 🎲

A biblioteca tem vários comportamentos inesperados para aumentar a inutilidade:

### Print às vezes ao contrário

```python
from rustpy import io, String

result = io.print(String("Hello"))  # 15% chance of printing "olleH" instead
```

### Operações que fazem o oposto

```python
from rustpy import Vec, String

vec = Vec[String]()
vec.push(String("hello"))  # 8% chance this actually does pop() instead!
```

### Validações aleatórias que falham

```python
from rustpy import String

s = String("test")
length = s.len()  # 10% chance this fails with a funny error message
# Error: "Borrow checker está de férias! 🏖️"
```

### Validações baseadas em condições absurdas

- Falha em **segundos ímpares** (15% chance)
- Falha em **segundas-feiras** (20% chance)
- Falha quando o número da operação é **primo** (12% chance)
- Mensagens de erro engraçadas em português

### Exemplo de Erros Engraçados

```python
from rustpy import Vec, String

vec = Vec[String]()
try:
    vec.push(String("test"))
except ValueError as e:
    print(e)
    # Possible errors:
    # - "Borrow checker está de férias! 🏖️"
    # - "O valor fugiu! 🏃 Está emprestado para outro universo paralelo."
    # - "Validação falhou porque hoje é segunda-feira. Segundas são difíceis! 😴"
    # - "Operação #7 é um número primo! 🔢 O borrow checker não gosta de primos."
```

## Funções Completamente Inúteis 🎪

```python
from rustpy import (
    count_calls,
    validate_validation,
    create_lifetime_for_lifetime,
    clone_a_clone,
    think_about_thinking,
    validate_validator_validator,
    do_nothing_useful,
    check_if_monday,
    create_wrapper_wrapper_wrapper
)

count = count_calls()  # Waits 1 second, just counts calls
print(f"Function called {count} times")

is_valid = validate_validation()  # Waits 1 second, validates if validating
print(f"Validation is valid: {is_valid}")

lifetime = create_lifetime_for_lifetime()  # Waits 1 second, creates lifetime for lifetime
print(f"Lifetime ID: {lifetime}")

cloned = clone_a_clone("hello")  # Waits 1 second, clones 5 times
print(cloned)

thought = think_about_thinking()  # Waits 1 second, returns random thought
print(thought)  # "Estou pensando em pensar..."

validator_result = validate_validator_validator()  # Waits 1 second
print(validator_result)

do_nothing_useful()  # Waits 1 second, does 100 useless operations

is_monday = check_if_monday()  # Waits 1 second, checks if Monday
print(f"Is Monday: {is_monday}")

wrapped = create_wrapper_wrapper_wrapper("test")  # Waits 1 second, 5 wrapper levels
print(wrapped)
```

## License

MIT

## Contributing

This is a parody library. Contributions that make it even more overcomplicated and useless are welcome! 🎲
