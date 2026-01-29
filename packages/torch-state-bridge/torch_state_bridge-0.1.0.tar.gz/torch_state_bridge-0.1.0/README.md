# torch-state-bridge

**torch-state-bridge** is a powerful and flexible library for transforming PyTorch `state_dict` keys using **rule-based mappings**, **regex captures**, **arithmetic expressions**, and **composable transformation pipelines**.

It is designed to make model weight conversion easy across:

* different architectures
* renamed modules
* framework migrations
* checkpoints with inconsistent naming

---

## ✨ Features

* 🔁 **Rule-based key transformation** using readable patterns
* 🔢 **Arithmetic expressions** in key mappings
* 🔄 **Forward & reverse mappings**
* 🧩 **Composable pipelines** for complex workflows
* 🌳 **Nested dictionary support**
* 👀 **Preview & diff tools** before applying changes
* 🚫 **Collision detection**
* ♻️ **Reusable rule templates**
* ⚡ **LRU-cached transformations for performance**

---

## 📦 Installation

```bash
pip install torch-state-bridge
```

Or install from source:

```bash
git clone https://github.com/yourname/torch-state-bridge.git
cd torch-state-bridge
pip install -e .
```

---

## 🚀 Quick Start

```python
from torch_state_bridge import state_bridge

state_dict = {
    "layer.0.weight": weight_tensor,
    "layer.0.bias": bias_tensor,
}

rules = """
layer.{n}.weight, block.{n}.weight
layer.{n}.bias,   block.{n}.bias
"""

new_state_dict = state_bridge(state_dict, rules)
```

Result:

```text
layer.0.weight → block.0.weight
layer.0.bias   → block.0.bias
```

---

## 🧠 Rule Syntax

### Basic Rule

```
source_pattern, destination_pattern
```

### Capture Groups

```
layer.{n}.weight, block.{n}.weight
```

* `{n}` captures numeric values
* Captures are reusable in destination

### Arithmetic Expressions

```
layer.{n}.weight, block.{(n + 1)}.weight
```

Supported operators:

* `+  -  *  /  //  %  **`

Arithmetic is **safe and sandboxed**.

---

## 🔄 Reverse Rules

```python
state_bridge(state_dict, rules, reverse=True)
```

> ⚠️ Reverse mode is **not allowed** for rules with arithmetic expressions.

---

## 🧪 Preview Before Applying

```python
from torch_state_bridge import state_bridge_preview

mapping, unchanged, collisions = state_bridge_preview(state_dict, rules)
```

* `mapping`: old → new keys
* `unchanged`: keys not affected
* `collisions`: conflicting output keys

---

## 🖨 Pretty Diff Output

```python
from torch_state_bridge import print_diff

print_diff(state_dict, rules)
```

Example output:

```
============================================================
TRANSFORMATION PREVIEW
============================================================

📝 CHANGES:
  layer.0.weight -> block.0.weight
  layer.0.bias   -> block.0.bias

✓ UNCHANGED: 12 keys
============================================================
```

---

## 🧩 Batch Operations Pipeline

Apply multiple transformations sequentially:

```python
from torch_state_bridge import state_bridge_batch

ops = [
    {"type": "prefix", "add": "model."},
    {"type": "rules", "rules_text": "layer.{n}, block.{n}"},
    {"type": "remove_prefix", "remove": "model."}
]

new_sd = state_bridge_batch(state_dict, ops)
```

### Supported Batch Operations

* `prefix`
* `suffix`
* `remove_prefix`
* `remove_suffix`
* `replace`
* `rules`
* `filter`

---

## 🌳 Nested State Dicts

Handles deeply nested dictionaries:

```python
from torch_state_bridge import state_bridge_nested

nested = {
    "model": {
        "layer1": {
            "weight": tensor
        }
    }
}

rules = "model.layer1, model.block1"
new_nested = state_bridge_nested(nested, rules)
```

---

## 🔗 Rule Chains

Chain multiple rule engines with tracing:

```python
from torch_state_bridge import RuleChain

chain = (
    RuleChain()
    .add("rename layers", "layer.{n}, block.{n}")
    .add("add prefix", "{key}, model.{key}")
)

new_sd = chain.apply(state_dict, trace=True)
```

---

## 🧱 Rule Templates

Reusable built-in templates:

```python
from torch_state_bridge import RuleTemplate

new_sd = RuleTemplate.apply_template(
    state_dict,
    "huggingface_to_timm"
)
```

### Available Templates

* `huggingface_to_timm`
* `pytorch_to_tensorflow`
* `add_prefix`
* `remove_prefix`

You can also expand templates manually:

```python
rules = RuleTemplate.expand_template("add_prefix", prefix="model")
```

---

## 🔍 Rule Validation

```python
from torch_state_bridge import validate_rules

errors = validate_rules(rules_text)
if errors:
    print(errors)
```

---

## 📐 Range Expansion

```python
from torch_state_bridge import expand_range_rules

rules = "layer.{0..2}.weight, block.{0..2}.weight"
print(expand_range_rules(rules))
```

---

## 🔁 Inverse Rule Generation

```python
from torch_state_bridge import generate_inverse_rules

inverse = generate_inverse_rules("layer.{n}, block.{n}")
```

---

## ⚠️ Collision Detection

By default, key collisions raise an error:

```python
state_bridge(state_dict, rules, detect_collision=True)
```

Disable if needed:

```python
state_bridge(state_dict, rules, detect_collision=False)
```

---

## 🛡 Safety

* No `eval`
* AST-based math evaluation
* Strict regex capture rules
* Safe integer-only arithmetic

---

## 📄 License

MIT License © 2026 Your Name

---

## 🤝 Contributing

Contributions are welcome!

* Bug reports
* Feature requests
* New rule templates
* Documentation improvements

---

## 🌟 Why torch-state-bridge?

Because **renaming model weights should be declarative, safe, and composable**.

If you work with:

* model conversion
* checkpoint surgery
* research code cleanup
* framework interoperability

**torch-state-bridge** is built for you.

---

Happy bridging 🚀
