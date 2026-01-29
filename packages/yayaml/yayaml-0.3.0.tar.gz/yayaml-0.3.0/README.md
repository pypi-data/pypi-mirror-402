# `yayaml`

The `yayaml` package provides extensions to `ruamel.yaml` that allow creating some often-needed Python objects directly via YAML tags and making it easier to represent custom objects when writing YAML files.

yay 🥳


`yayaml` is used in the following projects:

* [paramspace](https://gitlab.com/blsqr/paramspace): for config-file-based grid search with deeply nested dicts
* [dantro](https://gitlab.com/utopia-project/dantro): for loading, processing and visualizing high-dimensional simulation output
* [utopya](https://gitlab.com/utopia-project/utopya): a versatile simulation framework


## Installation
First, create and/or enter a Python virtual environment in which you would like to install this package.

The package can then be installed using [pip]:

```bash
pip install yayaml
```


## Use
Loading and writing YAML files is easy:

```python
import yayaml as yay

# Loading and writing
yay.yaml.load("{foo: bar}")
yay.load_yml("path/to/file.yml")
yay.write_yml(dict(foo="bar"), path="path/to/output.yml")
```

The main feature of `yayaml` is to provide 40+ additional YAML tags for common operations, super-charing your YAML files.
For example:

```yaml
# Math operations
sum: !sum [1, 2, 3]           # 6
product: !prod [2, 3, 4]      # 24
power: !pow [2, 8]            # 256
expr: !expr 2**8 + 1          # 257

# Comparisons and logic
check: !gt [5, 3]             # true
all_true: !all [true, true]   # true
result: !if-else [!gt [5, 3], "yes", "no"]  # "yes"

# Strings
msg: !format ["{} + {} = {}", 1, 2, 3]  # "1 + 2 = 3"
csv: !join [", ", [a, b, c]]            # "a, b, c"

# Environment and paths
home: !env HOME                         # /home/user
config: !expanduser ~/.config/myapp     # /home/user/.config/myapp
path: !joinpath ["~", data, file.csv]   # ~/data/file.csv

# Numeric ranges (useful for configs)
params: !linspace [0, 1, 5]   # [0.0, 0.25, 0.5, 0.75, 1.0]
range: !arange [0, 10, 2]     # [0, 2, 4, 6, 8]
```

See the [documentation](https://yayaml.readthedocs.io) for the full list of YAML tags.
It is also easily possible to create custom constructors and representers using simple decorators.


## For developers
If you would like to develop for this project, installation should be done from a local `git clone` of the repository.
After having the project cloned, enter a virtual environment for development.

To then install the package (in editable mode), run:

```bash
cd yayaml
pip install -e ".[dev]"
```

Or, using [uv]:

```bash
cd yayaml
uv sync
```

This will include development-related dependencies (for tests and building of the documentation).

To automatically run [pre-commit][pre-commit] hooks, install the configured git hooks using `pre-commit install`.


### Running tests
Enter the virtual environment, then run [pytest]:

```bash
python -m pytest -v tests/ --cov=yayaml --cov-report=term-missing
```

### Building the documentation
```bash
cd doc
make doc
make linkcheck  # optional
make doctest    # optional
```

The documentation can then be found in [`doc/_build/html`](doc/_build/html/).

To automatically generate figures, set the `YAYAML_USE_TEST_OUTPUT_DIR` environment variable before invoking `make doc`.

```bash
export YAYAML_USE_TEST_OUTPUT_DIR=yes
```


## License
The `yayaml` package is open-source software licensed under BSD 2-clause, see [`LICENSE`](LICENSE).

### Copyright holders

- Yunus Sevinchan (*maintainer*)


[repository]: https://gitlab.com/blsqr/yayaml
[pip]: https://pip.pypa.io/en/stable/
[uv]: https://docs.astral.sh/uv/
[pytest]: https://pytest.org/
[pre-commit]: https://pre-commit.com
