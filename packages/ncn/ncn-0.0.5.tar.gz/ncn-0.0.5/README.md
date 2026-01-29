# ncn (Nominal Composition Notation)

Use cnc to name, parse and find nominal composition notation.

## name

```python
from ncn import name

print(name(Ti='balance', Al=6, V=4))
# Output: Ti6Al4V
```

## parse

```python
from ncn import parse

print(parse('Ti-6Al-4V', balance=True))
# Output: {'Al': 6.0, 'V': 4.0, 'Ti': 90.0}
``` 

## find

```python
from ncn import find

print(find('Titanium Ti-8Al-1Mo-1V (Ti-8-1-1) Annealed 8 hr at 790°C (1450°F)'))
# Output: ['Ti-8Al-1Mo-1V']
```