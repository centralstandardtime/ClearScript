# ClearScript

[![CI](https://github.com/centralstandardtime/ClearScript/workflows/CI/badge.svg)](https://github.com/centralstandardtime/ClearScript/actions)

A C-styled language that compiles to InfiltrationEngine's StateScript.

## Installation

```bash
pip install -e .
```

## Usage

### Compile a file

```bash
clearscript compile input.cst -o output.ss
```

### Example

**input.cst:**
```c
int x = 10;

function test() {
    x++;
}

test();
kill();
```

**Compiles to:**
```
INIT x 10

GOTO _main

:test
INC x
RETURN

:_main
CALL test
KILL
```

### RAW Blocks

Insert StateScript directly using `raw { }`:

```c
int count = 0;

raw {
    SHUFFLE Output 12345 A B C D
    GUID RandomID
}

count++;
```

## Language Features

- Variables: `int`, `float`
- **Arrays**: `int[] arr = [1, 2, 3]`, array indexing `arr[i]`
- **Const**: `const int MAX = 100`
- Functions with parameters
- Control flow: `if/else`, `while`, **`for` loops**, **`switch/case`**
- **Ternary operator**: `x = (a > b) ? a : b`
- **Classes/Structs**: `class Player { int health; method init() { ... } }` (parsing only)
- Labels and `goto`
- Built-in commands: `wait()`, `spawnbot()`, `moveto()`, `animate()`, `delete()`, `kill()`
- Stack operations: `push()`, `pop()`, `peek()`, `set()`
- RAW blocks for direct StateScript

## Examples

See [`examples/`](./examples) directory.

## License

CC BY-NC-SA 4.0
