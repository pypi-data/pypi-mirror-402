## Typed Envs

typed_envs is used to create specialized `EnvironmentVariable` objects that behave exactly the same as any other instance of the `typ` used to create them.

typed_envs is used for:
    - defining your envs in a readable, user friendly way
    - enhancing type hints for the returned instances
    - enhancing __repr__ of the returned instance with extra contextual information

In the example below, `some_var` can be used just like as any other `int` object.

```
import typed_envs
some_var = typed_envs.create_env("SET_WITH_THIS_ENV", int, 10)
>>> isinstance(some_var, int)
True
>>> isinstance(some_var, EnvironmentVariable)
True
```

There are only 2 differences between `some_var` and `int(10)`:
    - `some_var` will properly type check as an instance of both `int` and `EnvironmentVariable`
    - `some_var.__repr__()` will include contextual information about the `EnvironmentVariable`.

```
>>> some_var
<EnvironmentVariable[name=`SET_WITH_THIS_ENV`, type=int, default_value=10, current_value=10, using_default=True]>
>>> str(some_var)
"10"
>>> some_var + 5
15
>>> 20 / some_var
2
```

### Mypy plugin

Mypy cannot natively model the dynamic subclass created by typed_envs. If you
want mypy to treat `EnvironmentVariable[T]` as having the methods and attributes
of both `EnvironmentVariable` and its underlying `T` (including for
`create_env(...)` and `EnvVarFactory.create_env(...)`), enable the plugin:

```
[mypy]
plugins = typed_envs.mypy_plugin
```

For `pyproject.toml` users:

```
[tool.mypy]
plugins = ["typed_envs.mypy_plugin"]
```

The plugin synthesizes a mypy-only class that inherits from both
`EnvironmentVariable` and the underlying type, so you can call methods from
either side without casts. It also preserves unions, optionals, and common
typing constructs like `Annotated`, `TypedDict`, and `Literal`.
