#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Configuration management for iOS Unit Test Generator.

This module provides centralized configuration with support for:
- Environment variable overrides
- Default values
- Type validation
- Easy extension
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PathConfig:
    """File and directory path configuration."""
    
    # Chromium source root (can be overridden by CHROMIUM_SRC env var)
    chromium_src_root: str = field(default_factory=lambda: os.getenv('CHROMIUM_SRC', ''))
    
    # Default build output directory
    default_build_dir: str = 'out/Debug-iphonesimulator'
    
    # BUILD file names
    build_gn_name: str = 'BUILD.gn'
    build_edge_gni_name: str = 'BUILD_edge.gni'
    
    # Test pattern database
    pattern_db_file: str = 'ios_test_patterns.json'


@dataclass
class TestTargetConfig:
    """Test target detection configuration."""
    
    # Path prefix to test target mapping
    path_to_target: Dict[str, str] = field(default_factory=lambda: {
        'components/': 'components_unittests',
        'ios/components/': 'ios_components_unittests',
        'ios/web': 'ios_web_unittests',
        'ios/chrome': 'ios_chrome_unittests',
    })
    
    # Default test target
    default_target: str = 'ios_chrome_unittests'


@dataclass
class EdgeDetectionConfig:
    """Edge-specific file detection configuration."""
    
    # Filename suffixes that indicate Edge code
    edge_suffixes: List[str] = field(default_factory=lambda: ['_edge'])
    
    # Filename prefixes that indicate Edge code
    edge_prefixes: List[str] = field(default_factory=lambda: ['edge_'])
    
    # Directory patterns that indicate Edge code
    edge_dir_patterns: List[str] = field(default_factory=lambda: ['/edge_'])


@dataclass
class BuildFileConfig:
    """BUILD file update configuration."""
    
    # Edge BUILD file paths
    edge_ios_chrome_build: str = 'ios/chrome/test/BUILD_edge.gni'
    edge_components_build: str = 'components/BUILD_edge.gni'
    
    # Template names
    edge_ios_template: str = 'edge_overlay_test_ios_chrome_unittests'
    edge_components_template: str = 'edge_overlay_test_components_unittests'
    
    # Indentation settings
    deps_indent: str = '    '
    template_indent: str = '        '


@dataclass
class TestQualityConfig:
    """Test quality validation configuration."""
    
    # Minimum assertions per test for good quality
    min_assertions_per_test: float = 1.5
    
    # Quality score thresholds
    excellent_score: int = 85
    good_score: int = 70
    acceptable_score: int = 60
    
    # Penalty weights
    error_penalty: int = 20
    warning_penalty: int = 5
    
    # Bonus points
    good_assertion_density_bonus: int = 10
    no_todos_bonus: int = 5
    no_nil_only_checks_bonus: int = 10


@dataclass
class CompilationConfig:
    """Compilation and execution configuration."""
    
    # Compiler command
    compiler_cmd: str = 'autoninja'
    
    # Test runner script
    test_runner_script: str = 'testing/iossim/iossim.py'
    
    # Maximum compilation output size (bytes)
    max_output_size: int = 60000
    
    # Timeout settings (seconds)
    compile_timeout: int = 600
    test_timeout: int = 300


@dataclass
class Config:
    """Master configuration container."""
    
    paths: PathConfig = field(default_factory=PathConfig)
    test_targets: TestTargetConfig = field(default_factory=TestTargetConfig)
    edge_detection: EdgeDetectionConfig = field(default_factory=EdgeDetectionConfig)
    build_files: BuildFileConfig = field(default_factory=BuildFileConfig)
    test_quality: TestQualityConfig = field(default_factory=TestQualityConfig)
    compilation: CompilationConfig = field(default_factory=CompilationConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure chromium_src_root is set
        if not self.paths.chromium_src_root:
            # Try to detect from script location
            script_path = Path(__file__).resolve()
            potential_root = script_path.parent.parent.parent.parent
            if (potential_root / 'ios' / 'chrome').exists():
                self.paths.chromium_src_root = str(potential_root)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance (singleton pattern)."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config():
    """Reset configuration to defaults (useful for testing)."""
    global _config
    _config = None


# Convenience functions for accessing config values
def get_chromium_src_root() -> Path:
    """Get Chromium source root directory."""
    config = get_config()
    if not config.paths.chromium_src_root:
        raise RuntimeError(
            "Could not find Chromium source root. Please set CHROMIUM_SRC "
            "environment variable:\n"
            "  export CHROMIUM_SRC=/path/to/chromium/src"
        )
    return Path(config.paths.chromium_src_root).resolve()


def get_test_target_for_path(path: str) -> str:
    """Get test target name for a given source file path."""
    config = get_config()
    normalized_path = path.replace('\\', '/')
    
    for prefix, target in config.test_targets.path_to_target.items():
        if normalized_path.startswith(prefix):
            return target
    
    return config.test_targets.default_target


def is_edge_file(file_path: str) -> bool:
    """Check if file is Edge-specific based on naming conventions."""
    config = get_config()
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Check filename suffix
    for suffix in config.edge_detection.edge_suffixes:
        if name_without_ext.endswith(suffix):
            return True
    
    # Check filename prefix
    for prefix in config.edge_detection.edge_prefixes:
        if name_without_ext.startswith(prefix):
            return True
    
    # Check directory patterns
    for pattern in config.edge_detection.edge_dir_patterns:
        if pattern in file_path:
            return True
    
    return False
