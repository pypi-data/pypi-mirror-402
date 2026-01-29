# Saboteur

[![PyPI version](https://badge.fury.io/py/saboteur.svg)](https://badge.fury.io/py/saboteur)

A simple and extensible data mutation library for Chaos Engineering in Python.

## 🤔 What is Saboteur?

**Saboteur** is a lightweight Python library designed to test the robustness of your data processing logic. It helps you practice Chaos Engineering by intentionally and randomly injecting faulty or unexpected data into your system.

By "attacking" your data with various mutation strategies, Saboteur helps you uncover hidden bugs, handle edge cases gracefully, and build more resilient applications.

## ✨ Key Features

-   **Simple API**: Get started in seconds with the intuitive `.attack()` method.
-   **Randomized Mutations**: Automatically selects a random field and applies a random, applicable mutation to simulate real-world unpredictability.
-   **Extensible**: Easily create and add your own custom mutation strategies to fit your specific needs.
-   **Lightweighted Dependencies**: A pure Python library that can be dropped into any project without extra baggage.

## 💾 Installation

Install Saboteur directly from PyPI:

```bash
# pip
pip install saboteur

# poetry
pip install poetry && poetry add saboteur
```

## 🚀 Quick Start

Using Saboteur is straightforward. Import the `Saboteur` class and the desired strategies, then call the `attack` method on your data.

```python
from saboteur.application.facade import Saboteur
from saboteur.infrastructure.strategies.injections import NullInjectionStrategy
from saboteur.infrastructure.strategies.flippings import TypeFlipStrategy
from saboteur.domain.mutation.configs import MutationConfig

# 1. Define the strategies you want to use
strategies = [
    NullInjectionStrategy(),
    TypeFlipStrategy(),
]

# 2. Set configuration what you want
config = MutationConfig(
    strategies=strategies,
    apply_all_strategies=True,
)

# 3. Initialize Saboteur with your configuration
saboteur = Saboteur(config=config)

# 4. Prepare your data
mock_data = {
    "user_id": 12345,
    "username": "test_user",
    "is_active": True,
    "score": 987
}

# 5. Attack the data!
# Saboteur will randomly pick one key (e.g., "user_id") and apply one
# applicable strategy (e.g., TypeFlipStrategy).
mutated_data = saboteur.attack(mock_data)

# Example output: {'user_id': '12345', 'username': 'test_user', ...}
# Or: {'user_id': 12345, 'username': None, ...}
print(mutated_data)
```

## 🛠️ Available Strategies

Saboteur comes with a set of built-in strategies to get you started.

### `NullInjectionStrategy`

Replaces the original value of a field with `None`. This is useful for testing how your code handles missing or null data.

-   **Applicable when**: The original value is not `None`.
-   **Mutation**: `original_value` -> `None`

### `TypeFlipStrategy`

Changes the data type of a field. Currently supports `int` to `str` and `str` to `int` conversions. This helps test for `TypeError` exceptions and weak typing issues.

-   **Applicable when**: The original value is an `int` or a `str`.
-   **Mutation**:
    -   `int` -> `str` (e.g., `123` -> `'123'`)
    -   `str` -> `int` (e.g., `'456'` -> `456`). If the string is not a digit, it returns `-1`.

## ✍️ Creating a Custom Strategy

You can easily create your own strategies by inheriting from `MutationStrategy` and implementing two methods: `is_applicable` and `apply`.

Here's an example of a `BooleanFlipStrategy` that flips `True` to `False` and vice-versa.

```python
# custom_strategies.py
from typing import Any
from saboteur.domain.mutation.strategies import MutationStrategy
from saboteur.domain.mutation.contexts import MutationContext
from saboteur.domain.mutation.configs import MutationConfig

class BooleanFlipStrategy(MutationStrategy):
    """Flips a boolean value."""
    def is_applicable(self, context: MutationContext) -> bool:
        # This strategy only applies to boolean types
        return isinstance(context.original_value, bool)

    def apply(self, context: MutationContext) -> Any:
        # The mutation logic is simple: flip the boolean
        return not context.original_value

# You can then use it with Saboteur:
strategies = [
    BooleanFlipStrategy(),
    # ... other strategies
]

config = MutationConfig(
    strategies=strategies,
    ... # other options
)

saboteur = Saboteur(config=config)
```

## 🤝 Contributing

Contributions are welcome! Whether it's adding new strategies, improving documentation, or fixing bugs, please feel free to open an issue or submit a pull request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 🗺️ Roadmap

Saboteur is currently focused on data mutation, but we plan to expand its capabilities. Future versions will include logic for **API load testing**, allowing you to simulate heavy traffic and test the performance and stability of your endpoints under stress.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
