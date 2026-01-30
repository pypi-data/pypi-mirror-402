[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![PyPI](https://img.shields.io/pypi/v/lazyscribe-joblib)](https://pypi.org/project/lazyscribe-joblib/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lazyscribe-joblib)](https://pypi.org/project/lazyscrib-joblib/) [![codecov](https://codecov.io/gh/lazyscribe/lazyscribe-joblib/graph/badge.svg?token=W5TPK7GX7G)](https://codecov.io/gh/lazyscribe/lazyscribe-joblib)

# Joblib-based artifact handling for lazyscribe

`lazyscribe-joblib` is a lightweight package that adds the following artifact handlers for `lazyscribe`:

* `joblib`

Any object that can be written with `joblib.dump` and read with `joblib.load` is compatible with this
handler. Note that we do persist the `joblib` version for runtime environment validation.
