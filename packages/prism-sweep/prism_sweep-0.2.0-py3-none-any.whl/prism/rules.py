"""
Prism Rules - Rule-based validation and filtering for experiments.

This module handles the prism.rules.yaml file which defines rules for
filtering, skipping, or flagging experiment configurations.

Rules YAML Format:

    rules:
      - name: "Skip large model with small LR"
        conditions:
          model.size: "large"
          optimizer.lr: 0.0001
        action: skip
        message: "Large models require higher learning rates"
      
      - name: "Warn about experimental combination"
        conditions:
          backbone: "vit"
          loss: "focal"
        action: include-warning
        message: "This combination is experimental"

Supported actions:
    - error: Raise an error, stop the sweep generation
    - skip: Silently skip this configuration
    - skip-warning: Skip but print a warning
    - include-warning: Include but print a warning

Condition operators (in condition values):
    - Direct value: Exact match
    - {"$gt": value}: Greater than
    - {"$gte": value}: Greater than or equal
    - {"$lt": value}: Less than
    - {"$lte": value}: Less than or equal
    - {"$ne": value}: Not equal
    - {"$in": [values]}: Value in list
    - {"$nin": [values]}: Value not in list
    - {"$regex": "pattern"}: Regex match (strings only)
"""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .utils import print_info, print_warning, print_error, deep_get


class RuleAction(str, Enum):
    """Possible actions when a rule matches."""
    ERROR = "error"
    SKIP = "skip"
    SKIP_WARNING = "skip-warning"
    INCLUDE_WARNING = "include-warning"


@dataclass
class Rule:
    """A single validation rule."""
    name: str
    conditions: Dict[str, Any]
    action: RuleAction
    message: str = ""
    
    def matches(self, config: Dict[str, Any]) -> bool:
        """Check if the rule conditions match the given config."""
        for param_path, expected in self.conditions.items():
            actual = deep_get(config, param_path)
            if not self._match_value(actual, expected):
                return False
        return True
    
    def _match_value(self, actual: Any, expected: Any) -> bool:
        """Match a single value against an expected pattern."""
        # Handle operator syntax
        if isinstance(expected, dict):
            return self._match_operators(actual, expected)
        
        # Direct equality
        return actual == expected
    
    def _match_operators(self, actual: Any, operators: Dict[str, Any]) -> bool:
        """Match using operator syntax."""
        for op, value in operators.items():
            if op == "$gt":
                if actual is None or actual <= value:
                    return False
            elif op == "$gte":
                if actual is None or actual < value:
                    return False
            elif op == "$lt":
                if actual is None or actual >= value:
                    return False
            elif op == "$lte":
                if actual is None or actual > value:
                    return False
            elif op == "$ne":
                if actual == value:
                    return False
            elif op == "$in":
                if actual not in value:
                    return False
            elif op == "$nin":
                if actual in value:
                    return False
            elif op == "$regex":
                if actual is None or not isinstance(actual, str):
                    return False
                if not re.search(value, actual):
                    return False
            elif op == "$exists":
                exists = actual is not None
                if exists != value:
                    return False
            else:
                # Unknown operator - treat as nested dict match
                if not isinstance(actual, dict) or op not in actual:
                    return False
                if actual[op] != value:
                    return False
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """Create a Rule from a dictionary."""
        name = data.get("name", "Unnamed rule")
        conditions = data.get("conditions", {})
        action_str = data.get("action", "skip-warning")
        message = data.get("message", "")
        
        try:
            action = RuleAction(action_str)
        except ValueError:
            raise ValueError(f"Invalid rule action '{action_str}'. "
                           f"Must be one of: {[a.value for a in RuleAction]}")
        
        return cls(name=name, conditions=conditions, action=action, message=message)


@dataclass
class RuleResult:
    """Result of applying a rule to a config."""
    rule: Rule
    matched: bool
    
    @property
    def should_skip(self) -> bool:
        """Check if this result means the config should be skipped."""
        return self.matched and self.rule.action in (RuleAction.SKIP, RuleAction.SKIP_WARNING)
    
    @property
    def is_error(self) -> bool:
        """Check if this result is an error."""
        return self.matched and self.rule.action == RuleAction.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this result should produce a warning."""
        return self.matched and self.rule.action in (RuleAction.SKIP_WARNING, RuleAction.INCLUDE_WARNING)


@dataclass
class RulesConfig:
    """Container for all rules."""
    rules: List[Rule] = field(default_factory=list)
    source_file: Optional[Path] = None
    
    def add_rule(self, rule: Rule):
        """Add a rule to the configuration."""
        self.rules.append(rule)
    
    def apply(self, config: Dict[str, Any]) -> List[RuleResult]:
        """Apply all rules to a config and return results."""
        results = []
        for rule in self.rules:
            matched = rule.matches(config)
            results.append(RuleResult(rule=rule, matched=matched))
        return results
    
    def check(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Check a config against all rules.
        
        Returns:
            Tuple of (should_include, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        should_include = True
        
        for result in self.apply(config):
            if not result.matched:
                continue
            
            message = f"[{result.rule.name}] {result.rule.message}" if result.rule.message else f"[{result.rule.name}]"
            
            if result.is_error:
                errors.append(message)
                should_include = False
            elif result.should_skip:
                should_include = False
                if result.is_warning:
                    warnings.append(f"SKIP: {message}")
            elif result.is_warning:
                warnings.append(message)
        
        return should_include, errors, warnings
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> "RulesConfig":
        """Load rules from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        rules_data = data.get("rules", [])
        rules = [Rule.from_dict(r) for r in rules_data]
        
        return cls(rules=rules, source_file=path)
    
    @classmethod
    def load_if_exists(cls, path: Union[str, Path]) -> Optional["RulesConfig"]:
        """Load rules from a YAML file if it exists."""
        path = Path(path)
        if not path.exists():
            return None
        return cls.load(path)


class RulesEngine:
    """
    Engine for applying rules to experiment configurations.
    
    This class manages the loading and application of rules,
    and provides methods for filtering configurations.
    """
    
    def __init__(self, rules_config: Optional[RulesConfig] = None):
        self.rules_config = rules_config or RulesConfig()
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "RulesEngine":
        """Create a RulesEngine from a rules file."""
        rules_config = RulesConfig.load(path)
        return cls(rules_config)
    
    @classmethod
    def from_file_if_exists(cls, path: Union[str, Path]) -> "RulesEngine":
        """Create a RulesEngine from a rules file if it exists."""
        rules_config = RulesConfig.load_if_exists(path)
        return cls(rules_config)
    
    def filter_configs(
        self,
        configs: Dict[str, Dict[str, Any]],
        verbose: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Filter configurations based on rules.
        
        Args:
            configs: Dict of {key: config} to filter
            verbose: Whether to print warnings/info
        
        Returns:
            Dict of configurations that passed all rules
        
        Raises:
            ValueError: If any config triggers an error rule
        """
        if not self.rules_config.rules:
            return configs
        
        filtered = {}
        skipped_count = 0
        
        for key, config in configs.items():
            should_include, errors, warnings = self.rules_config.check(config)
            
            # Print warnings if verbose
            if verbose:
                for warning in warnings:
                    print_warning(f"{key}: {warning}")
            
            # Raise on errors
            if errors:
                error_msg = f"Configuration '{key}' triggered error rules:\n"
                error_msg += "\n".join(f"  - {e}" for e in errors)
                raise ValueError(error_msg)
            
            if should_include:
                filtered[key] = config
            else:
                skipped_count += 1
        
        if verbose and skipped_count > 0:
            print_info(f"Rules skipped {skipped_count} configurations")
        
        return filtered
    
    def validate_config(
        self,
        key: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single configuration against rules.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        return self.rules_config.check(config)


def find_rules_file(
    prism_configs_dir: Path,
    project_root: Optional[Path] = None
) -> Optional[Path]:
    """
    Find a rules file in the expected locations.
    
    Search order:
    1. prism_configs_dir / prism.rules.yaml
    2. project_root / prism.rules.yaml
    3. project_root / configs / prism.rules.yaml
    """
    candidates = [
        prism_configs_dir / "prism.rules.yaml",
    ]
    
    if project_root:
        candidates.extend([
            project_root / "prism.rules.yaml",
            project_root / "configs" / "prism.rules.yaml",
        ])
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    return None
