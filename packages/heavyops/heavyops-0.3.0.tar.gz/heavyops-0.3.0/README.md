# heavyops

`heavyops` identifies performance bottlenecks related to specific bytecode instructions.

Use it to find redundant object allocations, unexpected side effects of closures, and other inefficiencies in your Python code.

The project is based on `sys.monitoring`.

## Installation

```bash
$ pip install heavyops
```

## Example use case: side effects of closures

When a variable is captured by a closure, Python creates a cell object to hold the variable. This can lead to performance overhead. By tracking `LOAD_DEREF` instructions, you can identify functions that use closures and refactor them if necessary. For example:

```python
class Foo:
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi

    def intersects(self, other):
        if isinstance(other, Foo):
            return self.lo < other.hi and other.lo < self.hi
        elif isinstance(other, list):
            # the following captures 'self' in a closure for the generator expression
            return any(self.intersects(item) for item in other)
        else:
            return False


for i in range(1000):
    Foo(1, 4).intersects(Foo(2, 5))
```

Even though the generator expression is not in a hot path, it captures `self`, leading to the creation of a cell object for `self` and the use of `LOAD_DEREF` instructions in the hot path:

```console
$ python3 -m heavyops example.py 
3,814 / 94,467 tracked instructions

COUNT    | INSTRUCTION
--------------------------------------------------
   2,662 | LOAD_DEREF
     512 | MAKE_FUNCTION
     ...

COUNT    | LOCATION
--------------------------------------------------
   1,000 | example.py:8 intersects LOAD_DEREF
   1,000 | example.py:8 intersects LOAD_DEREF
     ...
```

This can be fixed by avoiding the generator expression, for example by using a for loop:

```python
class Foo:
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi

    def intersects(self, other):
        if isinstance(other, Foo):
            return self.lo < other.hi and other.lo < self.hi
        elif isinstance(other, list):
            for item in other:
                if self.intersects(item):
                    return True
            return False
```

## Usage

After installation an executable `heavyops` is available. Simply run it with the target script and its arguments:

```console
heavyops [options] target_script.py [script_args...]
```

or as a module:

```console
python3 -m heavyops [options] target_script.py [script_args...]
```

By default, it will report the following instructions:

* `MAKE_FUNCTION`
* `BUILD_TUPLE`
* `BUILD_LIST`
* `BUILD_SET`
* `BUILD_MAP`
* `LOAD_DEREF`

You can customize the instructions to track using on or more `-i` / `--instructions` flags.

```bash
heavyops -i MAKE_FUNCTION -i BUILD_LIST my_app arg1 arg2
```

You can restrict tracking to specific files using the `-f` / `--file` flag:

```bash
heavyops -f 'specific_file.py' my_app arg1 arg2
```
