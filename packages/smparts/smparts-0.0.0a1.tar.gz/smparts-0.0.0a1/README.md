## SMparts

This project is bootstrapped from the PyPA template:
https://github.com/pypa/sampleproject/

SMparts is a lightweight Python package collecting small, carefully designed building blocks for composing **state machines** and **token-driven transducers**.

The goal is to provide minimal yet precise components with clear semantics, formal-style documentation, and executable examples.

---

## Repository layout

Core package:
- [src/smparts/__init__.py](src/smparts/__init__.py)
- [src/smparts/sentinels.py](src/smparts/sentinels.py)
- [src/smparts/reset_buffer.py](src/smparts/reset_buffer.py)

Tests:
- [tests/test_sentinels.py](tests/test_sentinels.py)
- [tests/test_reset_buffer.py](tests/test_reset_buffer.py)

Examples:
- [examples/try_reset_buffer.py](examples/try_reset_buffer.py)

Docs:
- [docs/reset_buffer.md](docs/reset_buffer.md)

---

## Package testing

Activate a conda environment, then install the package in editable mode:

```
pip install -e '.[dev,test]'
```

Run tests:
```
pytest -q
```


