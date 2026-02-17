"""
Unified Metadata Builder for all generators.

This module provides standardized metadata generation for task deduplication,
parameter tracking, and reproducibility.

Author: VBVR-DataFactory Team
"""

import hashlib
import json
import re
import subprocess
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional


SKIP_KEYS = {
    'temp_path', 'temp_dir', 'temp_file',
    'video_temp_path', 'image_temp_path', 
    'cache_path', 'cache_dir',
    '_cache', '_internal', '_temp', '_tmp',
    'seed', 'random_seed',
    'tmp', 'tmpdir',
}


@lru_cache(maxsize=1)
def _get_git_info() -> Dict[str, Any]:
    """
    Fetch git provenance info exactly once per process.

    Returns cached dict with commit, branch, remote, is_dirty.
    All subprocess calls happen only on the first invocation;
    every subsequent call returns the cached result.
    """
    def _run(cmd: list[str]) -> str:
        try:
            return subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, text=True
            ).strip()
        except Exception:
            return ""

    commit = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    raw_remote = _run(["git", "remote", "get-url", "origin"])
    repo = _sanitize_remote(raw_remote)
    is_dirty = _run(["git", "status", "--porcelain"]) != ""

    return {
        "commit": commit,
        "branch": branch,
        "repo": repo,
        "is_dirty": is_dirty,
    }


def _sanitize_remote(url: str) -> str:
    """
    Extract owner/repo from a git remote URL and return a full GitHub link.
    Strips credentials, protocol, hostname, and .git suffix.
    Returns empty string if parsing fails.
    """
    if not url:
        return ""
    m = re.search(r'[/:]([^/:]+/[^/:]+?)(?:\.git)?$', url)
    if m:
        return f"https://github.com/{m.group(1)}"
    return ""


def build_metadata(
    task_id: str,
    generator_name: str,
    parameters: Dict[str, Any],
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build standardized metadata for a task.
    
    Args:
        task_id: Unique task identifier (e.g., "shape_scaling_00000001")
        generator_name: Name of the generator (domain)
        parameters: Task parameters dict (from _generate_task_data())
        seed: Random seed used for generation (does not affect param_hash)
    
    Returns:
        Standardized metadata dict with all required fields
    """
    clean_params = _clean_parameters(parameters)
    param_hash = _compute_param_hash(clean_params)

    return {
        "task_id": task_id,
        "generator": generator_name,
        "timestamp": datetime.now().isoformat(),
        "parameters": clean_params,
        "param_hash": param_hash,
        "generation": {
            "seed": seed,
            "git": _get_git_info(),
        }
    }


def _clean_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean parameters by removing non-serializable and unnecessary keys.
    """
    clean = {}
    
    for key, value in params.items():
        if any(skip in key.lower() for skip in SKIP_KEYS):
            continue
        
        serialized = _serialize_value(value)
        if serialized is not None:
            clean[key] = serialized
    
    return clean


def _serialize_value(value: Any) -> Any:
    """
    Convert any Python value to JSON-serializable format.
    """
    if isinstance(value, (str, int, bool, type(None))):
        return value
    
    if isinstance(value, float):
        return round(value, 6)
    
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    
    if isinstance(value, dict):
        serialized_dict = {}
        for k, v in value.items():
            if isinstance(k, tuple):
                key_str = str(k)
            else:
                key_str = _serialize_value(k) if not isinstance(k, (str, int, bool, type(None))) else k
            serialized_dict[key_str] = _serialize_value(v)
        return serialized_dict
    
    if hasattr(value, '__dict__'):
        obj_dict = {}
        for attr in ['name', 'type', 'id', 'value', 'label']:
            if hasattr(value, attr):
                attr_value = getattr(value, attr)
                serialized = _serialize_value(attr_value)
                if serialized is not None:
                    obj_dict[attr] = serialized
        
        if obj_dict:
            obj_dict['_type'] = type(value).__name__
            return obj_dict
        else:
            return {"_type": type(value).__name__}
    
    return type(value).__name__


def _compute_param_hash(params: Dict[str, Any]) -> str:
    """
    Compute deterministic hash for parameters.

    Uses SHA256 and returns first 16 characters.
    """
    param_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
    hash_obj = hashlib.sha256(param_str.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


def verify_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Verify that metadata has all required fields and correct format.
    """
    required_fields = [
        'task_id', 'generator', 'timestamp',
        'parameters', 'param_hash', 'generation'
    ]
    
    for field in required_fields:
        if field not in metadata:
            return False
    
    if not isinstance(metadata['param_hash'], str) or len(metadata['param_hash']) != 16:
        return False
    
    if not isinstance(metadata['parameters'], dict):
        return False
    
    if 'seed' not in metadata['generation']:
        return False
    
    git_info = metadata.get('generation', {}).get('git', {})
    if 'commit' not in git_info:
        return False
    
    return True


if __name__ == "__main__":
    example_metadata = build_metadata(
        task_id="shape_scaling_00000001",
        generator_name="O-9_shape_scaling_data-generator",
        parameters={
            "shape_a": "circle",
            "shape_c": "square",
            "scale_factor": 1.5,
            "color": [255, 0, 0],
            "position": (100, 200),
            "seed": 42
        },
        seed=42,
    )
    
    print("Example Metadata:")
    print(json.dumps(example_metadata, indent=2, ensure_ascii=False))
    print("\nVerification:", verify_metadata(example_metadata))
