#!/usr/bin/env python3
"""
Column transformation utilities for data processing
"""
import re


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def flatten_dict(d, parent_key='', sep='_', convert_to_snake=False):
    """Flatten nested dictionary, optionally converting keys to snake_case"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if convert_to_snake:
            new_key = camel_to_snake(new_key)
            
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep, convert_to_snake=convert_to_snake).items())
        else:
            items.append((new_key, str(v) if v is not None else None))
    return dict(items)
