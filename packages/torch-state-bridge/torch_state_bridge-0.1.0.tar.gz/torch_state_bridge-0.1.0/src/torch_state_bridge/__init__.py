"""
torch-state-bridge: A powerful library for transforming PyTorch state dict keys
with rule-based mappings, arithmetic operations, and advanced transformations.

Author: Jenil Sheth
"""

import re
import ast
import operator
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Callable, Any, Tuple, Set

__all__ = [
    'state_bridge',
    'state_bridge_batch',
    'state_bridge_nested',
    'state_bridge_preview',
    'print_diff',
    'RuleEngine',
    'RuleChain',
    'RuleTemplate',
    'Rule',
    'parse_rules',
    'expand_range_rules',
    'generate_inverse_rules',
    'validate_rules',
]

logger = logging.getLogger(__name__)


# ==================== SAFE MATH EVAL ==================== #

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def eval_math_expr(expr: str) -> int:
    """
    Safely evaluate mathematical expressions with integers.
    
    Args:
        expr: Mathematical expression string (e.g., "10 + 5", "n * 2")
        
    Returns:
        Evaluated integer result
        
    Raises:
        ValueError: If expression is invalid or contains division by zero
        
    Examples:
        >>> eval_math_expr("10 + 5")
        15
        >>> eval_math_expr("3 * 4")
        12
    """
    if not expr or not expr.strip():
        raise ValueError("Empty expression")
    
    try:
        def _eval(n):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return int(n.value)
            if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_OPS:
                left, right = _eval(n.left), _eval(n.right)
                # Division by zero check
                if isinstance(n.op, (ast.FloorDiv, ast.Mod)) and right == 0:
                    raise ValueError("Division by zero")
                result = _ALLOWED_OPS[type(n.op)](left, right)
                return int(result)
            if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_OPS:
                return _ALLOWED_OPS[type(n.op)](_eval(n.operand))
            raise ValueError(f"Invalid operation: {type(n).__name__}")

        return _eval(ast.parse(expr, mode="eval").body)
    except SyntaxError as e:
        raise ValueError(f"Invalid syntax in expression: {expr}") from e


# ==================== RULE CORE ==================== #

@dataclass(frozen=True, slots=True)
class Rule:
    """
    A single transformation rule with regex pattern and transform function.
    
    Attributes:
        regex: Compiled regex pattern to match keys
        transform: Function to transform matched keys
    """
    regex: re.Pattern
    transform: Callable[[re.Match], str]
    
    def __repr__(self) -> str:
        return f"Rule(pattern={self.regex.pattern!r})"


class RuleEngine:
    """
    Engine for applying multiple transformation rules to keys.
    
    Args:
        rules: List of Rule objects to apply
        debug: If True, log transformation steps
        cache_size: Size of LRU cache for transformed keys
    """
    
    def __init__(self, rules: List[Rule], debug: bool = False, cache_size: int = 128):
        self.rules = rules
        self.debug = debug
        self._apply_cached = lru_cache(maxsize=cache_size)(self._apply_impl)

    def _apply_impl(self, key: str) -> str:
        """Internal implementation of apply."""
        for r in self.rules:
            key = r.regex.sub(r.transform, key)
        return key
    
    def apply(self, key: str) -> str:
        """
        Apply all rules to transform a key.
        
        Args:
            key: Input key string
            
        Returns:
            Transformed key string
        """
        original = key
        
        if self.debug:
            key = original
            for i, rule in enumerate(self.rules):
                new_key = rule.regex.sub(rule.transform, key)
                if new_key != key:
                    logger.debug(f"Rule {i}: {key} -> {new_key}")
                key = new_key
            
            if key != original:
                logger.info(f"Final: {original} -> {key}")
            return key
        else:
            return self._apply_cached(key)


# ==================== RULE COMPILER ==================== #

_CAPTURE = re.compile(r"\{(\w+)\}")
_MATH = re.compile(r"\{\(([^()]+)\)\}")


def _compile(src: str, dst: str, *, reverse: bool) -> Rule:
    """
    Compile a transformation rule from source and destination patterns.
    
    Args:
        src: Source pattern with {var} placeholders
        dst: Destination pattern with {var} or {(expr)} placeholders
        reverse: If True, swap src and dst
        
    Returns:
        Compiled Rule object
        
    Raises:
        ValueError: If patterns are invalid or reverse with math
    """
    if not src or not dst:
        raise ValueError("Source and destination cannot be empty")
    
    # reverse means swap src <-> dst
    if reverse:
        if _MATH.search(dst):
            raise ValueError(
                f"Reverse mapping not allowed with arithmetic in: {dst}"
            )
        src, dst = dst, src

    parts = _CAPTURE.split(src)
    regex_parts = []

    for i, p in enumerate(parts):
        if i % 2 == 0:
            regex_parts.append(re.escape(p))
        else:
            regex_parts.append(rf"(?P<{p}>\d+)")

    regex = re.compile("".join(regex_parts))

    def transform(m: re.Match) -> str:
        out = dst

        # replace captures
        for name, val in m.groupdict().items():
            out = out.replace(f"{{{name}}}", val)

        # math only allowed in forward
        def _math(m2):
            expr = m2.group(1)
            for name, val in m.groupdict().items():
                expr = expr.replace(name, val)
            return str(eval_math_expr(expr))

        out = _MATH.sub(_math, out)
        return out

    return Rule(regex, transform)


def parse_rules(text: str, *, reverse: bool = False, debug: bool = False) -> RuleEngine:
    """
    Parse transformation rules from text format.
    
    Args:
        text: Newline-separated rules in format "src, dst"
        reverse: If True, swap src and dst in all rules
        debug: If True, enable debug logging
        
    Returns:
        RuleEngine configured with parsed rules
        
    Raises:
        ValueError: If rules are malformed
        
    Examples:
        >>> engine = parse_rules(\"\"\"
        ...     layer.{n}.weight, block.{n}.weight
        ...     encoder.{n}, backbone.{n}
        ... \"\"\")
    """
    rules = []
    for line_num, line in enumerate(text.strip().splitlines(), 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Validate format
        if ',' not in line:
            raise ValueError(f"Line {line_num}: Missing comma separator")
            
        parts = line.split(',', 1)  # Split only on first comma
        if len(parts) != 2:
            raise ValueError(f"Line {line_num}: Invalid rule format")
            
        src, dst = map(str.strip, parts)
        
        if not src or not dst:
            raise ValueError(f"Line {line_num}: Empty source or destination")
            
        try:
            rules.append(_compile(src, dst, reverse=reverse))
        except ValueError as e:
            raise ValueError(f"Line {line_num}: {e}") from e
    
    return RuleEngine(rules, debug=debug)


# ==================== UTILITY FUNCTIONS ==================== #

def validate_rules(rules_text: str) -> List[str]:
    """
    Validate rules and return list of errors.
    
    Args:
        rules_text: Rules text to validate
        
    Returns:
        List of error messages (empty if valid)
        
    Examples:
        >>> errors = validate_rules("layer.{n}, block.{n}")
        >>> len(errors)
        0
    """
    errors = []
    for line_num, line in enumerate(rules_text.strip().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if ',' not in line:
            errors.append(f"Line {line_num}: Missing comma")
        else:
            parts = line.split(',', 1)
            if len(parts) != 2:
                errors.append(f"Line {line_num}: Invalid format")
                continue
                
            src, dst = map(str.strip, parts)
            if not src:
                errors.append(f"Line {line_num}: Empty source")
            if not dst:
                errors.append(f"Line {line_num}: Empty destination")
    
    return errors


def expand_range_rules(rules_text: str) -> str:
    """
    Expand range syntax in rules.
    
    Args:
        rules_text: Rules with {start..end} syntax
        
    Returns:
        Expanded rules text
        
    Examples:
        >>> expand_range_rules("layer.{0..2}.weight, block.{0..2}.weight")
        'layer.0.weight, block.0.weight\\nlayer.1.weight, block.1.weight\\nlayer.2.weight, block.2.weight'
    """
    expanded_lines = []
    
    for line in rules_text.strip().splitlines():
        if '..' not in line:
            expanded_lines.append(line)
            continue
        
        # Find range pattern {start..end}
        range_pattern = re.compile(r'\{(\d+)\.\.(\d+)\}')
        match = range_pattern.search(line)
        
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            for i in range(start, end + 1):
                expanded = range_pattern.sub(str(i), line, count=1)
                expanded_lines.append(expanded)
        else:
            expanded_lines.append(line)
    
    return '\n'.join(expanded_lines)


def generate_inverse_rules(rules_text: str) -> str:
    """
    Generate inverse mapping from rules.
    
    Args:
        rules_text: Original rules
        
    Returns:
        Inverted rules text
        
    Raises:
        ValueError: If rules contain arithmetic (cannot be inverted)
        
    Examples:
        >>> generate_inverse_rules("layer.{n}, block.{n}")
        'block.{n}, layer.{n}'
    """
    inverse_lines = []
    
    for line in rules_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        src, dst = map(str.strip, line.split(','))
        
        # Check if inverse is possible (no math)
        if _MATH.search(dst):
            raise ValueError(f"Cannot invert rule with math: {line}")
        
        # Swap src and dst
        inverse_lines.append(f"{dst}, {src}")
    
    return '\n'.join(inverse_lines)


# ==================== MAIN API ==================== #

def state_bridge(
    state_dict: Dict[str, Any],
    rules_text: str,
    *,
    reverse: bool = False,
    detect_collision: bool = True,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Transform state dictionary keys using rule-based mappings.
    
    Args:
        state_dict: Input dictionary to transform
        rules_text: Newline-separated rules in format "src, dst"
        reverse: If True, swap src and dst in rules
        detect_collision: If True, raise error on key collisions
        debug: If True, log transformation steps
        
    Returns:
        New dictionary with transformed keys
        
    Raises:
        KeyError: If collision detected and detect_collision=True
        ValueError: If rules are malformed
        
    Examples:
        >>> sd = {"layer.0.weight": torch.randn(10, 10)}
        >>> rules = "layer.{n}.weight, block.{n}.weight"
        >>> new_sd = state_bridge(sd, rules)
        >>> "block.0.weight" in new_sd
        True
    """
    engine = parse_rules(rules_text, reverse=reverse, debug=debug)
    new_sd = {}
    collisions = []

    for k, v in state_dict.items():
        try:
            nk = engine.apply(k)
        except Exception as e:
            raise ValueError(f"Failed to transform key '{k}': {e}") from e

        if detect_collision and nk in new_sd:
            collisions.append((k, nk))
        
        new_sd[nk] = v

    if collisions:
        collision_msg = ", ".join(f"{k}->{nk}" for k, nk in collisions)
        raise KeyError(f"Key collisions detected: {collision_msg}")

    return new_sd


def state_bridge_batch(
    state_dict: Dict[str, Any],
    operations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply multiple operations in sequence.
    
    Args:
        state_dict: Input state dictionary
        operations: List of operation dicts
        
    Returns:
        Transformed state dictionary
        
    Examples:
        >>> ops = [
        ...     {'type': 'prefix', 'add': 'model.'},
        ...     {'type': 'rules', 'rules_text': 'layer.{n}, block.{n}'},
        ... ]
        >>> new_sd = state_bridge_batch(sd, ops)
    """
    result = state_dict.copy()
    
    for op in operations:
        op_type = op.get('type')
        
        if op_type == 'prefix':
            prefix = op['add']
            result = {f"{prefix}{k}": v for k, v in result.items()}
            
        elif op_type == 'suffix':
            suffix = op['add']
            result = {f"{k}{suffix}": v for k, v in result.items()}
            
        elif op_type == 'remove_prefix':
            prefix = op['remove']
            result = {
                k[len(prefix):] if k.startswith(prefix) else k: v 
                for k, v in result.items()
            }
            
        elif op_type == 'remove_suffix':
            suffix = op['remove']
            result = {
                k[:-len(suffix)] if k.endswith(suffix) else k: v 
                for k, v in result.items()
            }
            
        elif op_type == 'replace':
            old, new = op['old'], op['new']
            result = {k.replace(old, new): v for k, v in result.items()}
            
        elif op_type == 'rules':
            result = state_bridge(
                result, 
                op['rules_text'],
                reverse=op.get('reverse', False),
                detect_collision=op.get('detect_collision', True),
                debug=op.get('debug', False),
            )
            
        elif op_type == 'filter':
            # Filter keys matching pattern
            pattern = re.compile(op['pattern'])
            include = op.get('include', True)
            if include:
                result = {k: v for k, v in result.items() if pattern.search(k)}
            else:
                result = {k: v for k, v in result.items() if not pattern.search(k)}
    
    return result


def state_bridge_nested(
    state_dict: Dict[str, Any],
    rules_text: str,
    separator: str = '.',
    *,
    reverse: bool = False,
    detect_collision: bool = True,
) -> Dict[str, Any]:
    """
    Handle nested dictionaries by flattening, transforming, then unflattening.
    
    Args:
        state_dict: Nested dictionary
        rules_text: Transformation rules
        separator: Key separator for flattening
        reverse: If True, reverse the rules
        detect_collision: If True, detect key collisions
        
    Returns:
        Transformed nested dictionary
        
    Examples:
        >>> nested = {'model': {'layer1': {'weight': tensor}}}
        >>> rules = "model.layer1, model.block1"
        >>> result = state_bridge_nested(nested, rules)
    """
    def flatten(d: Dict, prefix: str = '') -> Dict[str, Any]:
        items = {}
        for k, v in d.items():
            new_key = f"{prefix}{separator}{k}" if prefix else k
            if isinstance(v, dict):
                items.update(flatten(v, new_key))
            else:
                items[new_key] = v
        return items
    
    def unflatten(d: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for k, v in d.items():
            parts = k.split(separator)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = v
        return result
    
    flat = flatten(state_dict)
    transformed = state_bridge(flat, rules_text, reverse=reverse, detect_collision=detect_collision)
    return unflatten(transformed)


def state_bridge_preview(
    state_dict: Dict[str, Any],
    rules_text: str,
    *,
    reverse: bool = False,
) -> Tuple[Dict[str, str], Set[str], Set[str]]:
    """
    Preview transformations without applying them.
    
    Args:
        state_dict: Input state dictionary
        rules_text: Transformation rules
        reverse: If True, reverse the rules
        
    Returns:
        Tuple of (mapping, unchanged, collisions)
        - mapping: Dict of old_key -> new_key
        - unchanged: Set of keys that didn't change
        - collisions: Set of new keys that collide
        
    Examples:
        >>> mapping, unchanged, collisions = state_bridge_preview(sd, rules)
        >>> print(f"Will transform {len(mapping) - len(unchanged)} keys")
    """
    engine = parse_rules(rules_text, reverse=reverse)
    
    mapping = {}
    unchanged = set()
    new_keys = {}
    collisions = set()
    
    for k in state_dict.keys():
        nk = engine.apply(k)
        mapping[k] = nk
        
        if k == nk:
            unchanged.add(k)
        
        if nk in new_keys:
            collisions.add(nk)
        new_keys[nk] = k
    
    return mapping, unchanged, collisions


def print_diff(state_dict: Dict[str, Any], rules_text: str, reverse: bool = False):
    """
    Pretty print transformation diff.
    
    Args:
        state_dict: Input state dictionary
        rules_text: Transformation rules
        reverse: If True, reverse the rules
    """
    mapping, unchanged, collisions = state_bridge_preview(state_dict, rules_text, reverse=reverse)
    
    print("=" * 60)
    print("TRANSFORMATION PREVIEW")
    print("=" * 60)
    
    print("\n📝 CHANGES:")
    changes = [(old, new) for old, new in mapping.items() if old != new]
    if changes:
        for old, new in changes:
            print(f"  {old} -> {new}")
    else:
        print("  No changes")
    
    print(f"\n✓ UNCHANGED: {len(unchanged)} keys")
    
    if collisions:
        print(f"\n⚠️  COLLISIONS: {len(collisions)}")
        for key in collisions:
            print(f"  {key}")
    
    print("=" * 60)


# ==================== ADVANCED FEATURES ==================== #

class RuleChain:
    """Chain multiple rule engines together."""
    
    def __init__(self):
        self.engines: List[Tuple[str, RuleEngine]] = []
    
    def add(self, name: str, rules_text: str, reverse: bool = False, debug: bool = False):
        """
        Add a rule engine to the chain.
        
        Args:
            name: Name for this step (for tracing)
            rules_text: Transformation rules
            reverse: If True, reverse the rules
            debug: If True, enable debug logging
            
        Returns:
            Self for chaining
        """
        engine = parse_rules(rules_text, reverse=reverse, debug=debug)
        self.engines.append((name, engine))
        return self
    
    def apply(self, state_dict: Dict[str, Any], trace: bool = False) -> Dict[str, Any]:
        """
        Apply all engines in sequence.
        
        Args:
            state_dict: Input state dictionary
            trace: If True, print progress
            
        Returns:
            Transformed state dictionary
        """
        result = state_dict
        
        if trace:
            print(f"Initial: {len(result)} keys")
        
        for name, engine in self.engines:
            new_result = {}
            for k, v in result.items():
                nk = engine.apply(k)
                new_result[nk] = v
            result = new_result
            
            if trace:
                print(f"After {name}: {len(result)} keys")
        
        return result


class RuleTemplate:
    """Reusable rule templates with parameter substitution."""
    
    TEMPLATES = {
        'huggingface_to_timm': """
            embeddings.{n}, patch_embed.{n}
            encoder.layer.{n}, blocks.{n}
            attention.self, attn
            attention.output.dense, attn.proj
            intermediate.dense, mlp.fc1
            output.dense, mlp.fc2
            LayerNorm, norm
        """,
        
        'pytorch_to_tensorflow': """
            {prefix}.weight, {prefix}/kernel
            {prefix}.bias, {prefix}/bias
            running_mean, moving_mean
            running_var, moving_variance
        """,
        
        'add_prefix': """
            {key}, {prefix}.{key}
        """,
        
        'remove_prefix': """
            {prefix}.{key}, {key}
        """,
    }
    
    @classmethod
    def expand_template(cls, template_name: str, **params) -> str:
        """
        Expand template with parameters.
        
        Args:
            template_name: Name of template
            **params: Parameters to substitute
            
        Returns:
            Expanded rules text
            
        Examples:
            >>> RuleTemplate.expand_template('add_prefix', prefix='model')
        """
        template = cls.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Replace parameters
        for key, val in params.items():
            template = template.replace(f"{{{key}}}", str(val))
        
        return template
    
    @classmethod
    def apply_template(cls, state_dict: Dict[str, Any], 
                       template_name: str, **params) -> Dict[str, Any]:
        """
        Apply a named template to state dict.
        
        Args:
            state_dict: Input state dictionary
            template_name: Name of template
            **params: Parameters for template
            
        Returns:
            Transformed state dictionary
        """
        rules = cls.expand_template(template_name, **params)
        return state_bridge(state_dict, rules)