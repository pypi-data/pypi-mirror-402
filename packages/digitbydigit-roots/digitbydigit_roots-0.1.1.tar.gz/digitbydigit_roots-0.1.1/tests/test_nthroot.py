
---

## 7. Tests (very important for credibility)

### `tests/test_nthroot.py`

```python
from digitbydigit_roots import NthRoot

def test_square():
    r = NthRoot(144, 2)
    assert r.root() == 12

def test_non_square():
    r = NthRoot(145, 2, digits=5)
    assert float(r.root())**2 < 145.00001

def test_perfect_power():
    r = NthRoot(256, 4)
    assert r.root() == 4
