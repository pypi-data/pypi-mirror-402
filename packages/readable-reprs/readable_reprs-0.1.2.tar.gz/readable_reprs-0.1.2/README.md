# readable-reprs
Patch the reprs of existing types so that the string representation is a valid Python expression.

This is really useful for REPL-like work and debugging because it allows you to log the program state and copy-paste
it into another Python program for experimentation. This is especially useful for when you have large nested objects.

Please file an issue if you notice anything else in the Python standard library that should have a readable repr.

## Version Support
Python versions 3.8 and above are supported and tested in CI. Lower versions may work too.

## Example Usage
Let's model Alice having two pets, a dog and a cat:

```python
from dataclasses import dataclass
from enum import Enum, auto


class Animal(Enum):
    DOG = auto()
    CAT = auto()
    BIRD = auto()


@dataclass
class Human:
    name: str
    pets: list[Animal]


if __name__ == '__main__':
    human = Human(name='Alice', pets=[])
    human.pets.append(Animal.DOG)
    human.pets.append(Animal.CAT)
    print(human)

```

Printing out Alice yields this string:

```
Human(name='Alice', pets=[<Animal.DOG: 1>, <Animal.CAT: 2>])
```

Which isn't particularly nice because it contains angled brackets, which aren't valid Python code.

Adding a `patch_reprs` call to the start of your program fixes this:

```python
from readable_reprs import patch_reprs

patch_reprs()

# ... as before ...
```

```
Human(name='Alice', pets=[Animal.DOG, Animal.CAT])
```

You can use this string as a valid Python expression to recreate the object in another Python program.
