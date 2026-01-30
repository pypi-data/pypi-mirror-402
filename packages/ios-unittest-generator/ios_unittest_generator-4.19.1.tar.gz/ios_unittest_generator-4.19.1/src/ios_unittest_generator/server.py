#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""iOS Unit Test Generator MCP Server.

This MCP server provides tools to generate unit tests for iOS Edge code.
It analyzes existing code, generates test files following iOS/Edge conventions,
and updates BUILD.gn files automatically.

Usage:
    uvx ios-unittest-generator           # Run via uvx (recommended)
    python -m ios_unittest_generator     # Run as module
"""

import json
import os
import re
import subprocess
import sys
import time
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mcp.server import fastmcp

# Import refactored modules (relative imports for package)
from .config import get_config, get_chromium_src_root
from .config import get_test_target_for_path, is_edge_file
from .workflow_state import get_workflow_state as get_workflow_state_obj
from .workflow_state import update_workflow_state as update_workflow_state_obj
from .build_file_utils import add_component_to_test_target

mcp = fastmcp.FastMCP('ios-unittest-generator')

# ============================================================================
# DEBUG CONTROL - Disable debug output during normal operation
# ============================================================================
# Save original stderr for startup messages, then redirect to devnull
_original_stderr = sys.stderr


# ============================================================================
# EXECUTION FINGERPRINT - Prevents Copilot from fabricating results
# ============================================================================

def generate_execution_fingerprint(tool_name: str, output_sample: str = "") -> Dict:
    """Generate unforgeable execution proof to prevent Copilot from fabricating results.
    
    Returns a dictionary with:
    - execution_id: Random UUID that cannot be predicted
    - timestamp_us: Microsecond-precision timestamp
    - process_id: Actual OS process ID
    - output_hash: SHA256 hash of actual output (first 1000 chars)
    - tool_name: Name of the tool that was executed
    
    Copilot CANNOT fake these values because:
    1. UUID is random and changes every execution
    2. Microsecond timestamp is precise and unpredictable
    3. Process ID is from actual OS
    4. Output hash requires actual output content
    """
    return {
        'EXECUTION_PROOF': {
            'execution_id': str(uuid.uuid4()),
            'timestamp_microseconds': time.time_ns() // 1000,  # microseconds since epoch
            'process_id': os.getpid(),
            'output_hash_sha256': hashlib.sha256(output_sample[:1000].encode()).hexdigest(),
            'tool_name': tool_name,
            'verification': 'This execution proof cannot be fabricated. Check VS Code Output panel for actual tool execution logs.'
        }
    }


# ============================================================================
# WORKFLOW STATE MACHINE - Ensures proper step execution order
# ============================================================================

# Using refactored thread-safe workflow state from workflow_state.py
# Convert WorkflowState dataclass to dict for backward compatibility
def get_workflow_state(source_file: str) -> Dict:
    """Get workflow state as dict (backward compatible wrapper)."""
    state = get_workflow_state_obj(source_file)
    return {
        'source_file': state.source_file,
        'step_1_analyze_complete': state.step_1_analyze_complete,
        'step_2_generate_complete': state.step_2_generate_complete,
        'step_3_enhancement_verified': state.step_3_enhancement_verified,
        'step_4_build_updated': state.step_4_build_updated,
        'step_5_compilation_success': state.step_5_compilation_success,
        'step_6_tests_passed': state.step_6_tests_passed,
        'test_file_path': state.test_file_path,
        'test_count_baseline': state.test_count_baseline,
        'quality_score_baseline': state.quality_score_baseline,
        'workflow_started': state.workflow_started
    }

def update_workflow_state(source_file: str, **updates) -> None:
    """Update workflow state (backward compatible wrapper)."""
    update_workflow_state_obj(source_file, **updates)


# ============================================================================
# Core Utility Functions
# ============================================================================

# Using refactored config-based implementation from config.py
# get_chromium_src_root is imported directly from config module


def is_ios_source_file(file_path: str) -> bool:
    """Checks if the file is an iOS source file (.h, .mm, .m).
    
    Accepts files in any directory structure that contains 'ios':
    - ios/chrome/browser/ui/main/my_feature.mm (standard iOS)
    - components/edge_hybrid/ios/edge_hybrid_base_view.mm (component iOS)
    - third_party/some_lib/ios/helper.mm (third-party iOS)
    """
    # Normalize path separators
    normalized_path = file_path.replace('\\', '/')
    
    # Check if path contains '/ios/' or starts with 'ios/' or ends with '/ios'
    has_ios_dir = ('/ios/' in normalized_path or 
                   normalized_path.startswith('ios/') or
                   normalized_path.endswith('/ios'))
    
    # Check file extension
    is_ios_extension = any(normalized_path.endswith(ext) for ext in ['.h', '.mm', '.m'])
    
    return has_ios_dir and is_ios_extension


def detect_test_target(source_file_path: str) -> str:
    """Intelligently detect the correct test target by analyzing existing tests.
    
    Detection strategy:
    1. Check path patterns first (components/*, ios/chrome/*, etc.)
    2. Look for existing test files in the same directory
    3. Search BUILD files (BUILD.gn, BUILD_edge.gni) to see which target includes them
    4. Trace back to find the actual executable test target
    5. Fallback to standard targets based on path patterns
    
    Args:
        source_file_path: Path to source file (relative to src root)
        
    Returns:
        Test target name (e.g., 'ios_chrome_unittests')
    """
    normalized_path = source_file_path.replace('\\', '/')
    src_root = get_chromium_src_root()
    
    # [!]️ CRITICAL: Check path patterns FIRST before any file searching
    # This prevents incorrect target detection from BUILD file analysis
    
    # For components/* paths - ALWAYS components_unittests
    if normalized_path.startswith('components/'):
        return 'components_unittests'
    
    # For ios/components/* paths
    if normalized_path.startswith('ios/components/'):
        return 'ios_components_unittests'
    
    # For ios/web/* paths
    if 'ios/web' in normalized_path:
        return 'ios_web_unittests'
    
    # For ios/chrome/* paths - continue with file-based detection
    # (Fall through to existing logic below)
    
    # Step 2: Find existing test files in the same directory
    source_dir = Path(source_file_path).parent
    test_dir = src_root / source_dir
    
    existing_tests = []
    if test_dir.exists():
        for test_file in test_dir.glob('*_unittest.mm'):
            existing_tests.append(test_file.name)
    
    # Step 2: If we found existing tests, search BUILD files to see where they're included
    if existing_tests:
        # Search in current directory and parent directories
        current_dir = test_dir
        for _ in range(5):  # Search up to 5 levels up
            for build_file_name in ['BUILD.gn', 'BUILD_edge.gni']:
                build_file = current_dir / build_file_name
                if build_file.exists():
                    try:
                        content = build_file.read_text()
                        
                        # Check if any existing test file is mentioned in this BUILD file
                        for test_file in existing_tests[:3]:  # Check first 3 tests
                            if test_file in content:
                                # Found! Now extract the target name
                                target = _extract_test_target_from_build_file(content, test_file)
                                if target:
                                    return target
                    except:
                        pass
            
            # Move up one directory
            if current_dir.parent == current_dir:
                break
            current_dir = current_dir.parent
    
    # Step 3: Fallback to pattern-based detection for remaining paths
    # (components/* and ios/components/* and ios/web/* already handled at top)
    
    # Standard iOS chrome paths
    if 'ios/chrome' in normalized_path:
        return 'ios_chrome_unittests'
    
    # Default fallback
    return 'ios_chrome_unittests'


def _extract_test_target_from_build_file(build_content: str, test_file: str) -> Optional[str]:
    """Extract the test target that includes a specific test file.
    
    Args:
        build_content: Content of BUILD.gn or BUILD_edge.gni
        test_file: Name of test file to search for
        
    Returns:
        Test target name if found, None otherwise
    """
    import re
    
    # Strategy 1: Look for source_set("unit_tests") that includes this file
    # Then trace where this source_set is used
    
    # Check if file is in a source_set
    source_set_pattern = r'source_set\s*\(\s*"([^"]+)"\s*\)\s*\{([^}]*?' + re.escape(test_file) + r'[^}]*)\}'
    match = re.search(source_set_pattern, build_content, re.DOTALL)
    
    if match:
        source_set_name = match.group(1)
        
        # If it's "unit_tests", this is typically included in a parent target
        # Look for where this source_set is referenced
        if source_set_name == 'unit_tests':
            # Common pattern: deps = [ ":unit_tests" ] in a larger target
            # Look in parent BUILD files or ios/chrome/test/BUILD_edge.gni
            
            # For now, return ios_chrome_unittests as it's the most common
            return 'ios_chrome_unittests'
        
        # If it has a specific name, that might be the target
        if 'unittest' in source_set_name or 'test' in source_set_name:
            return source_set_name
    
    # Strategy 2: Look for test() definitions that include this file
    test_pattern = r'test\s*\(\s*"([^"]+)"\s*\)\s*\{[^}]*?' + re.escape(test_file) + r'[^}]*\}'
    match = re.search(test_pattern, build_content, re.DOTALL)
    
    if match:
        return match.group(1)
    
    # Strategy 3: Check for edge_overlay_test_ios_chrome_unittests pattern (Edge-specific)
    if 'edge_overlay_test_ios_chrome_unittests' in build_content:
        return 'ios_chrome_unittests'
    
    return None


# Using refactored implementation from build_file_utils.py
_add_component_to_test_target = add_component_to_test_target


def generate_build_edge_gni_instructions(source_file: str, build_gn_path: str) -> str:
    """Generates instructions for adding Edge-specific tests to BUILD_edge.gni.
    
    Args:
        source_file: Path to source file
        build_gn_path: Path to BUILD.gn file
        
    Returns:
        Formatted instructions string
    """
    # Extract the relative path for the BUILD target
    directory = str(Path(build_gn_path).parent)
    target_path = f'//{directory}:unit_tests'
    
    instructions = f"""
{'='*80}
WARNING: Edge-specific tests need to be manually added to BUILD_edge.gni
{'='*80}

This is Edge-specific code. Test target needs to be added to:
  File: ios/chrome/test/BUILD_edge.gni

Please follow these steps:

 Open file: ios/chrome/test/BUILD_edge.gni

 Find the deps list in edge_overlay_test_ios_chrome_unittests template

 Add the following line in alphabetical order:

    deps += [
      ...
      "{target_path}",  # <- Add this line
      ...
    ]

 Ensure alphabetical ascending order! Example:

    deps += [
      "//ios/chrome/browser/app_launcher:unit_tests",
      "{target_path}",  # <- Your new test
      "//ios/chrome/browser/passwords:unit_tests",
    ]

 After saving, recompile:

    autoninja -C out/Debug-iphonesimulator ios_chrome_unittests

Tip:
  - BUILD_edge.gni is specifically for Edge-specific tests
  - Alphabetical sorting is important for maintenance and finding
  - If directory name starts with edge_, it's Edge-specific code

{'='*80}
"""
    return instructions


def calculate_test_file_path(source_file: str) -> str:
    """Calculates the corresponding test file path for a source file.
    
    Args:
        source_file: Path to the source file (e.g., 'ios/chrome/app/foo.mm')
        
    Returns:
        Path to the test file (e.g., 'ios/chrome/app/foo_unittest.mm')
        
    Examples:
        'ios/chrome/app/profile/profile_controller.mm' ->
        'ios/chrome/app/profile/profile_controller_unittest.mm'
        
        'ios/chrome/app/profile/profile_controller_edge.mm' ->
        'ios/chrome/app/profile/profile_controller_edge_unittest.mm'
    """
    if not source_file.endswith(('.mm', '.m', '.h')):
        raise ValueError(f"Invalid source file extension: {source_file}")
    
    # Split path and extension
    base_path, ext = os.path.splitext(source_file)
    
    # For header files, prefer .mm for tests
    test_ext = '.mm' if ext == '.h' else ext
    
    # Check if test file already exists
    test_path = f"{base_path}_unittest{test_ext}"
    
    return test_path


def find_existing_test_file(source_file: str) -> Optional[str]:
    """Finds existing test file for the given source file.
    
    Args:
        source_file: Path to the source file
        
    Returns:
        Path to existing test file if found, None otherwise
    """
    src_root = get_chromium_src_root()
    test_path = calculate_test_file_path(source_file)
    full_test_path = src_root / test_path
    
    if full_test_path.exists():
        return test_path
    
    return None


# ============================================================================
# PATTERN DETECTION ENGINE (Layer 3)
# ============================================================================

def load_pattern_database() -> Dict:
    """Loads the pattern database from ios_test_patterns.json.
    
    Returns:
        Pattern database dict with 'patterns' key containing list of patterns
    """
    import json
    
    # Get script directory (where server.py is located)
    script_dir = Path(__file__).parent
    pattern_db_path = script_dir / "ios_test_patterns.json"
    
    if not pattern_db_path.exists():
        return {"patterns": []}
    
    try:
        with open(pattern_db_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!]️ Warning: Failed to load pattern database: {e}")
        return {"patterns": []}


def extract_source_features(source_file: str, source_content: str, 
                            testable_elements: Dict) -> Dict:
    """Extracts features from source file for pattern matching.
    
    Args:
        source_file: Path to source file (relative to chromium src)
        source_content: Content of source file
        testable_elements: Dict with interfaces/implementations
        
    Returns:
        Dict with keys: class_name, base_class, path, imports
    """
    features = {
        "class_name": "",
        "base_class": "",
        "path": source_file.lower(),
        "imports": []
    }
    
    # Extract class name
    if testable_elements.get('implementations'):
        features['class_name'] = testable_elements['implementations'][0]
    elif testable_elements.get('interfaces'):
        features['class_name'] = testable_elements['interfaces'][0]
    
    # Extract base class from @interface or class declaration
    import re
    
    if features['class_name']:
        # Objective-C: @interface ClassName : BaseClass
        interface_match = re.search(
            r'@interface\s+' + re.escape(features['class_name']) + r'\s*:\s*(\w+)',
            source_content
        )
        if interface_match:
            features['base_class'] = interface_match.group(1)
        
        # C++: class ClassName : public BaseClass
        class_match = re.search(
            r'class\s+' + re.escape(features['class_name']) + r'\s*:\s*public\s+(\w+)',
            source_content
        )
        if class_match:
            features['base_class'] = class_match.group(1)
    else:
        # Fallback 1: Extract from @interface or class declarations in source
        interface_match = re.search(r'@interface\s+(\w+)\s*:\s*(\w+)', source_content)
        if interface_match:
            features['class_name'] = interface_match.group(1)
            features['base_class'] = interface_match.group(2)
        else:
            class_match = re.search(r'class\s+(\w+)\s*:\s*public\s+(\w+)', source_content)
            if class_match:
                features['class_name'] = class_match.group(1)
                features['base_class'] = class_match.group(2)
            else:
                # Fallback 2: Extract standalone class/struct definition (no inheritance)
                # class ClassName {  or  struct ClassName {
                standalone_match = re.search(r'(?:class|struct)\s+(\w+)\s*\{', source_content)
                if standalone_match:
                    features['class_name'] = standalone_match.group(1)
                else:
                    # Fallback 3: Extract from namespace (for C++ utility files)
                    # namespace foo { ... } → use "foo" related classes
                    namespace_match = re.search(r'namespace\s+(\w+)', source_content)
                    if namespace_match:
                        # Use first function/struct name in namespace
                        func_match = re.search(r'(?:struct|class)\s+(\w+)', source_content)
                        if func_match:
                            features['class_name'] = func_match.group(1)
    
    # Final fallback: If still no class_name, derive from filename for pattern matching
    # This ensures pattern matching works even for pure utility files
    if not features['class_name']:
        import os
        filename = os.path.basename(source_file)
        name_without_ext = os.path.splitext(filename)[0]
        # Remove _unittest suffix if present
        name_without_ext = name_without_ext.replace('_unittest', '')
        # Convert snake_case to PascalCase for pattern matching
        # e.g., "ios_user_agent_config" -> "IosUserAgentConfig"
        parts = name_without_ext.split('_')
        features['class_name'] = ''.join(word.capitalize() for word in parts)
    
    # Extract imports (first 50 lines usually contain imports)
    import_lines = source_content.split('\n')[:50]
    for line in import_lines:
        # #import "path/to/file.h"
        import_match = re.search(r'#import\s+"([^"]+)"', line)
        if import_match:
            features['imports'].append(import_match.group(1))
    
    return features


def calculate_pattern_match_score(features: Dict, pattern: Dict) -> float:
    """Calculates how well source features match a pattern.
    
    Args:
        features: Source features from extract_source_features()
        pattern: Pattern dict from database
        
    Returns:
        Score between 0.0 and 1.0, where 1.0 is perfect match
    """
    import re
    
    rules = pattern.get('detection_rules', [])
    score = 0.0
    
    # Process each detection rule
    for rule in rules:
        field = rule.get('field', '')
        rule_type = rule.get('type', '')
        pattern_str = rule.get('pattern', '')
        weight = rule.get('weight', 0.0)
        
        # Get the feature value to check
        feature_value = ''
        if field == 'class_name':
            feature_value = features['class_name'].lower()
        elif field == 'path':
            feature_value = features['path'].lower()
        elif field == 'base_class':
            feature_value = features['base_class'].lower()
        elif field == 'imports':
            feature_value = '\n'.join(features['imports']).lower()
        else:
            continue
        
        # Apply the rule
        matched = False
        if rule_type == 'regex':
            if pattern_str and re.search(pattern_str.lower(), feature_value):
                matched = True
        elif rule_type == 'contains':
            if pattern_str and pattern_str.lower() in feature_value:
                matched = True
        elif rule_type == 'not_contains':
            if pattern_str and pattern_str.lower() not in feature_value:
                matched = True
        
        if matched:
            score += weight
    
    return score


def detect_test_pattern_with_examples(
    source_file: str,
    source_content: str,
    testable_elements: Dict
) -> Dict:
    """Returns all available patterns for AI to select - NO auto-scoring.
    
    This function does NOT auto-select patterns. Instead, it provides:
    1. Complete list of all available patterns
    2. Source code preview for AI analysis  
    3. Instructions for AI to make intelligent selection
    
    The AI (Copilot) will read the source code and choose the most appropriate
    pattern based on semantic understanding, not regex matching.
    
    Args:
        source_file: Path to source file (relative to chromium src)
        source_content: Content of source file
        testable_elements: Dict with interfaces/implementations
        
    Returns:
        Dict with keys:
        - all_patterns: Complete list of all patterns (unsorted)
        - source_preview: Source code for AI analysis
        - instruction: How AI should select pattern
        - default_pattern: Simple fallback (not a recommendation)
    """
    # Load pattern database
    db = load_pattern_database()
    
    if not db.get('patterns'):
        return {
            'all_patterns': [],
            'source_preview': source_content[:2000],
            'source_file': source_file,
            'instruction': 'No patterns available, use simple test structure',
            'default_pattern': {
                'pattern_id': 'simple_class_pattern',
                'template': '',
                'example_files': []
            }
        }
    
    # Prepare all patterns - NO scoring, just list them
    all_patterns = []
    
    for pattern in db['patterns']:
        all_patterns.append({
            'pattern_id': pattern['pattern_name'] + '_pattern',
            'pattern_name': pattern.get('pattern_name', 'unknown'),
            'display_name': pattern.get('display_name', pattern['pattern_name']),
            'description': pattern.get('description', ''),
            'template': pattern.get('test_template', ''),
            'example_files': pattern.get('example_files', [])[:5],
            'total_matches': pattern.get('total_matches', 0)
        })
    
    # Source preview for AI analysis (first 150 lines)
    source_lines = source_content.split('\n')[:150]
    source_preview = '\n'.join(source_lines)
    
    return {
        'all_patterns': all_patterns,
        'source_preview': source_preview,
        'source_file': source_file,
        'instruction': (
            'AI PATTERN SELECTION (Required):\n'
            '1. READ the source file completely to understand its purpose\n'
            '2. REVIEW all available patterns and their descriptions\n'
            '3. COMPARE source code with example files from each pattern\n'
            '4. SELECT the pattern that matches the code\'s semantic purpose\n'
            '5. USE that pattern\'s template and examples for generation\n'
            '\n'
            'Do NOT rely on auto-scoring. Make your own judgment based on code analysis.'
        ),
        # Default pattern (not a recommendation, just a fallback)
        'default_pattern': {
            'pattern_id': 'simple_class_pattern',
            'template': '',
            'example_files': []
        }
    }


def read_file_content(file_path: str) -> str:
    """Reads and returns the content of a file.
    
    Args:
        file_path: Path relative to chromium src root
        
    Returns:
        File content as string
    """
    src_root = get_chromium_src_root()
    full_path = src_root / file_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def find_build_gn_file(source_file: str) -> Optional[str]:
    """Finds the BUILD.gn file that should contain the test target.
    
    Args:
        source_file: Path to the source file
        
    Returns:
        Path to BUILD.gn file if found, None otherwise
    """
    src_root = get_chromium_src_root()
    current_dir = Path(source_file).parent
    
    # Search upwards for BUILD.gn
    while True:
        build_gn_path = src_root / current_dir / 'BUILD.gn'
        if build_gn_path.exists():
            return str(current_dir / 'BUILD.gn')
        
        # Stop at ios/chrome level
        if str(current_dir) == 'ios/chrome' or str(current_dir) == 'ios':
            break
            
        # Move up one directory
        if current_dir.parent == current_dir:
            break
        current_dir = current_dir.parent
    
    return None


def analyze_existing_tests(test_file_content: str) -> Dict:
    """Analyzes existing test file to understand coverage.
    
    Args:
        test_file_content: Content of the test file
        
    Returns:
        Dictionary with test analysis including:
        - test_count: Number of test cases
        - test_names: List of test case names
        - test_fixtures: List of test fixture classes
        - tested_methods: Methods that have test coverage
    """
    analysis = {
        'test_count': 0,
        'test_names': [],
        'test_fixtures': [],
        'tested_methods': set(),
    }
    
    # Find TEST and TEST_F macros
    test_pattern = re.compile(r'TEST(?:_F)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)')
    for match in test_pattern.finditer(test_file_content):
        fixture, test_name = match.groups()
        analysis['test_count'] += 1
        analysis['test_names'].append(test_name)
        if fixture not in analysis['test_fixtures']:
            analysis['test_fixtures'].append(fixture)
    
    # Find tested methods (methods called in tests)
    # This is a simple heuristic - looks for method calls
    method_call_pattern = re.compile(r'\[(?:self|[\w]+)\s+(\w+)(?:\]|:)')
    for match in method_call_pattern.finditer(test_file_content):
        method_name = match.group(1)
        if not method_name.startswith('test'):
            analysis['tested_methods'].add(method_name)
    
    # Convert set to list for JSON serialization
    analysis['tested_methods'] = list(analysis['tested_methods'])
    
    return analysis


def parse_build_gn_for_deps(source_file: str) -> List[str]:
    """Parses BUILD.gn file to find the actual dependencies of the source file.
    
    Args:
        source_file: Path to the source file (e.g., 'ios/chrome/app/profile/foo.mm')
        
    Returns:
        List of GN dependency targets from the source file's BUILD.gn
    """
    try:
        src_root = get_chromium_src_root()
        source_dir = Path(source_file).parent
        build_gn_path = src_root / source_dir / 'BUILD.gn'
        
        if not build_gn_path.exists():
            return []
        
        build_gn_content = build_gn_path.read_text(encoding='utf-8')
        source_basename = os.path.basename(source_file)
        
        # Find the target that contains this source file
        # Look for source_set(), component(), or static_library() that includes this file
        target_pattern = re.compile(
            r'(source_set|component|static_library|executable)\s*\(\s*"([^"]+)"\s*\)\s*\{([^}]*)\}',
            re.DOTALL
        )
        
        deps = []
        for match in target_pattern.finditer(build_gn_content):
            target_type, target_name, target_body = match.groups()
            
            # Check if this target contains our source file
            if source_basename in target_body or source_file in target_body:
                # Extract deps from this target
                deps_match = re.search(r'deps\s*=\s*\[([^\]]*)\]', target_body, re.DOTALL)
                if deps_match:
                    deps_content = deps_match.group(1)
                    # Extract quoted strings (dependencies)
                    dep_pattern = re.compile(r'"([^"]+)"')
                    for dep_match in dep_pattern.finditer(deps_content):
                        dep = dep_match.group(1)
                        # Filter out non-relevant deps (like testonly targets)
                        if ':' in dep or dep.startswith('//'):
                            deps.append(dep)
                break
        
        return deps
    except Exception:
        # If parsing fails, return empty list
        return []


def extract_dependencies_from_source(source_content: str, source_file: str) -> Dict:
    """Extracts potential dependencies needed for testing.
    
    Args:
        source_content: Content of the source file
        source_file: Path to the source file
        
    Returns:
        Dictionary with:
        - imports: List of imported headers
        - suggested_deps: List of suggested GN dependencies
        - common_test_deps: Standard test dependencies needed
    """
    imports = []
    suggested_deps = []
    
    # First, try to get actual dependencies from the source file's BUILD.gn
    actual_deps = parse_build_gn_for_deps(source_file)
    if actual_deps:
        suggested_deps.extend(actual_deps)
    
    # Extract #import statements for additional context
    import_pattern = re.compile(r'#import\s+[<"]([^>"]+)[>"]')
    for match in import_pattern.finditer(source_content):
        header = match.group(1)
        imports.append(header)
        
        # Map common headers to GN dependencies (only if not already found in BUILD.gn)
        if 'base/' in header:
            if '//base' not in suggested_deps:
                suggested_deps.append('//base')
        if 'components/' in header and 'test' not in header:
            # Only suggest top-level component deps, user needs to refine
            comp_path = header.split('/')[1]
            dep = f'//components/{comp_path}'
            if dep not in suggested_deps and len(suggested_deps) < 10:
                suggested_deps.append(dep)
    
    # Common test dependencies - these are ESSENTIAL for compilation
    common_test_deps = [
        '//testing/gtest',
        '//testing/gmock',
        '//ios/chrome/test:test_support',
        '//base',
        '//base/test:test_support',
    ]
    
    # Add OCMock if we detect Objective-C classes/protocols
    if '@interface' in source_content or '@protocol' in source_content:
        if '//third_party/ocmock' not in common_test_deps:
            common_test_deps.append('//third_party/ocmock')
    
    return {
        'imports': imports,
        'suggested_deps': suggested_deps,
        'common_test_deps': common_test_deps,
        'deps_from_build_gn': len(actual_deps) > 0,  # Indicate if we found actual deps
    }


def find_similar_test_files(source_file: str) -> List[str]:
    """Finds similar test files in the same directory for reference.
    
    Args:
        source_file: Path to source file
        
    Returns:
        List of paths to similar test files
    """
    try:
        src_root = get_chromium_src_root()
        source_dir = Path(source_file).parent
        test_dir = src_root / source_dir
        
        # Find all *_unittest.mm files in the same directory
        similar_tests = []
        if test_dir.exists():
            for test_file in test_dir.glob('*_unittest.mm'):
                similar_tests.append(str(test_file.relative_to(src_root)))
                if len(similar_tests) >= 3:  # Limit to 3 examples
                    break
        
        return similar_tests
    except Exception:
        return []


def analyze_existing_test_patterns(test_file_path: str) -> Dict:
    """Analyzes an existing test file to learn patterns.
    
    Args:
        test_file_path: Path to test file
        
    Returns:
        Dictionary with patterns found:
        - uses_mocks: bool
        - setup_pattern: str (how SetUp is implemented)
        - common_assertions: list
        - helper_methods: list
    """
    try:
        content = read_file_content(test_file_path)
        
        patterns = {
            'uses_mocks': False,
            'uses_ocmock': False,
            'setup_creates_object': False,
            'has_helper_methods': False,
            'common_imports': [],
            'common_assertions': []
        }
        
        # Check for mock usage
        if 'OCMock' in content or 'OCMStub' in content:
            patterns['uses_ocmock'] = True
            patterns['uses_mocks'] = True
        if 'gmock' in content or 'MockFunction' in content:
            patterns['uses_mocks'] = True
        
        # Check if SetUp creates object
        if re.search(r'void SetUp\(\).*?\[\[.*alloc\] init\]', content, re.DOTALL):
            patterns['setup_creates_object'] = True
        
        # Find common imports
        import_pattern = re.compile(r'#import\s+"([^"]+)"')
        for match in import_pattern.finditer(content):
            header = match.group(1)
            if 'test' in header.lower() or 'mock' in header.lower():
                patterns['common_imports'].append(header)
        
        # Find helper methods
        if re.search(r'^\s*\w+\s+\w+Helper', content, re.MULTILINE):
            patterns['has_helper_methods'] = True
        
        # Find common assertion patterns
        if 'EXPECT_OCMOCK_VERIFY' in content:
            patterns['common_assertions'].append('EXPECT_OCMOCK_VERIFY')
        if 'ASSERT_NE' in content:
            patterns['common_assertions'].append('ASSERT_NE')
        
        return patterns
    except Exception:
        return {
            'uses_mocks': False,
            'uses_ocmock': False,
            'setup_creates_object': False,
            'has_helper_methods': False,
            'common_imports': [],
            'common_assertions': []
        }


def method_has_parameters(full_signature: str) -> bool:
    """Check if method signature has parameters (contains ':')."""
    return ':' in full_signature


def generate_test_content(
    source_file: str,
    test_file_path: str,
    testable_elements: Dict,
    test_type: str = 'comprehensive'
) -> str:
    """Generates actual test file content with patterns learned from similar tests.
    
    Args:
        source_file: Path to source file
        test_file_path: Path where test will be saved
        testable_elements: Dict with interfaces, methods, functions
        test_type: 'comprehensive', 'basic', or 'missing'
        
    Returns:
        Complete test file content
    """
    # Defensive check: ensure testable_elements is a dict
    if not isinstance(testable_elements, dict):
        testable_elements = {
            'interfaces': [],
            'implementations': [],
            'methods': [],
            'properties': {},
            'method_details': {}
        }
    
    source_basename = os.path.basename(source_file)
    source_name = os.path.splitext(source_basename)[0]
    test_basename = os.path.basename(test_file_path)
    
    # Determine if Edge-specific
    is_edge = is_edge_file(source_file)
    
    # Learn from similar tests in the same directory
    similar_tests = find_similar_test_files(source_file)
    patterns = {'uses_mocks': False, 'uses_ocmock': False, 'setup_creates_object': False}
    
    if similar_tests:
        # Analyze the first similar test for patterns
        result = analyze_existing_test_patterns(similar_tests[0])
        if isinstance(result, dict):
            patterns = result
    
    # Determine primary class name
    if testable_elements['implementations']:
        class_name = testable_elements['implementations'][0]
    elif testable_elements['interfaces']:
        class_name = testable_elements['interfaces'][0]
    else:
        class_name = source_name.replace('_', ' ').title().replace(' ', '')
    
    # 🆕 Use intelligent pattern detection engine
    try:
        pattern_info = detect_test_pattern_with_examples(
            source_file,
            read_file_content(source_file),
            testable_elements
        )
        # Ensure pattern_info is a dict
        if not isinstance(pattern_info, dict):
            pattern_info = {
                'pattern_id': 'simple_class_pattern',
                'confidence': 0.0,
                'example_files': [],
                'template': ''
            }
    except Exception:
        pattern_info = {
            'pattern_id': 'simple_class_pattern',
            'confidence': 0.0,
            'example_files': [],
            'template': ''
        }
    
    # Get selected pattern (backward compatible) or let AI choose from top_matches
    # Get default pattern (NO auto-selection, just a fallback)
    default_pattern = pattern_info.get('default_pattern', {})
    pattern_id = default_pattern.get('pattern_id', 'simple_class_pattern')
    pattern_template = default_pattern.get('template', '')
    example_files = default_pattern.get('example_files', [])
    
    # Make all patterns available for AI selection
    all_patterns = pattern_info.get('all_patterns', [])
    
    # Extract object reference from pattern template (no hardcoding)
    # Pattern template should contain object reference info
    object_ref = pattern_info.get('object_ref', 'test_object_')
    
    # Log pattern detection result
    sys.stderr.write(f"\n[PATTERN] Loaded {len(all_patterns)} available patterns\n")
    sys.stderr.write(f"[PATTERN] AI must select pattern by analyzing source code\n")
    sys.stderr.write(f"[PATTERN] Default fallback: {pattern_id}\n")
    sys.stderr.flush()
    
    # Copyright header with AI pattern selection guidance
    content = f"""// Copyright (C) Microsoft Corporation. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// ============================================================================
// ⚠️ ⚠️ ⚠️  [DELETE MARKERS] - READ THIS FIRST  ⚠️ ⚠️ ⚠️
// ============================================================================
//
// This file contains TWO sections that MUST BE DELETED after implementation:
//
//   [DELETE_SECTION_1] Pattern selection list (lines 11-~{50 + len(all_patterns) * 4})
//   [DELETE_SECTION_2] Enhancement instructions (lines ~{55 + len(all_patterns) * 4}-~{75 + len(all_patterns) * 4})
//
// Keep TODO comments in your test code if complex logic needs review.
//
// After deleting sections 1-2, ADD at very end:
//   // Selected pattern: <pattern_name>
//   // CONFIDENCE_SCORE: XX/100 - [justification]
//
// ============================================================================
// [DELETE_SECTION_1_START] PATTERN SELECTION - DELETE AFTER CHOOSING
// ============================================================================
//
// TASK: Read source file {source_file} and select matching pattern
//
// AVAILABLE PATTERNS ({len(all_patterns)} total):
"""
    
    # List ALL patterns (not scored, just listed)
    for i, pattern in enumerate(all_patterns, 1):
        content += f"//\n//   {i}. {pattern['pattern_id']}"
        if pattern.get('description'):
            content += f" - {pattern['description']}"
        content += "\n"
        if pattern.get('example_files'):
            content += f"//      Example: {pattern['example_files'][0]}\n"
        if pattern.get('total_matches'):
            content += f"//      Used in: {pattern['total_matches']} tests\n"
    
    content += f"""//
// ============================================================================
// [DELETE_SECTION_1_END] Delete from [DELETE_SECTION_1_START] to here
// ============================================================================
"""
    
    content += """//
// ============================================================================
// [DELETE_SECTION_2_START] ENHANCEMENT INSTRUCTIONS - DELETE AFTER IMPLEMENTING
// ============================================================================
//
// IMPLEMENTATION STEPS:
//
//   1. Select a pattern from [DELETE_SECTION_1] above
//   2. Read the pattern's example files to understand structure
//   3. Add all necessary #import statements
//   4. Implement test fixture (SetUp/TearDown if needed)
//   5. Replace all TODO comments with actual test code
//   6. Add proper assertions (3+ per test)
//   7. Delete [DELETE_SECTION_1] and [DELETE_SECTION_2]
//   8. Keep any TODO comments for logic that needs domain expertise
//   9. Add at end: // Selected pattern: <pattern_name>
//                  // CONFIDENCE_SCORE: XX/100 - [justification]
//
// ============================================================================
// [DELETE_SECTION_2_END] Delete from [DELETE_SECTION_2_START] to here  
// ============================================================================
"""
    
    # ============================================================================
    # Minimal imports - Copilot will add more based on template
    # ============================================================================
    imports = []
    header_file = source_file.replace('.mm', '.h').replace('.cc', '.h')
    imports.append(header_file)
    imports.append('testing/gtest/include/gtest/gtest.h')
    imports.append('testing/platform_test.h')
    
    # Add common test imports from similar tests
    for common_import in patterns.get('common_imports', [])[:3]:
        if common_import not in imports:
            imports.append(common_import)
    
    for import_path in sorted(set(imports)):
        content += f'#import "{import_path}"\n'
    
    content += '\n'
    content += '// TODO: Add additional imports based on the pattern template above\n'
    content += '// Study the example files to see what imports are needed\n\n'
    
    # ============================================================================
    # Minimal test fixture - Copilot will implement based on template
    # ============================================================================
    fixture_name = f'{class_name}Test'
    
    content += f'// TODO: Implement test fixture following the pattern template above\n'
    content += f'// Reference the example files to see the exact structure\n'
    if similar_tests:
        content += f'// Similar test: {os.path.basename(similar_tests[0])}\n'
    content += f'class {fixture_name} : public PlatformTest {{\n'
    content += ' protected:\n'
    content += '  // TODO: Add SetUp/TearDown or constructor/destructor based on pattern\n'
    content += '  // TODO: Add member variables for test infrastructure\n'
    content += '};\n\n'
    
    # ============================================================================
    # Minimal test stubs - Copilot will implement based on template
    # ============================================================================
    
    # Add method information as comments for Copilot
    methods = testable_elements.get('methods', [])
    properties = testable_elements.get('properties', [])
    
    content += f'// TODO: Implement tests following the pattern template above\n'
    content += f'// The following testable elements were found:\n'
    content += f'//\n'
    
    if methods:
        content += f'// Methods to test ({len(methods)} total):\n'
        for method in methods[:10]:  # Show first 10
            content += f'//   - {method}\n'
    
    if properties:
        content += f'//\n// Properties to test ({len(properties)} total):\n'
        # Handle list of dicts format
        for i, prop in enumerate(properties[:5]):  # Show first 5
            prop_name = prop.get('name', 'unknown') if isinstance(prop, dict) else str(prop)
            content += f'//   - {prop_name}\n'
    
    content += f'//\n// Generate appropriate tests based on the pattern template\n\n'
    
    # Add a basic initialization test stub
    content += f'TEST_F({fixture_name}, Initialization) {{\n'
    content += f'  // TODO: Implement initialization test based on pattern template\n'
    content += f'  // FAIL("Test not implemented");\n'
    content += '}\n\n'
    
    # Add TODO for additional tests
    content += f'// TODO: Add more test cases based on:\n'
    content += f'//  1. The pattern template above\n'
    content += f'//  2. The example files listed\n'
    content += f'//  3. The methods and properties shown above\n\n'
    
    # Final reminder at the end
    content += '\n'
    content += '// ============================================================================\n'
    content += '// FINAL STEPS AFTER IMPLEMENTATION\n'
    content += '// ============================================================================\n'
    content += '// 1. Delete [DELETE_SECTION_1] (pattern list at top)\n'
    content += '// 2. Delete [DELETE_SECTION_2] (enhancement instructions)\n'
    content += '// 3. Keep any TODO comments for complex logic that needs review\n'
    content += '// 4. Add test summary at end of file (see template below):\n'
    content += '// ============================================================================\n'
    content += '\n'
    content += '// ============================================================================\n'
    content += '// TEST SUMMARY (Add this section after implementation)\n'
    content += '// ============================================================================\n'
    content += '//\n'
    content += '// Selected pattern: <pattern_name>\n'
    content += '//\n'
    content += '// Test coverage:\n'
    content += '//   - List key methods/features tested\n'
    content += '//   - Edge cases covered\n'
    content += '//   - Integration points verified\n'
    content += '//\n'
    content += '// Not covered (if any):\n'
    content += '//   - List any methods/scenarios not tested\n'
    content += '//   - Explain why (e.g., requires integration test, UI test, etc.)\n'
    content += '//\n'
    content += '// CONFIDENCE_SCORE: XX/100\n'
    content += '// Justification: [Brief explanation of score]\n'
    content += '//\n'
    content += '// ============================================================================\n'

    return content


def generate_quality_report(validation: Dict) -> str:
    """Generate a formatted quality report for display.
    
    P1 Optimization: Makes quality issues visible to Copilot.
    """
    if not validation:
        return ""
    
    score = validation.get('quality_score', 0)
    errors = validation.get('errors', [])
    warnings = validation.get('warnings', [])
    suggestions = validation.get('suggestions', [])
    metrics = validation.get('metrics', {})
    
    report = f"\n{'='*60}\n"
    report += f"[REPORT] TEST QUALITY REPORT\n"
    report += f"{'='*60}\n"
    
    # Quality score with emoji indicator
    if score >= 80:
        indicator = "[OK]"
    elif score >= 60:
        indicator = "[!]️"
    else:
        indicator = "[FAIL]"
    report += f"Quality Score: {score}/100 {indicator}\n\n"
    
    # Metrics
    if metrics:
        report += f"[METRICS] Metrics:\n"
        report += f"  • Tests: {metrics.get('test_count', 0)}\n"
        report += f"  • Assertions: {metrics.get('assertion_count', 0)}\n"
        report += f"  • Assertions/Test: {metrics.get('assertions_per_test', 0):.1f}\n"
        if metrics.get('todo_count', 0) > 0:
            report += f"  • TODOs: {metrics.get('todo_count', 0)} [!]️\n"
        report += "\n"
    
    # Errors
    if errors:
        report += f"[FAIL] ERRORS ({len(errors)}):\n"
        for err in errors[:3]:
            report += f"  • {err}\n"
        if len(errors) > 3:
            report += f"  • ... and {len(errors) - 3} more\n"
        report += "\n"
    
    # Warnings
    if warnings:
        report += f"[!]️  WARNINGS ({len(warnings)}):\n"
        for warn in warnings[:3]:
            report += f"  • {warn}\n"
        if len(warnings) > 3:
            report += f"  • ... and {len(warnings) - 3} more\n"
        report += "\n"
    
    # Suggestions
    if suggestions:
        report += f"[TIP] SUGGESTIONS ({len(suggestions)}):\n"
        for sug in suggestions[:3]:
            report += f"  • {sug}\n"
        if len(suggestions) > 3:
            report += f"  • ... and {len(suggestions) - 3} more\n"
        report += "\n"
    
    # Recommendation
    if score < 70:
        report += "[SEARCH] RECOMMENDATION: Consider improving test quality before proceeding\n"
    elif score < 85:
        report += "[TIP] RECOMMENDATION: Good quality, minor improvements suggested\n"
    else:
        report += "✨ RECOMMENDATION: Excellent quality!\n"
    
    report += f"{'='*60}\n"
    return report


def clean_delete_sections_from_test_file(test_file_path: str) -> Dict:
    """Remove DELETE_SECTION markers from test file after Copilot enhancement.
    
    This function removes the template guidance sections that are meant to be
    deleted after implementation:
    - [DELETE_SECTION_1_START] to [DELETE_SECTION_1_END] (pattern list)
    - [DELETE_SECTION_2_START] to [DELETE_SECTION_2_END] (enhancement instructions)
    
    Args:
        test_file_path: Path to test file (relative to Chromium src root)
        
    Returns:
        Dictionary with:
        - cleaned: Whether any sections were removed
        - sections_removed: List of section names removed
        - line_count_before: Original line count
        - line_count_after: Line count after cleaning
    """
    try:
        src_root = get_chromium_src_root()
        full_path = src_root / test_file_path
        
        if not full_path.exists():
            return {
                'error': f'Test file not found: {test_file_path}',
                'cleaned': False
            }
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_line_count = content.count('\n')
        sections_removed = []
        
        # Remove DELETE_SECTION_1 (pattern list)
        section1_pattern = r'// \[DELETE_SECTION_1_START\].*?// \[DELETE_SECTION_1_END\].*?\n'
        if re.search(section1_pattern, content, re.DOTALL):
            content = re.sub(section1_pattern, '', content, flags=re.DOTALL)
            sections_removed.append('DELETE_SECTION_1 (pattern list)')
        
        # Remove DELETE_SECTION_2 (enhancement instructions)
        section2_pattern = r'// \[DELETE_SECTION_2_START\].*?// \[DELETE_SECTION_2_END\].*?\n'
        if re.search(section2_pattern, content, re.DOTALL):
            content = re.sub(section2_pattern, '', content, flags=re.DOTALL)
            sections_removed.append('DELETE_SECTION_2 (enhancement instructions)')
        
        # Remove the top-level DELETE MARKERS warning block
        markers_pattern = r'// ============================================================================\n// ⚠️ ⚠️ ⚠️  \[DELETE MARKERS\].*?// ============================================================================\n'
        if re.search(markers_pattern, content, re.DOTALL):
            content = re.sub(markers_pattern, '', content, flags=re.DOTALL)
            sections_removed.append('DELETE MARKERS warning')
        
        new_line_count = content.count('\n')
        
        # Only write back if something was actually removed
        if sections_removed:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            sys.stderr.write(f"\n{'='*80}\n")
            sys.stderr.write(f"[CLEAN] Auto-cleaned DELETE sections from test file\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"File: {test_file_path}\n")
            sys.stderr.write(f"Removed {len(sections_removed)} section(s):\n")
            for section in sections_removed:
                sys.stderr.write(f"  - {section}\n")
            sys.stderr.write(f"Lines: {original_line_count} → {new_line_count} ({original_line_count - new_line_count} removed)\n")
            sys.stderr.write(f"{'='*80}\n\n")
            sys.stderr.flush()
            
            return {
                'cleaned': True,
                'sections_removed': sections_removed,
                'line_count_before': original_line_count,
                'line_count_after': new_line_count,
                'lines_removed': original_line_count - new_line_count
            }
        else:
            return {
                'cleaned': False,
                'sections_removed': [],
                'message': 'No DELETE sections found in file'
            }
            
    except Exception as e:
        return {
            'error': str(e),
            'cleaned': False
        }


def generate_compilation_fix_instructions(
    errors_found: List[Dict],
    fix_suggestions: List[Dict],
    test_file_path: str,
    auto_fixable_count: int
) -> str:
    """Generate formatted fix instructions for compilation errors.
    
    P0 Optimization: Provides actionable fix instructions to Copilot.
    """
    instructions = f"\n{'='*60}\n"
    instructions += f"[FIX] COMPILATION ERROR AUTO-FIX GUIDE\n"
    instructions += f"{'='*60}\n\n"
    
    if auto_fixable_count > 0:
        instructions += f"[OK] {auto_fixable_count} errors can be AUTO-FIXED\n\n"
        instructions += f"[NOTE] TO APPLY FIXES:\n"
        instructions += f"Use multi_replace_string_in_file with these changes:\n\n"
        
        fix_number = 1
        for i, error in enumerate(errors_found[:10]):
            if error['type'] in ['undefined_identifier', 'private_method_call']:
                instructions += f"{fix_number}. {error['type'].upper()}:\n"
                
                if error['type'] == 'undefined_identifier':
                    instructions += f"   Remove/comment: {error['identifier']}\n"
                    instructions += f"   Reason: Identifier not available in test scope\n"
                elif error['type'] == 'private_method_call':
                    instructions += f"   Remove: [{error['class']} {error['selector']}]\n"
                    instructions += f"   Reason: Cannot test private methods\n"
                
                instructions += "\n"
                fix_number += 1
        
        instructions += f"[TIP] TIP: Read test file first to see context, then apply fixes\n\n"
    
    manual_count = len(errors_found) - auto_fixable_count
    if manual_count > 0:
        instructions += f"[!]️  {manual_count} errors need MANUAL review:\n"
        for error in errors_found[:5]:
            if error['type'] not in ['undefined_identifier', 'private_method_call']:
                instructions += f"  • {error['type']}: Check priority_fixes for guidance\n"
        instructions += "\n"
    
    instructions += f"[LOOP] AFTER FIXING:\n"
    instructions += f"1. Use compile_ios_unittest to verify fixes\n"
    instructions += f"2. If errors persist, analyze again\n"
    instructions += f"3. Continue to next step when compilation succeeds\n"
    instructions += f"{'='*60}\n"
    
    return instructions


def validate_test_code_quality(content: str, source_file: str = None) -> Dict[str, any]:
    """Validates generated test code and returns detailed quality analysis.
    
    Args:
        content: Generated test file content
        source_file: Optional source file path for context
        
    Returns:
        Dictionary with validation results:
        - is_valid: bool - Overall validity
        - errors: List[str] - Critical errors that prevent compilation
        - warnings: List[str] - Non-critical issues
        - suggestions: List[str] - Improvement suggestions
        - quality_score: int - Quality score 0-100
        - auto_fixable: List[Dict] - Issues that can be auto-fixed
    """
    errors = []
    warnings = []
    suggestions = []
    auto_fixable = []
    
    # === CRITICAL ERRORS (Prevent Compilation) ===
    
    # Check for basic C++ syntax issues
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        errors.append(f'ERROR: Mismatched braces ({open_braces} open, {close_braces} close)')
    
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        errors.append(f'ERROR: Mismatched parentheses ({open_parens} open, {close_parens} close)')
    
    # Check for mismatched block comments
    if content.count('/*') != content.count('*/'):
        errors.append('ERROR: Mismatched block comments /* */')
        auto_fixable.append({
            'type': 'remove_block_comments',
            'description': 'Replace block comments with line comments'
        })
    
    # Check for non-existent headers
    if 'edge_test_support.h' in content:
        errors.append('ERROR: Contains non-existent header: edge_test_support.h')
        auto_fixable.append({
            'type': 'remove_header',
            'header': 'edge_test_support.h',
            'description': 'Remove non-existent header import'
        })
    
    # === WARNINGS (Likely Issues) ===
    
    # Check for proper test infrastructure
    if 'Coordinator' in content:
        if 'initWithBaseViewController:browser:' not in content:
            warnings.append('WARNING: Coordinator should use initWithBaseViewController:browser: initializer')
            auto_fixable.append({
                'type': 'fix_coordinator_init',
                'description': 'Update coordinator initialization pattern'
            })
    
    if 'Agent' in content and 'profile' in content.lower():
        if 'ProfileState' not in content:
            warnings.append('WARNING: ProfileAgent tests should include ProfileState setup')
    
    # Check for test quality - count assertions
    assertion_count = content.count('EXPECT_') + content.count('ASSERT_')
    test_count = content.count('TEST_F(')
    
    if test_count > 0:
        assertions_per_test = assertion_count / test_count
        if assertions_per_test < 1.5:
            warnings.append(f'WARNING: Low assertion density ({assertions_per_test:.1f} per test). Tests may be too simple.')
            suggestions.append('Add more meaningful assertions to verify actual behavior')
    
    # Check for overly simple tests (only checking nil)
    only_nil_checks = content.count('EXPECT_NE(') == assertion_count
    if only_nil_checks and assertion_count > 0:
        warnings.append('WARNING: All assertions only check for nil. Add behavior verification.')
        suggestions.append('Example: EXPECT_TRUE([obj isStarted]) instead of just EXPECT_NE(obj, nil)')
    
    # Check for TODO comments (incomplete tests)
    todo_count = content.count('TODO') + content.count('FIXME')
    if todo_count > test_count * 0.5:
        warnings.append(f'WARNING: {todo_count} TODO/FIXME comments found. Many tests are incomplete.')
    
    # === SUGGESTIONS (Best Practices) ===
    
    # Check for overly long comment blocks
    lines = content.split('\n')
    comment_block_length = 0
    max_comment_block = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('//'):
            comment_block_length += 1
            max_comment_block = max(max_comment_block, comment_block_length)
        else:
            comment_block_length = 0
    
    if max_comment_block > 10:
        suggestions.append(f'Consider breaking up long comment blocks ({max_comment_block} lines)')
    
    # Check for test naming conventions
    if 'TEST_F' in content:
        test_names = re.findall(r'TEST_F\([^,]+,\s*(\w+)\)', content)
        for name in test_names:
            if name.islower():
                suggestions.append(f'Test name "{name}" should use PascalCase (e.g., "{name.title()}")')
                break
    
    # Check for proper copyright header
    if 'Copyright (C) Microsoft Corporation. All rights reserved.' not in content:
        warnings.append('WARNING: Missing or incorrect copyright header')
    
    # === CALCULATE QUALITY SCORE ===
    quality_score = 100
    
    # Deduct for errors
    quality_score -= len(errors) * 20
    
    # Deduct for warnings
    quality_score -= len(warnings) * 5
    
    # Bonus for good practices
    if assertions_per_test > 2.0:
        quality_score += 10
    if todo_count == 0:
        quality_score += 5
    if not only_nil_checks:
        quality_score += 10
    
    quality_score = max(0, min(100, quality_score))
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions,
        'quality_score': quality_score,
        'auto_fixable': auto_fixable,
        'metrics': {
            'test_count': test_count,
            'assertion_count': assertion_count,
            'assertions_per_test': assertions_per_test if test_count > 0 else 0,
            'todo_count': todo_count
        }
    }


def write_test_file(test_file_path: str, content: str) -> Dict[str, any]:
    """Writes test content to file after validation.
    
    Args:
        test_file_path: Relative path to test file
        content: Test file content
        
    Returns:
        Dictionary with write result and validation info
    """
    try:
        # Validate code quality before writing
        validation = validate_test_code_quality(content)
        
        if validation['errors']:
            print("\n[FAIL] Critical errors found - file NOT written:")
            for error in validation['errors']:
                print(f"   {error}")
            return {
                'success': False,
                'validation': validation,
                'error': 'Critical validation errors'
            }
        
        if validation['warnings']:
            print("\n[!]️  Code quality warnings:")
            for warning in validation['warnings']:
                print(f"   {warning}")
        
        if validation['suggestions']:
            print("\n[TIP] Suggestions for improvement:")
            for suggestion in validation['suggestions']:
                print(f"   {suggestion}")
        
        print(f"\n[REPORT] Quality Score: {validation['quality_score']}/100")
        print()
        
        src_root = get_chromium_src_root()
        full_path = src_root / test_file_path
        
        # Create directory if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            'success': True,
            'validation': validation,
            'file_path': str(full_path)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def update_build_gn(
    build_gn_path: str,
    test_file_name: str,
    deps: List[str]
) -> Tuple[bool, str]:
    """Updates BUILD.gn to include the test file with proper dependencies.
    
    Args:
        build_gn_path: Path to BUILD.gn file
        test_file_name: Name of test file to add
        deps: List of dependencies from source analysis
        
    Returns:
        (success, message) tuple
    """
    try:
        src_root = get_chromium_src_root()
        full_path = src_root / build_gn_path
        
        if not full_path.exists():
            return False, f"BUILD.gn not found: {build_gn_path}"
        
        content = full_path.read_text(encoding='utf-8')
        
        # Check if test file already in BUILD.gn
        if test_file_name in content:
            return True, f"Test file already in BUILD.gn: {test_file_name}"
        
        # Ensure essential test dependencies are included
        essential_test_deps = [
            '//testing/gtest',
            '//ios/chrome/test:test_support',
        ]
        
        # Combine deps: essential + provided deps (deduplicated)
        all_deps = essential_test_deps.copy()
        for dep in deps:
            if dep not in all_deps:
                all_deps.append(dep)
        
        # Add common iOS test dependencies if not present
        ios_common_deps = [
            '//base',
            '//base/test:test_support',
        ]
        for dep in ios_common_deps:
            if dep not in all_deps and any(dep in d for d in all_deps):
                # Only add if we already have base-related deps
                if dep not in all_deps:
                    all_deps.append(dep)
        
        # Sort dependencies alphabetically
        all_deps = sorted(set(all_deps))
        
        # Find unit_tests target
        unit_tests_pattern = re.compile(
            r'(source_set\("unit_tests"\)\s*\{[^}]*sources\s*=\s*\[)([^\]]*)\]',
            re.DOTALL
        )
        
        match = unit_tests_pattern.search(content)
        if match:
            # Add to existing unit_tests target
            prefix = match.group(1)
            sources = match.group(2)
            
            # Parse existing source files
            existing_sources = []
            for line in sources.split('\n'):
                stripped = line.strip()
                if stripped and stripped.startswith('"') and stripped.endswith(('",', '"')):
                    # Extract filename
                    filename = stripped.strip('",').strip()
                    if filename:
                        existing_sources.append(filename)
            
            # Add new test file and sort alphabetically
            existing_sources.append(test_file_name)
            existing_sources.sort()
            
            # Rebuild sources list with proper formatting
            # Ensure first item is on a new line after 'sources = ['
            new_sources = '\n' + '\n'.join([f'    "{src}",' for src in existing_sources])
            new_sources += '\n  '
            
            new_content = content[:match.start()] + prefix + new_sources + ']' + content[match.end():]
            
            # Check if we need to add deps to existing target
            # Look for deps in the unit_tests target
            target_match = re.search(
                r'source_set\("unit_tests"\)\s*\{([^}]*)\}',
                new_content,
                re.DOTALL
            )
            if target_match:
                target_body = target_match.group(1)
                has_deps = 'deps' in target_body
                
                if not has_deps:
                    # Add deps section before closing brace (already sorted)
                    deps_section = '\n  deps = [\n'
                    for dep in all_deps[:15]:  # Limit to 15 most important deps
                        deps_section += f'    "{dep}",\n'
                    deps_section += '  ]\n'
                    
                    # Insert deps before closing brace
                    insert_pos = target_match.end() - 1
                    new_content = new_content[:insert_pos] + deps_section + new_content[insert_pos:]
            
            full_path.write_text(new_content, encoding='utf-8')
            return True, f"Added {test_file_name} to unit_tests (with {len(all_deps)} dependencies)"
        else:
            # Create new unit_tests target with proper structure
            # all_deps is already sorted alphabetically
            new_target = f'\nsource_set("unit_tests") {{\n'
            new_target += '  testonly = true\n'
            new_target += '  sources = [\n'
            new_target += f'    "{test_file_name}",\n'
            new_target += '  ]\n'
            new_target += '  deps = [\n'
            for dep in all_deps[:15]:  # Limit to 15 most important deps
                new_target += f'    "{dep}",\n'
            new_target += '  ]\n'
            new_target += '}\n'
            
            # Append to file
            new_content = content + new_target
            full_path.write_text(new_content, encoding='utf-8')
            return True, f"Created unit_tests target with {test_file_name} and {len(all_deps)} dependencies"
        
    except Exception as e:
        return False, f"Error updating BUILD.gn: {str(e)}"


def extract_testable_interfaces(source_content: str, header_content: str = None) -> Dict:
    """Extracts interfaces, classes, and methods from source code WITH DEEP ANALYSIS.
    
    IMPORTANT: Methods should be extracted from HEADER files (.h), not implementation files (.mm)!
    The header file contains the public API declarations.
    
    Args:
        source_content: Content of the source file (.mm)
        header_content: Content of the header file (.h) - PREFERRED source for methods!
        
    Returns:
        Dictionary with:
        - interfaces: List of @interface declarations
        - implementations: List of @implementation blocks
        - methods: List of method signatures (from header file if available)
        - functions: List of C++ functions
        - properties: List of @property declarations with types
        - instance_variables: Instance variables from @interface {...}
        - protocols: Protocols conformed to
        - class_hierarchy: Parent class information
        - method_details: Full method signatures with return types
    """
    result = {
        'interfaces': [],
        'implementations': [],
        'methods': [],
        'functions': [],
        'properties': [],
        'instance_variables': [],
        'protocols': [],
        'class_hierarchy': {},
        'method_details': {},
    }
    
    # PRIORITY 1: Extract methods from HEADER file (if available)
    # This is where the public API is declared!
    if header_content:
        # Extract @interface declarations with parent class hierarchy
        interface_with_parent = re.compile(
            r'@interface\s+(\w+)\s*:\s*(\w+)',
            re.MULTILINE
        )
        for match in interface_with_parent.finditer(header_content):
            class_name = match.group(1)
            parent_class = match.group(2)
            if class_name not in result['interfaces']:
                result['interfaces'].append(class_name)
            result['class_hierarchy'][class_name] = parent_class
        
        # Also handle @interface without explicit parent or with category/protocol
        interface_pattern = re.compile(
            r'@interface\s+(\w+)\s*(?::|\(|\{)',
            re.MULTILINE
        )
        for match in interface_pattern.finditer(header_content):
            if match.group(1) not in result['interfaces']:
                result['interfaces'].append(match.group(1))
        
        # Extract @property declarations with detailed type information
        property_pattern = re.compile(
            r'@property\s*\(([^)]+)\)\s*([^;]+?)\s+(\w+);',
            re.MULTILINE
        )
        for match in property_pattern.finditer(header_content):
            attributes = match.group(1)
            prop_type = match.group(2).strip()
            prop_name = match.group(3)
            result['properties'].append({
                'name': prop_name,
                'type': prop_type,
                'attributes': attributes
            })
        
        # Extract protocols conformed to
        protocol_pattern = re.compile(
            r'@interface\s+\w+\s*(?::\s*\w+)?\s*<([^>]+)>',
            re.MULTILINE
        )
        for match in protocol_pattern.finditer(header_content):
            protocols = [p.strip() for p in match.group(1).split(',')]
            result['protocols'].extend(protocols)
        
        # Detect key protocol implementations for intelligent test generation
        result['implements_profile_state_observer'] = 'ProfileStateObserver' in result['protocols']
        result['implements_scene_state_observer'] = 'SceneStateObserver' in result['protocols']
        
        # Extract instance variables from @interface {...}
        ivar_section = re.search(
            r'@interface\s+\w+[^{]*\{([^}]+)\}',
            header_content,
            re.MULTILINE | re.DOTALL
        )
        if ivar_section:
            ivar_lines = ivar_section.group(1).strip().split('\n')
            for line in ivar_lines:
                ivar_match = re.match(r'\s*([^\s]+)\s+([^;]+);', line.strip())
                if ivar_match:
                    result['instance_variables'].append({
                        'type': ivar_match.group(1),
                        'name': ivar_match.group(2).strip()
                    })
        
        # Extract Objective-C method declarations from header with FULL details
        # Look for methods between @interface and @end
        interface_blocks = re.findall(
            r'@interface\s+\w+.*?@end',
            header_content,
            re.DOTALL
        )
        
        for block in interface_blocks:
            # Extract FULL method signatures: - (returnType)methodName:(params)...
            full_method_pattern = re.findall(
                r'^([-+])\s*\(([^)]+)\)\s*([^;]+);',
                block,
                re.MULTILINE
            )
            
            for method_type, return_type, method_signature in full_method_pattern:
                # Extract the method selector (first part before ':' or entire name)
                selector_match = re.match(r'(\w+)', method_signature.strip())
                if selector_match:
                    method_name = selector_match.group(1)
                    if method_name not in result['methods']:
                        result['methods'].append(method_name)
                        # Store FULL method details for better test generation
                        result['method_details'][method_name] = {
                            'type': method_type,  # '-' for instance, '+' for class
                            'return_type': return_type.strip(),
                            'full_signature': method_signature.strip(),
                        }
    
    # FALLBACK: If no header content, extract from source file
    if not result['interfaces']:
        # Extract @interface declarations
        interface_pattern = re.compile(
            r'@interface\s+(\w+)\s*(?::|\(|\{)',
            re.MULTILINE
        )
        for match in interface_pattern.finditer(source_content):
            result['interfaces'].append(match.group(1))
    
    # Extract @implementation blocks from source
    impl_pattern = re.compile(
        r'@implementation\s+(\w+)',
        re.MULTILINE
    )
    for match in impl_pattern.finditer(source_content):
        result['implementations'].append(match.group(1))
    
    # CRITICAL: DO NOT extract private methods from implementation!
    # If header has no public methods, the class has NO testable public API.
    # Private methods in @implementation are NOT part of the public interface.
    # Tests should ONLY test public API declared in headers.
    # 
    # For classes with empty public interfaces (like DockingPromoProfileAgent),
    # we should only test:
    # 1. Initialization
    # 2. Inherited properties (like profileState from parent class)
    # 3. Protocol conformance
    # 
    # DO NOT add private methods to result['methods']!
    
    # Extract C++ classes from headers (if no Objective-C interfaces found)
    if not result['interfaces'] and (header_content or source_content):
        content_to_scan = header_content if header_content else source_content
        # Match: class ClassName { or class ClassName : public Base {
        cpp_class_pattern = re.compile(
            r'class\s+(\w+)(?:\s*:\s*public\s+\w+)?\s*{',
            re.MULTILINE
        )
        for match in cpp_class_pattern.finditer(content_to_scan):
            class_name = match.group(1)
            result['implementations'].append(class_name)
            # Extract parent class if exists
            parent_match = re.search(
                r'class\s+' + re.escape(class_name) + r'\s*:\s*public\s+(\w+)',
                content_to_scan
            )
            if parent_match:
                result['class_hierarchy'][class_name] = parent_match.group(1)
    
    # Extract C++ namespace functions from header
    content_to_scan = header_content if header_content else source_content
    # Match function declarations in headers: ReturnType FunctionName(params);
    func_decl_pattern = re.compile(
        r'^(?:[\w:]+\s+)+(\w+)\s*\([^)]*\)\s*;',
        re.MULTILINE
    )
    for match in func_decl_pattern.finditer(content_to_scan):
        func_name = match.group(1)
        # Skip common keywords and constructors matching class names
        if (func_name not in ['if', 'for', 'while', 'switch', 'return'] and
            func_name not in result['implementations'] and
            func_name not in result['interfaces']):
            result['functions'].append(func_name)
    
    # Also extract C++ function implementations (with body)
    func_impl_pattern = re.compile(
        r'^(?:static\s+)?(?:inline\s+)?[\w:]+\s+(\w+)\s*\([^)]*\)\s*{',
        re.MULTILINE
    )
    for match in func_impl_pattern.finditer(source_content):
        func_name = match.group(1)
        # Skip common keywords and duplicates
        if (func_name not in ['if', 'for', 'while', 'switch'] and
            func_name not in result['functions']):
            result['functions'].append(func_name)
    
    return result


# ============================================================================
# * PRIMARY TOOL: Step-by-Step Workflow (Visible Progress)
# ============================================================================

@mcp.tool(name='full_test_workflow', structured_output=False)
def full_test_workflow(source_file_path: str) -> str:
    """Generate iOS unit tests workflow - AUTOMATED END-TO-END EXECUTION.
    
    This tool EXECUTES the complete 6-step workflow automatically:
    
    [OK] AUTOMATIC STEPS (Steps 1-2):
      1. Analyzes source code structure
      2. Generates comprehensive test file with TODOs
    
    [INFO] GUIDED STEPS (Steps 3-6) - Returns TODO list with MCP tool requirements:
      3. Copilot enhances tests (read_file + replace_string_in_file)
      4. [REQUIRED] MUST call MCP tool: update_build_file_for_test (not manual edit)
      5. [REQUIRED] MUST call MCP tool: compile_ios_unittest (not run_in_terminal)
      6. [REQUIRED] MUST call MCP tool: run_ios_unittest (not run_in_terminal)
    
    [TARGET] KEY FEATURE: Returns a TODO list with explicit tool requirements
       for each remaining step, ensuring MCP tools are used correctly.
    
    Args:
        source_file_path: Path to the iOS source file (relative to Chromium src root)
        
    Returns:
        Formatted message with TODO list specifying which MCP tools to use
        for Steps 3-6. Each todo includes tool name and usage example.
    """
    import json
    from pathlib import Path
    
    sys.stderr.write("\n" + "="*80 + "\n")
    sys.stderr.write("[LAUNCH] FULL TEST WORKFLOW - AUTOMATED EXECUTION\n")
    sys.stderr.write("="*80 + "\n\n")
    sys.stderr.flush()
    
    try:
        # Check if test file already exists
        src_root = get_chromium_src_root()
        if source_file_path.endswith('.mm'):
            test_file_path = source_file_path[:-3] + '_unittest.mm'
        elif source_file_path.endswith('.m'):
            test_file_path = source_file_path[:-2] + '_unittest.mm'
        else:
            test_file_path = source_file_path + '_unittest.mm'
        
        test_file_full_path = src_root / test_file_path
        test_file_exists = test_file_full_path.exists()
        
        if test_file_exists:
            sys.stderr.write("[!]️  TEST FILE ALREADY EXISTS!\n")
            sys.stderr.write(f"   File: {test_file_path}\n\n")
            sys.stderr.write("[LOOP] SWITCHING TO INCREMENTAL MODE\n")
            sys.stderr.write("   -> Will analyze coverage and add missing tests\n")
            sys.stderr.write("   -> Will NOT overwrite existing tests\n")
            sys.stderr.write("="*80 + "\n\n")
            sys.stderr.flush()
            
            # Check test coverage to see if enhancement is needed
            sys.stderr.write("[REPORT] Checking test coverage...\n")
            sys.stderr.flush()
            
            coverage_result = check_ios_test_coverage(source_file_path)
            sys.stderr.write(f"[REPORT] Coverage result (raw):\n{coverage_result}\n\n")
            sys.stderr.flush()
            
            coverage = json.loads(coverage_result)
            
            if 'error' in coverage:
                sys.stderr.write(f"[FAIL] Error in coverage check: {coverage['error']}\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'error',
                    'error': coverage['error']
                })
            
            coverage_pct = coverage.get('coverage_percentage', 0)
            untested_methods = coverage.get('untested_methods', [])
            untested_count = coverage.get('untested_count', 0)
            
            sys.stderr.write(f"[REPORT] Parsed values:\n")
            sys.stderr.write(f"   coverage_pct = {coverage_pct} (type: {type(coverage_pct)})\n")
            sys.stderr.write(f"   untested_methods = {untested_methods}\n")
            sys.stderr.write(f"   untested_count = {untested_count} (type: {type(untested_count)})\n")
            sys.stderr.flush()
            
            # Handle case where untested_methods might be a string
            if isinstance(untested_methods, str):
                # Parse the count if it's a descriptive string
                untested_count = coverage.get('untested_count', 0)
            elif isinstance(untested_methods, list):
                untested_count = len(untested_methods)
            
            sys.stderr.write(f"   [OK] Coverage: {coverage_pct}%\n")
            sys.stderr.write(f"   [OK] Untested count: {untested_count}\n")
            sys.stderr.write(f"   [OK] Untested methods type: {type(untested_methods).__name__}\n")
            sys.stderr.write(f"   [OK] Untested methods: {untested_methods if isinstance(untested_methods, list) else '(string)'}\n")
            sys.stderr.write(f"   [OK] Should update: coverage_pct < 90 ({coverage_pct < 90}) OR untested_count > 0 ({untested_count > 0})\n")
            sys.stderr.write(f"   [OK] Result: {coverage_pct < 90 or untested_count > 0}\n\n")
            sys.stderr.flush()
            
            if coverage_pct >= 90 and untested_count == 0:
                return f"""
{'='*80}
[OK] TEST FILE ALREADY COMPLETE
{'='*80}

[DIR] Test file: {test_file_path}
[REPORT] Coverage: {coverage_pct}%
[OK] All methods are tested

{'='*80}
[TARGET] NEXT ACTIONS:
{'='*80}

Since tests exist and coverage is good, you should:

 Compile tests:
   Use compile_ios_unittest for {source_file_path}

 Run tests:
   Use run_ios_unittest with appropriate test filter

[SKIP] DO NOT call full_test_workflow again (tests already exist!)

{'='*80}
""" + json.dumps({
                    'status': 'test_file_already_complete',
                    'test_file': test_file_path,
                    'coverage_percentage': coverage_pct,
                    'next_action': f'Use compile_ios_unittest for {source_file_path}',
                    'FORBIDDEN_ACTIONS': ['Do NOT call full_test_workflow again']
                }, indent=2)
            else:
                # Tests exist but coverage insufficient - check if incomplete
                # The check will be done below in analyze_existing_test_file
                sys.stderr.write("[INFO] Test file exists with low coverage, analyzing...\n\n")
                sys.stderr.flush()
        
        # Test file doesn't exist - proceed with normal workflow
        sys.stderr.write("[OK] Test file doesn't exist - proceeding with full workflow\n\n")
        sys.stderr.flush()
        
        workflow_results = {
            'workflow': 'iOS Unit Test Generation',
            'source_file': source_file_path,
            'steps_completed': [],
            'steps_pending': []
        }
        
        # STEP 1: Analyze source code
        sys.stderr.write("[INFO] Step 1/6: Analyzing source code structure...\n")
        sys.stderr.flush()
        
        analysis_result = analyze_ios_code_for_testing(source_file_path)
        analysis = json.loads(analysis_result)
        
        if 'error' in analysis:
            return json.dumps({
                'status': 'error',
                'step': 1,
                'error': analysis['error']
            })
        
        workflow_results['steps_completed'].append({
            'step': 1,
            'name': 'Analyze source',
            'status': 'completed'
        })
        
        sys.stderr.write("   [OK] Analysis complete\n\n")
        sys.stderr.flush()
        
        # STEP 2: Generate test file
        sys.stderr.write("[INFO] Step 2/6: Generating test file...\n")
        sys.stderr.flush()
        
        generation_result = generate_ios_unittest_file(
            source_file_path=source_file_path,
            test_type='comprehensive',
            generation_mode='template'
        )
        generation = json.loads(generation_result)
        
        if 'error' in generation:
            return json.dumps({
                'status': 'error',
                'step': 2,
                'error': generation['error']
            })
        
        test_file_path = generation['test_file_path']
        test_count = generation['test_count']
        
        workflow_results['steps_completed'].append({
            'step': 2,
            'name': 'Generate tests',
            'status': 'completed',
            'test_file': test_file_path,
            'test_count': test_count
        })
        
        sys.stderr.write(f"   [OK] Generated {test_count} tests\n\n")
        sys.stderr.flush()
        
        # STEP 3: STOP HERE - Return context for Copilot enhancement
        # WHY STOP HERE?
        # - Step 3 requires Copilot to READ source + test files
        # - Step 3 requires Copilot to UNDERSTAND code logic
        # - Step 3 requires Copilot to WRITE test implementations
        # - These actions cannot be done inside a single MCP tool call
        # - Copilot must use read_file, replace_string_in_file in the OUTER context
        # 
        # ALTERNATIVE: User can skip full_test_workflow and call tools individually:
        #   1. analyze_ios_code_for_testing
        #   2. generate_ios_unittest_file
        #   3. [Copilot reads files and enhances tests]
        #   4. update_build_file_for_test
        #   5. compile_ios_unittest
        #   6. run_ios_unittest
        sys.stderr.write("="*80 + "\n")
        sys.stderr.write("⏸️  WORKFLOW PAUSED AFTER STEP 2\n")
        sys.stderr.write("="*80 + "\n")
        sys.stderr.write("\nWHY PAUSED?\n")
        sys.stderr.write("  Step 3 requires Copilot to read files, understand code,\n")
        sys.stderr.write("  and enhance tests. This cannot happen inside an MCP tool.\n")
        sys.stderr.write("  Copilot will now read files and enhance tests.\n\n")
        sys.stderr.write("NEXT STEPS (Copilot will do automatically):\n")
        sys.stderr.write(f"  1. Read {source_file_path}\n")
        sys.stderr.write(f"  2. Read {test_file_path}\n")
        sys.stderr.write("  3. Enhance tests with proper implementations\n")
        sys.stderr.write(f"  4. Call update_build_file_for_test('{test_file_path}')\n")
        sys.stderr.write(f"  5. Call compile_ios_unittest('{source_file_path}')\n")
        sys.stderr.write(f"  6. Call run_ios_unittest with test filter\n")
        sys.stderr.write("="*80 + "\n\n")
        sys.stderr.flush()
        
        # Return comprehensive context for Copilot to enhance tests
        # CRITICAL: Use manage_todo_list to create a FORCED workflow
        workflow_result = {
            'status': 'ready_for_enhancement',
            'workflow_phase': 'Step 3 of 6 - Test Enhancement',
            'steps_completed': workflow_results['steps_completed'],
            'source_file': source_file_path,
            'test_file': test_file_path,
            'test_count': test_count,
            'critical_instruction': '[BOT] COPILOT: Read files and enhance ALL tests NOW',
            'MANDATORY_TODO_LIST': {
                'instruction': 'YOU MUST create this todo list using manage_todo_list tool',
                'todos': [
                    {
                        'id': 1,
                        'title': f'Read and understand {source_file_path}',
                        'status': 'not-started'
                    },
                    {
                        'id': 2,
                        'title': f'Read and review {test_file_path}',
                        'status': 'not-started'
                    },
                    {
                        'id': 3,
                        'title': 'Enhance tests: add imports, mocks, and logic',
                        'status': 'not-started'
                    },
                    {
                        'id': 4,
                        'title': f'Call update_build_file_for_test for {test_file_path}',
                        'status': 'not-started'
                    },
                    {
                        'id': 5,
                        'title': f'Call compile_ios_unittest for {source_file_path}',
                        'status': 'not-started'
                    },
                    {
                        'id': 6,
                        'title': 'Call run_ios_unittest with appropriate test filter',
                        'status': 'not-started'
                    }
                ]
            },
            'automation_level': 'USE_MCP_TOOLS_FOR_WORKFLOW',
            'do_not': [
                '[FAIL] Do NOT skip test enhancement after Step 2',
                '[FAIL] Do NOT use run_in_terminal for compile (MUST use compile_ios_unittest MCP tool)',
                '[FAIL] Do NOT use run_in_terminal for run (MUST use run_ios_unittest MCP tool)',
                '[FAIL] Do NOT run autoninja directly (MUST use compile_ios_unittest)',
                '[FAIL] Do NOT manually create test files (use generate_ios_unittest_file)',
                '[FAIL] Do NOT manually modify BUILD files (use update_build_file_for_test)',
                '[FAIL] Do NOT skip any workflow steps'
            ],
            'allowed_in_step_2_5': [
                '[OK] read_file to read source and test files',
                '[OK] replace_string_in_file to enhance tests',
                '[OK] multi_replace_string_in_file for multiple edits'
            ],
            'do': '[OK] Follow workflow steps in order, use MCP tools for compile/run',
            'warning': '[!] Review and enhance tests before proceeding to BUILD update',
            'instructions': (
                'Workflow started for: ' + source_file_path + '\n\n'
                '[LAUNCH] OPTIMIZED WORKFLOW (6 steps with full automation):\n'
                '  Step 1: Analyze source structure\n'
                '          -> MCP tool: analyze_ios_code_for_testing\n'
                '  Step 2: Generate test skeleton\n'
                '          -> MCP tool: generate_ios_unittest_file\n'
                '          -> Creates basic test structure with TODOs\n'
                '  Step 3: [BOT] Copilot Enhancement (CRITICAL - NO SHORTCUTS)\n'
                '          -> Review test file and source file thoroughly\n'
                '          -> [SKIP] NEVER use DISABLED_ to skip complex tests\n'
                '          -> [SKIP] NEVER leave TODOs or placeholder code\n'
                '          -> [OK] Create mocks/fakes for complex dependencies\n'
                '          -> [OK] Implement ALL tests with real logic\n'
                '          -> [OK] Add 3+ meaningful assertions per test\n'
                '          -> Follow AAA pattern: Arrange -> Act -> Assert\n'
                '          -> [!]️ Quality over speed - full implementation required\n'
                '  Step 4: Update BUILD files automatically\n'
                '          -> MCP tool: update_build_file_for_test\n'
                '          -> [OK] Auto-detects Edge/Core and updates BUILD.gn/BUILD_edge.gni\n'
                '  Step 5: Compile tests [!]️ MUST USE MCP TOOL\n'
                '          -> MCP tool: compile_ios_unittest (DO NOT use run_in_terminal!)\n'
                '          -> [OK] Auto-detects test target\n'
                '          -> [OK] If compilation fails: auto-analyzes errors\n'
                '          -> [OK] Copilot fixes issues and retries\n'
                '  Step 6: Run tests [!]️ MUST USE MCP TOOL\n'
                '          -> MCP tool: run_ios_unittest (DO NOT use run_in_terminal!)\n'
                '          -> [OK] If tests fail: auto-analyzes runtime errors\n'
                '          -> [OK] Copilot fixes -> RECOMPILE (Step 5) -> RERUN (Step 6)\n'
                '          -> [OK] Loop: fix -> compile -> run until all pass\n\n'
                '[FAST] Key Improvements:\n'
                '  [BOT] Copilot naturally enhances tests after generation\n'
                '  [OK] Fills TODOs, improves assertions, adds edge cases\n'
                '  [OK] BUILD files updated automatically (update_build_file_for_test)\n'
                '  [OK] Compilation errors analyzed automatically (analyze_compilation_errors)\n'
                '  [OK] Runtime errors analyzed automatically (analyze_runtime_errors)\n'
                '  [OK] High automation - minimal manual operations\n\n'
                '[TARGET] Next: Call analyze_ios_code_for_testing to start Step 1\n'
            ),
            'next_action': {
                'tool': 'analyze_ios_code_for_testing',
                'params': {'source_file_path': source_file_path},
                'description': 'MUST use MCP tool: analyze_ios_code_for_testing',
                'reminder': 'Do not skip this step, call the tool immediately'
            },
            'remaining_steps': [
                {
                    'step': 2,
                    'tool': 'generate_ios_unittest_file',
                    'params': {'source_file_path': source_file_path, 'test_type': 'comprehensive'},
                    'description': 'MUST use MCP tool: generate_ios_unittest_file',
                    'note': 'Generates test skeleton with TODO markers',
                    'wait_for': 'After Step 1 completes',
                    'reminder': 'Do not create files manually, use MCP tool'
                },
                {
                    'step': 3,
                    'type': 'manual_enhancement',
                    'description': '[BOT] Copilot Enhancement - Implement tests with confidence scoring',
                    'critical_requirements': [
                        '[SKIP] FORBIDDEN: Using DISABLED_ prefix to skip tests',
                        '[SKIP] FORBIDDEN: Deleting test cases',
                        '[SKIP] FORBIDDEN: Placeholder assertions like EXPECT_TRUE(true)',
                        '[OK] ALLOWED: TODO comments for complex/uncertain implementations',
                        '[OK] REQUIRED: Preserve ALL generated test cases',
                        '[OK] REQUIRED: Create mocks for Browser, ProfileIOS, services',
                        '[OK] REQUIRED: Implement tests to best of ability',
                        '[OK] REQUIRED: 3+ meaningful assertions per implemented test',
                        '[OK] REQUIRED: Add confidence score (0-100) at end of test file'
                    ],
                    'what_happens': [
                        'Read source file to understand all dependencies',
                        'Read test file to see current implementation',
                        'Create mock/fake objects for complex dependencies',
                        'Implement test methods to best of your ability',
                        'For difficult tests: Keep skeleton + add TODO with explanation',
                        'Add meaningful assertions testing actual behavior',
                        'Verify AAA pattern in all tests',
                        'Add confidence score comment: // CONFIDENCE_SCORE: 85/100'
                    ],
                    'todo_guidance': [
                        '[OK] Use TODO for tests requiring deep domain knowledge',
                        '[OK] Use TODO for tests with unclear mocking strategy',
                        '[OK] Format: // TODO: [Reason] - e.g., "Requires understanding of ProfileIOS lifecycle"',
                        '[OK] Leave test skeleton intact with basic structure',
                        '[FAIL] Do NOT delete the test - developer will review and implement'
                    ],
                    'confidence_scoring': {
                        'definition': 'Rate implementation quality 0-100 based on completeness',
                        'format': '// CONFIDENCE_SCORE: XX/100 - [Brief justification]',
                        'criteria': [
                            '90-100: All tests fully implemented with proper mocks',
                            '70-89: Most tests implemented, few TODOs for complex cases',
                            '50-69: Basic implementation, several TODOs needing review',
                            '30-49: Skeleton only, many TODOs, needs significant work',
                            '0-29: Minimal implementation, mostly TODOs'
                        ],
                        'placement': 'Add at end of test file before closing'
                    },
                    'automatic': True,
                    'quality_bar': 'Maximize implemented tests, use TODO for genuinely uncertain cases',
                    'recommended_approach': [
                        '[OK] Implement all straightforward tests completely',
                        '[OK] Add TODO for tests requiring domain expertise',
                        '[OK] Provide confidence score for developer guidance',
                        '[FAIL] Never delete generated test cases'
                    ]
                },
                {
                    'step': 4,
                    'tool': 'update_build_file_for_test',
                    'params': {
                        'test_file_path': test_file_path,
                        'auto_apply': True
                    },
                    'description': '🆕 Auto-update BUILD.gn or BUILD_edge.gni',
                    'benefits': '[OK] Eliminates manual BUILD file editing',
                    'wait_for': 'After Step 2 completes',
                    'reminder': 'This replaces manual BUILD_edge.gni editing!'
                },
                {
                    'step': 5,
                    'tool': 'compile_ios_unittest',
                    'params': {'source_file': source_file_path},
                    'description': '[BUILD] Compile tests using MCP TOOL ONLY',
                    'benefits': [
                        '[OK] Auto-detects test target',
                        '[OK] Compiles tests using autoninja internally',
                        '[OK] Auto-analyzes compilation errors if fails',
                        '[OK] Copilot fixes errors automatically',
                        '[OK] Retries compilation until success'
                    ],
                    'wait_for': 'After Step 3 (enhancement) or Step 4 completes',
                    'critical_rules': [
                        '[!]️ MUST use compile_ios_unittest MCP tool',
                        '[SKIP] DO NOT use run_in_terminal with autoninja',
                        '[SKIP] DO NOT declare success if linking fails',
                        '[SKIP] DO NOT skip fixing linking errors',
                        '[OK] MUST fix all compilation and linking errors',
                        '[OK] Success = tests compile and link without errors'
                    ],
                    'example_call': f'compile_ios_unittest("{source_file_path}")'
                },
                {
                    'step': 6,
                    'tool': 'run_ios_unittest',
                    'params': {'test_filter': '<auto-detected>', 'test_file_path': test_file_path, 'source_file_path': source_file_path},
                    'description': '[RUN] Run tests using MCP TOOL ONLY',
                    'benefits': [
                        '[OK] Uses correct iOS test runner (ios/build/bots/scripts/run_test.py)',
                        '[OK] Auto-analyzes runtime errors if tests fail',
                        '[OK] Copilot fixes test issues automatically',
                        '[OK] After fix: RECOMPILE (Step 5) -> RERUN (Step 6)',
                        '[OK] Loop: fix -> compile -> run until all pass'
                    ],
                    'wait_for': 'After Step 5 succeeds (compilation passes)',
                    'critical_rules': [
                        '[!]️ MUST use run_ios_unittest MCP tool',
                        '[SKIP] DO NOT use run_in_terminal with iossim or run_test.py',
                        '[OK] MUST provide test_filter, test_file_path, source_file_path',
                        '[OK] MUST actually run tests to verify they pass',
                        '[LOOP] If tests fail: fix -> RECOMPILE (use compile_ios_unittest) -> RERUN',
                        '[OK] Success = all tests pass (green)'
                    ],
                    'example_call': f'run_ios_unittest("TestFixtureName.*", test_file_path="{test_file_path}", source_file_path="{source_file_path}")'
                }
            ],
            'critical_reminder': 'Each step MUST use MCP tools - do not run terminal commands or edit files manually!'
        }
        
        # Format the response with TODO list that Copilot should create automatically
        response_message = f"""
{'='*80}
# [!][!][!] COPILOT: READ THIS FIRST - MANDATORY TOOL SELECTION [!][!][!]
{'='*80}

FOR STEPS 3-6 BELOW, YOU **MUST** USE SPECIFIC TOOLS:

# [READ] Step 3: Enhancement (read & edit tests)
   [OK] ALLOWED TOOLS: read_file, replace_string_in_file, multi_replace_string_in_file
   [SKIP] FORBIDDEN: Nothing - use standard editing tools

[NOTE] Step 4: BUILD File Update  
   # [!] MANDATORY MCP TOOL: update_build_file_for_test
   [SKIP] ABSOLUTELY FORBIDDEN: run_in_terminal, manual editing of BUILD.gn
   # [!]️  If you think "let me edit BUILD.gn" -> STOP! Use the MCP tool!
   # [!]️  If you think "run_in_terminal" -> STOP! Use the MCP tool!

# [BUILD] Step 5: Compilation
   # [!] MANDATORY MCP TOOL: compile_ios_unittest  
   [SKIP] ABSOLUTELY FORBIDDEN: run_in_terminal with autoninja
   # [!]️  If you think "autoninja -C" -> STOP! Use compile_ios_unittest!
   # [!]️  If you think "run_in_terminal" -> STOP! Use compile_ios_unittest!

# [RUN] Step 6: Run Tests
   # [!] MANDATORY MCP TOOL: run_ios_unittest
   [SKIP] ABSOLUTELY FORBIDDEN: run_in_terminal with python3/iossim
   # [!]️  If you think "python3 ios/tools" -> STOP! Use run_ios_unittest!
   # [!]️  If you think "run_in_terminal" -> STOP! Use run_ios_unittest!

[TIP] WHY USE MCP TOOLS (NOT run_in_terminal)?
   [OK] Auto-detects correct test targets
   [OK] Auto-analyzes errors if compilation/tests fail
   [OK] Provides fix guidance automatically
   [OK] Tracks workflow state
   [OK] Formats output for better visibility
   
   [FAIL] run_in_terminal will NOT provide these benefits!

{'='*80}
[LAUNCH] WORKFLOW INITIALIZED - AUTOMATIC TODO LIST
{'='*80}

[OK] Step 1-2 Complete: Analysis and test generation finished
# [WAIT] Step 3-6 Pending: Executing workflow with TODO tracking

[INFO] TODO LIST (auto-created for workflow tracking):

   [ ] Todo 1: Read and understand {source_file_path}
       # -> Use: read_file tool
   
   [ ] Todo 2: Read and review {test_file_path}
       # -> Use: read_file tool
   
   [ ] Todo 3: Enhance tests - CRITICAL FOR ONE-PASS SUCCESS
       # -> Use: replace_string_in_file or multi_replace_string_in_file
       
       [NOTE] COMPREHENSIVE CHECKLIST (do ALL to avoid recompilation):
       
       [OK] 1. Add ALL necessary #import statements:
          - Check source file for dependencies
          - Import headers for ALL classes/protocols used in tests
          - Common imports: testing/gtest/include/gtest/gtest.h
                           testing/platform_test.h
                           base/test/ios/wait_util.h (if async)
       
       [OK] 2. Create mock objects for dependencies:
          - Identify external dependencies in source file
          - Create mock classes implementing required protocols
          - Use OCMock if appropriate (add #import "third_party/ocmock/...")
       
       [OK] 3. Implement ALL test methods completely:
          - Replace ALL TODO comments with real code
          - Add 3+ meaningful assertions per test
          - Test normal cases + edge cases
          - Use proper test pattern: Arrange -> Act -> Assert
       
       [OK] 4. Handle async operations properly:
          - Use WaitUntilConditionOrTimeout for async tests
          - Add proper completion handlers
       
       [OK] 5. Verify test fixture setup:
          - Ensure SetUp() creates all needed objects
          - Ensure TearDown() cleans up properly
       
       [TARGET] GOAL: Write tests so complete that they compile and pass on FIRST try!
   
   [ ] Todo 4: [!] MANDATORY MCP TOOL [!] Update BUILD file
       
       # [!]️[!]️[!]️ CRITICAL: YOU MUST USE MCP TOOL [!]️[!]️[!]️
       
       [OK] CORRECT: update_build_file_for_test("{test_file_path}")
       
       [FAIL] FORBIDDEN: run_in_terminal
       [FAIL] FORBIDDEN: Manually editing BUILD.gn
       [FAIL] FORBIDDEN: Using replace_string_in_file on BUILD.gn
       
       If you are thinking of ANY method other than update_build_file_for_test,
       you are about to make a mistake! STOP and use the MCP tool!
   
   [ ] Todo 5: [!] MANDATORY MCP TOOL [!] Compile tests
       
       # [!]️[!]️[!]️ CRITICAL: YOU MUST USE MCP TOOL [!]️[!]️[!]️
       
       [OK] CORRECT: compile_ios_unittest("{source_file_path}")
       
       [FAIL] FORBIDDEN: run_in_terminal with autoninja
       [FAIL] FORBIDDEN: Any terminal command for compilation
       
       If you are thinking "autoninja -C" or "run_in_terminal",
       you are about to make a mistake! STOP and use compile_ios_unittest!
   
   [ ] Todo 6: [!] MANDATORY MCP TOOL [!] Run tests
       
       # [!]️[!]️[!]️ CRITICAL: YOU MUST USE MCP TOOL [!]️[!]️[!]️
       
       [OK] CORRECT: run_ios_unittest("TestFixtureName.*", 
                                    test_file_path="{test_file_path}",
                                    source_file_path="{source_file_path}")
       
       [FAIL] FORBIDDEN: run_in_terminal with python3
       [FAIL] FORBIDDEN: run_in_terminal with iossim
       [FAIL] FORBIDDEN: Any terminal command for running tests
       
       If you are thinking "python3 ios/tools" or "run_in_terminal",
       you are about to make a mistake! STOP and use run_ios_unittest!

[TARGET] Workflow State:
   Source: {source_file_path}
   Test:   {test_file_path}
   Tests:  {test_count} test cases generated

[FAST] CRITICAL REMINDER:
   Steps 4-6 MUST use MCP tools (not terminal commands)
   This ensures automatic error analysis and fixing

{'='*80}
# [!] COMPLETION CRITERIA - DO NOT STOP UNTIL ALL MET [!]
{'='*80}

YOU MUST CONTINUE ITERATING UNTIL:

[OK] 1. ALL tests compile without errors
   # -> Use compile_ios_unittest MCP tool
   # -> If errors: fix and RECOMPILE
   # -> Repeat until returncode == 0

[OK] 2. ALL tests pass (100% success rate)
   # -> Use run_ios_unittest MCP tool
   # -> If failures: analyze, fix, RECOMPILE, RERUN
   # -> Repeat until ALL tests show [  PASSED  ]

[OK] 3. No test is DISABLED_
   # -> If you added DISABLED_ prefix, you failed
   # -> Remove DISABLED_, implement the test properly

[OK] 4. No TODO comments remain in critical code
   # -> Test setup, core assertions must be complete
   # -> Optional: Complex edge cases can have TODO

[SKIP] DO NOT STOP WHEN:
   [FAIL] Some tests pass but some fail (6/11 is NOT done!)
   [FAIL] Compilation has warnings (must be clean)
   [FAIL] Tests are commented out
   [FAIL] Tests have DISABLED_ prefix

[LOOP] ITERATION LOOP (KEEP GOING UNTIL 100% PASS):

   1. Analyze test failure from run_ios_unittest output
   2. Fix the failing test in test file
   3. RECOMPILE using compile_ios_unittest
   4. RERUN using run_ios_unittest
   5. Check if ALL tests pass:
      # -> YES: DONE [OK]
      # -> NO: Go back to step 1

[TIP] BATCH FIXES TO REDUCE COMPILATIONS:
   - If multiple tests fail for similar reasons, fix them ALL at once
   - Then recompile ONCE
   - This reduces iterations

[TARGET] SUCCESS EXAMPLE:
   [OK] Compilation: returncode=0, no errors
   [OK] Test run: [  PASSED  ] 11 tests
   [OK] No DISABLED_ tests
   [OK] Test file has confidence score: // CONFIDENCE_SCORE: 95/100

[FAIL] FAILURE EXAMPLES (DO NOT STOP HERE):
   [FAIL] [  PASSED  ] 6 tests, [  FAILED  ] 5 tests
   [FAIL] Some tests commented out
   [FAIL] DISABLED_TestName exists

{'='*80}
"""
        
        return response_message
        
        return response_message
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'fallback': 'Use full_test_workflow tool instead'
        })


# ============================================================================
# PATTERN DETECTION ENGINE (Layer 3)
# ============================================================================
# ============================================================================
# AI-ENHANCED TEST GENERATION SUPPORT
# ============================================================================

def get_test_infrastructure_template(pattern_info: Dict) -> str:
    """Returns the test infrastructure template from pattern database.
    
    Args:
        pattern_info: Pattern information from detect_test_pattern_with_examples()
        
    Returns:
        C++ test infrastructure template string from pattern database
    """
    # Use pattern template from database instead of hardcoded templates
    template = pattern_info.get('template', '')
    
    if template:
        return template
    
    # Fallback: minimal stub if no pattern template
    return '''
// Test Infrastructure (minimal stub - enhance based on source code)
class {ClassName}Test : public PlatformTest {
 protected:
  // TODO: Add SetUp/TearDown methods
  // TODO: Add member variables for test fixture
};
'''


def format_methods_for_copilot(methods: List[Dict]) -> str:
    """Formats method information for Copilot consumption.
    
    Args:
        methods: List of method dictionaries with signatures and types
        
    Returns:
        Formatted string describing methods to test
    """
    if not methods:
        return "No public methods to test"
    
    formatted = []
    for i, method in enumerate(methods, 1):
        name = method.get('name', 'unknown')
        signature = method.get('full_signature', name)
        return_type = method.get('return_type', 'id')
        has_params = ':' in signature
        
        formatted.append(f"{i}. Method Name: {name}")
        formatted.append(f"   Full Signature: {signature}")
        formatted.append(f"   Return Type: {return_type}")
        formatted.append(f"   Needs Parameters: {'Yes' if has_params else 'No'}")
        formatted.append("")
    
    return "\n".join(formatted)


def format_properties_for_copilot(properties: List[Dict]) -> str:
    """Formats property information for Copilot consumption."""
    if not properties:
        return "No properties to test"
    
    formatted = []
    for i, prop in enumerate(properties, 1):
        name = prop.get('name', 'unknown')
        prop_type = prop.get('type', 'id')
        
        formatted.append(f"{i}. Property Name: {name}")
        formatted.append(f"   Type: {prop_type}")
        formatted.append("")
    
    return "\n".join(formatted)


def prepare_copilot_context(source_file: str, analysis: Dict, testable_elements: Dict) -> Dict:
    """Prepares comprehensive context for Copilot test generation.
    
    Args:
        source_file: Path to source file
        analysis: Analysis results from analyze_ios_code_for_testing
        testable_elements: Detailed testable elements
        
    Returns:
        Dictionary with all context needed for Copilot to generate tests
    """
    # Determine class name
    if testable_elements['implementations']:
        class_name = testable_elements['implementations'][0]
    elif testable_elements['interfaces']:
        class_name = testable_elements['interfaces'][0]
    else:
        class_name = 'Unknown'
    
    # 🆕 Use intelligent pattern detection engine
    pattern_info = detect_test_pattern_with_examples(
        source_file,
        read_file_content(source_file),
        testable_elements
    )
    
    default_pattern = pattern_info.get('default_pattern', {})
    pattern_template = default_pattern.get('template', '')
    example_files = default_pattern.get('example_files', [])
    pattern_id = default_pattern.get('pattern_id', 'simple_class_pattern')
    all_patterns = pattern_info.get('all_patterns', [])
    
    # Get parent class from hierarchy
    parent_class = testable_elements.get('class_hierarchy', {}).get(class_name, '')
    
    # Use pattern template from database (no hardcoded templates)
    if pattern_template:
        template = pattern_template.replace('{class_name}', class_name)
    else:
        template = get_test_infrastructure_template(pattern_info)
        template = template.replace('{ClassName}', class_name)
    
    # Format methods and properties
    methods_info = []
    for method in testable_elements.get('methods', []):
        method_details = testable_elements.get('method_details', {}).get(method, {})
        methods_info.append({
            'name': method,
            'full_signature': method_details.get('full_signature', method),
            'return_type': method_details.get('return_type', 'id')
        })
    
    properties_info = []
    properties = testable_elements.get('properties', [])
    # Handle both list of dicts and dict formats
    if isinstance(properties, list):
        properties_info = properties
    else:
        # Legacy dict format
        for prop_name, prop_type in properties.items():
            properties_info.append({
                'name': prop_name,
                'type': prop_type
            })
    
    return {
        'source_file': source_file,
        'class_name': class_name,
        'parent_class': parent_class,
        'pattern_type': pattern_id,
        'pattern_id': pattern_id,
        'pattern_confidence': confidence,
        'pattern_template': pattern_template,
        'example_files': example_files,
        'object_reference': object_ref,
        'test_infrastructure_template': template,
        'methods': methods_info,
        'properties': properties_info,
        'functions': testable_elements.get('functions', []),
        'dependencies': analysis.get('dependencies', {}),
        'is_edge_specific': is_edge_file(source_file),
        'existing_test_count': analysis.get('existing_test_analysis', {}).get('test_count', 0) if analysis.get('test_file_exists') else 0
    }


# ============================================================================
# ANALYSIS AND GENERATION TOOLS
# ============================================================================

@mcp.tool(name='analyze_ios_code_for_testing', structured_output=False)
def analyze_ios_code_for_testing(source_file_path: str) -> str:
    """Analyze iOS source file for testing. Returns testable elements and recommendations.
    
    This tool performs comprehensive analysis of an iOS source file to identify:
    - Classes and their methods
    - Functions that can be unit tested
    - Existing test files and coverage
    - Dependencies and imports needed for testing
    
    Args:
        source_file_path: Path to the iOS source file (relative to Chromium src root)
        
    Returns:
        JSON string containing:
        - classes: List of detected classes with their methods
        - functions: List of standalone functions
        - test_file_exists: Whether a test file already exists
        - test_file_path: Path to the test file (existing or recommended)
        - build_gn_path: Path to the BUILD.gn file for test configuration
        - testing_recommendations: Suggestions for writing effective tests
    """
    import json
    import sys
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"ANALYZING: {source_file_path}\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    if not is_ios_source_file(source_file_path):
        return json.dumps({
            'status': 'error',
            'tool': 'analyze_ios_code_for_testing',
            'error': f'Not an iOS source file: {source_file_path}. '
                    'File must contain an ios directory in its path and end with .h, .mm, or .m'
        })
    
    try:
        # Read source file
        source_content = read_file_content(source_file_path)
        
        # Read header file for accurate method declarations
        header_file_path = source_file_path.replace('.mm', '.h').replace('.cc', '.h')
        header_content = None
        try:
            header_content = read_file_content(header_file_path)
        except:
            pass
        
        # Calculate test file path
        test_file_path = calculate_test_file_path(source_file_path)
        existing_test_path = find_existing_test_file(source_file_path)
        
        # Analyze source code - use header file for method declarations
        testable_elements = extract_testable_interfaces(source_content, header_content)
        
        # Analyze dependencies
        dependencies = extract_dependencies_from_source(source_content, source_file_path)
        
        # Analyze existing tests if present
        existing_test_analysis = None
        if existing_test_path:
            test_content = read_file_content(existing_test_path)
            existing_test_analysis = analyze_existing_tests(test_content)
        
        # Find BUILD.gn
        build_gn_file = find_build_gn_file(source_file_path)
        
        # Generate recommendations
        recommendations = []
        if existing_test_analysis:
            # Convert tested_methods list back to set for comparison
            tested_methods_set = set(existing_test_analysis['tested_methods'])
            untested_methods = set(testable_elements['methods']) - tested_methods_set
            if untested_methods:
                recommendations.append(
                    f"Add tests for {len(untested_methods)} untested methods: "
                    f"{', '.join(list(untested_methods)[:5])}"
                )
            if existing_test_analysis['test_count'] == 0:
                recommendations.append("Test file exists but has no test cases!")
        else:
            recommendations.append("No test file exists - need to create one")
            if testable_elements['interfaces']:
                recommendations.append(
                    f"Create tests for {len(testable_elements['interfaces'])} "
                    "interfaces"
                )
            if testable_elements['functions']:
                recommendations.append(
                    f"Create tests for {len(testable_elements['functions'])} "
                    "functions"
                )
        
        result = {
            'status': 'success',
            'tool': 'analyze_ios_code_for_testing',
            'message': 'Step 1 Complete - Code analysis results',
            'source_file': source_file_path,
            'is_edge_specific': is_edge_file(source_file_path),
            'test_file_path': test_file_path,
            'test_file_exists': existing_test_path is not None,
            'existing_test_analysis': existing_test_analysis,
            'testable_elements': {
                'interfaces': testable_elements['interfaces'],
                'implementations': testable_elements['implementations'],
                'method_count': len(testable_elements['methods']),
                'function_count': len(testable_elements['functions']),
            },
            'dependencies': {
                'imports': dependencies['imports'][:10],  # Limit to first 10
                'suggested_deps': dependencies['suggested_deps'],
                'common_test_deps': dependencies['common_test_deps'],
            },
            'build_gn_file': build_gn_file,
            'recommendations': recommendations,
            'next_step': {
                'action': 'Immediately call MCP tool: generate_ios_unittest_file',
                'tool': 'generate_ios_unittest_file',
                'params': {
                    'source_file_path': source_file_path,
                    'test_type': 'comprehensive'
                },
                'reminder': 'Do not create files manually, use MCP tool to generate automatically'
            }
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool(name='generate_ios_unittest_file', structured_output=False)
def generate_ios_unittest_file(
    source_file_path: str,
    test_type: str = 'comprehensive',
    generation_mode: str = 'template'
) -> str:
    """Generate iOS unit test file. Creates test file and updates BUILD.gn automatically.
    
    This tool generates a complete unit test file for an iOS source file, including:
    - Test fixture setup with proper Objective-C++ syntax
    - Import statements for required headers
    - Test cases for all methods and functions
    - Automatic BUILD.gn configuration updates
    
    Args:
        source_file_path: Path to the iOS source file (relative to Chromium src root)
        test_type: Type of tests to generate ('comprehensive', 'basic', or 'minimal')
        generation_mode: How to generate tests ('template' or 'ai')
        
    Returns:
        JSON string containing:
        - test_file_path: Path to the generated test file
        - test_file_content: Complete content of the generated test file
        - build_gn_updated: Whether BUILD.gn was successfully updated
        - coverage_before: Test coverage before generation
        - coverage_after: Test coverage after generation
        - next_steps: Recommended actions after generation
    """
    import json
    import sys
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"GENERATING TEST FILE: {source_file_path}\n")
    sys.stderr.write(f"Test type: {test_type}\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    if not is_ios_source_file(source_file_path):
        return json.dumps({
            'error': f'Not an iOS source file: {source_file_path}'
        })
    
    try:
        # Step 0: Check coverage BEFORE generating tests
        coverage_before = None
        try:
            coverage_result = check_ios_test_coverage(source_file_path)
            coverage_before = json.loads(coverage_result)
        except:
            # If no existing test, coverage is 0
            coverage_before = {
                'coverage_percentage': 0,
                'tested_count': 0,
                'test_quality_score': 0
            }
        
        # Step 1: Analyze the file
        print(f" Step 1/10: Analyzing source file... (mode: {generation_mode})")
        analysis_result = analyze_ios_code_for_testing(source_file_path)
        analysis = json.loads(analysis_result)
        
        if 'error' in analysis:
            return json.dumps(analysis)
        
        # Step 2: Read source and header files
        print(" Step 2/10: Reading source and header files...")
        source_content = read_file_content(source_file_path)
        
        header_file_path = source_file_path.replace('.mm', '.h').replace('.cc', '.h')
        header_content = None
        try:
            header_content = read_file_content(header_file_path)
            print(f"    Read header file: {header_file_path}")
        except:
            print(f"    No header file found, using source file only")
        
        # Step 3: Extract testable elements
        print(" Step 3/10: Extracting testable elements...")
        testable_elements = extract_testable_interfaces(source_content, header_content)
        
        # AI-ENHANCED MODE: Return context for Copilot to generate tests
        if generation_mode == 'ai_enhanced':
            print("\n" + "="*80)
            print("AI-ENHANCED MODE: Preparing context for Copilot")
            print("="*80 + "\n")
            
            context = prepare_copilot_context(source_file_path, analysis, testable_elements)
            
            # Build comprehensive prompt for Copilot
            copilot_prompt = f"""
# iOS Unit Test Generation Task

## Source File Information
- **File Path**: `{context['source_file']}`
- **Class Name**: `{context['class_name']}`
- **Parent Class**: `{context['parent_class']}`
- **Pattern Type**: `{context['pattern_type']}` {'(Coordinator)' if context['pattern_type'] == 'coordinator' else '(ProfileAgent)' if context['pattern_type'] == 'profile_agent' else '(Regular Class)'}
- **Object Reference**: `{context['object_reference']}`
- **Edge Specific**: {'Yes' if context['is_edge_specific'] else 'No'}
- **Existing Test Count**: {context['existing_test_count']}

## Required Test Infrastructure Template

```cpp{context['test_infrastructure_template']}
```

## Methods to Test ({len(context['methods'])})

{format_methods_for_copilot(context['methods'])}

## Properties to Test ({len(context['properties'])})

{format_properties_for_copilot(context['properties'])}

## Dependencies (Extracted from BUILD.gn)

```json
{json.dumps(context['dependencies'], indent=2)}
```

## Generation Requirements

### Rules to Follow:

1. **Strictly use the above test infrastructure template**
   - Coordinator: Must use `initWithBaseViewController:browser:`
   - ProfileAgent: Must use constructor pattern
   - Regular Class: Use SetUp/TearDown pattern

2. **Test File Structure**
   ```cpp
   // Copyright (C) Microsoft Corporation. All rights reserved.
   // Use of this source code is governed by a BSD-style license that can be
   // found in the LICENSE file.
   
   #import "{source_file_path.replace('.mm', '.h')}"
   
   // Import necessary test headers
   #import "testing/gtest/include/gtest/gtest.h"
   #import "testing/platform_test.h"
   // ... Add other imports based on pattern type
   
   // Test fixture class (using template above)
   // Test cases (using TEST_F macro)
   ```

3. **Intelligent Test Generation**
   - Generate test case for each public method
   - Use meaningful assertions (not just `EXPECT_NE(obj, nil)`)
   - Test normal path and edge cases
   - For methods with parameters, add TODO comment explaining needed parameters
   - Test Coordinator start/stop lifecycle
   - Test ProfileAgent initStage state transitions

4. **Test Naming Convention**
   - Test fixture: `{{ClassName}}Test`
   - Test case: Descriptive name (e.g., `Initialization`, `StartAndStop`, `MethodName`)

5. **Comments and Documentation**
   - Add clear comments for each test explaining its purpose
   - For complex initialization or assertions, add explanatory comments

### Example Test Case Structure:

```cpp
TEST_F({context['class_name']}Test, Initialization) {{
  // Verify coordinator is properly initialized
  ASSERT_NE({context['object_reference']}, nil);
  EXPECT_TRUE([{context['object_reference']} isKindOfClass:[{context['class_name']} class]]);
}}

// Generate similar intelligent tests for each method...
```

## Next Steps

Please generate **complete test file content** (including header imports, test fixture, and all test cases).

After generation, I will:
1. Verify code syntax
2. Write test file
3. Update BUILD.gn
4. Compile and run tests
"""
            
            # Print the prompt to stderr for Copilot to see
            sys.stderr.write("\n" + "="*80 + "\n")
            sys.stderr.write("AI ENHANCED MODE - Context for Test Generation\n")
            sys.stderr.write("="*80 + "\n\n")
            sys.stderr.write(copilot_prompt)
            sys.stderr.write("\n" + "="*80 + "\n\n")
            sys.stderr.flush()
            
            result = {
                'status': 'ai_enhanced_ready',
                'mode': 'ai_enhanced',
                'message': 'Context prepared for AI-enhanced test generation',
                'context': context,
                'test_file_path': analysis.get('test_file_path'),
                'build_gn_file': analysis.get('build_gn_file'),
                'next_step': {
                    'action': 'COPILOT_GENERATE_TEST_CODE',
                    'instructions': [
                        '1. Read the detailed prompt in stderr output',
                        '2. Generate complete test file content (C++ code)',
                        '3. Use correct test infrastructure template',
                        '4. Write code to file using create_file',
                        '5. Update BUILD.gn',
                        '6. Compile and run tests'
                    ],
                    'reminder': 'Follow the test infrastructure template strictly'
                }
            }
            
            return json.dumps(result, indent=2)
        
        # TEMPLATE MODE: Continue with original template-based generation
        
        # Print analysis summary
        print(f"    Source file: {source_file_path}")
        print(f"    Test file: {analysis.get('test_file_path', 'N/A')}")
        print(f"    BUILD.gn: {analysis.get('build_gn_file', 'N/A')}")
        print(f"    Testable elements found:")
        testable = analysis.get('testable_elements', {})
        print(f"      - Interfaces: {len(testable.get('interfaces', []))}")
        print(f"      - Methods: {testable.get('method_count', 0)}")
        print(f"      - Functions: {testable.get('function_count', 0)}")
        if analysis.get('existing_test_analysis'):
            existing = analysis['existing_test_analysis']
            print(f"    Existing tests: {existing.get('test_count', 0)} test cases")
        else:
            print(f"    Existing tests: None (will create new)")
        print("")
        
        # Step 2: Extract testable elements - READ HEADER FILE FOR ACCURATE METHOD LIST!
        print(" Step 2/10: Reading source and header files...")
        source_content = read_file_content(source_file_path)
        
        # CRITICAL: Read the HEADER file (.h) to get actual method declarations
        header_file_path = source_file_path.replace('.mm', '.h').replace('.cc', '.h')
        header_content = None
        try:
            header_content = read_file_content(header_file_path)
            print(f"    Read header file: {header_file_path}")
        except:
            # Header file doesn't exist or can't be read, fallback to source only
            print(f"     No header file found, using source file only")
            pass
        
        # Extract methods from header (preferred) or source (fallback)
        testable_elements = extract_testable_interfaces(source_content, header_content)
        print(f"    Found: {len(testable_elements['interfaces'])} interfaces, "
              f"{len(testable_elements['methods'])} methods, "
              f"{len(testable_elements['properties'])} properties")
        print("")
        
        # Step 3: Check if test file already exists
        test_file_path = analysis['test_file_path']
        src_root = get_chromium_src_root()
        test_full_path = src_root / test_file_path
        
        if test_full_path.exists():
            sys.stderr.write(f"\n{'='*80}\n")
            sys.stderr.write(f"[!]️  TEST FILE ALREADY EXISTS\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"File: {test_file_path}\n\n")
            sys.stderr.write(f"ℹ️  Skipping generation - file already exists.\n")
            sys.stderr.write(f"   To update existing tests, use: update_existing_tests\n")
            sys.stderr.write(f"   To check coverage, use: check_ios_test_coverage\n")
            sys.stderr.write(f"{'='*80}\n\n")
            sys.stderr.flush()
            
            return json.dumps({
                'status': 'already_exists',
                'test_file_path': test_file_path,
                'message': 'Test file already exists - skipped generation',
                'suggestion': 'Use update_existing_tests to add missing test cases',
                'next_steps': [
                    f'Check coverage: check_ios_test_coverage("{source_file_path}")',
                    f'Update tests: update_existing_tests("{source_file_path}")',
                    f'Compile: compile_ios_unittest("{source_file_path}")',
                    f'Run: run_ios_unittest with test filter'
                ]
            }, indent=2)
        
        # Step 4: Generate test content
        print("  Step 4/10: Generating test content...")
        test_content = generate_test_content(
            source_file_path,
            test_file_path,
            testable_elements,
            test_type
        )
        test_count = test_content.count('TEST_F(')
        print(f"    Generated {test_count} test cases ({test_type} mode)")
        print("")
        
        # Step 5: Write test file
        print(f" Step 5/10: Writing test file...")
        write_result = write_test_file(test_file_path, test_content)
        if not write_result.get('success'):
            return json.dumps({
                'status': 'error',
                'tool': 'generate_ios_unittest_file',
                'error': f'Failed to write test file: {write_result.get("error", "Unknown error")}'
            })
        print(f"    Test file written: {test_file_path}")
        
        # Check quality score and TODO count
        validation = write_result.get('validation', {})
        quality_score = validation.get('quality_score', 0)
        todo_count = test_content.count('TODO:')
        print(f"    Quality score: {quality_score}/100")
        print(f"    TODO markers: {todo_count}")
        print("")
        
        # Step 5.5: Clear warning about enhancement requirements
        sys.stderr.write(f"\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"[OK] Step 2/10: Test file generated\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"   File: {test_file_path}\n")
        sys.stderr.write(f"   Tests: {test_count} | TODOs: {todo_count} | Quality: {quality_score}/100\n")
        sys.stderr.write(f"\n")
        sys.stderr.write(f"[!]️  CRITICAL: Step 2.5 Enhancement Rules\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"[SKIP] FORBIDDEN:\n")
        sys.stderr.write(f"   - Using DISABLED_ to skip tests\n")
        sys.stderr.write(f"   - Leaving TODO comments\n")
        sys.stderr.write(f"   - Placeholder assertions (EXPECT_TRUE(true))\n")
        sys.stderr.write(f"\n")
        sys.stderr.write(f"[OK] REQUIRED:\n")
        sys.stderr.write(f"   - Create mocks/fakes for all dependencies\n")
        sys.stderr.write(f"   - Implement ALL {test_count} tests completely\n")
        sys.stderr.write(f"   - 3+ meaningful assertions per test\n")
        sys.stderr.write(f"\n")
        sys.stderr.write(f"➡️  Next: Fully enhance tests, then call update_build_file_for_test\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        # Step 6: Update BUILD.gn with proper dependencies for compilation
        print(" Step 6/10: Updating BUILD.gn...")
        dependencies = analysis.get('dependencies', {})
        suggested_deps = dependencies.get('suggested_deps', [])
        common_test_deps = dependencies.get('common_test_deps', [])
        
        # Merge and deduplicate: common test deps MUST come first (they're essential)
        all_deps = common_test_deps.copy()
        for dep in suggested_deps:
            if dep not in all_deps:
                all_deps.append(dep)
        
        print(f"    Total dependencies: {len(all_deps)}")
        print(f"      - Test framework deps: {len(common_test_deps)}")
        print(f"      - Source-specific deps: {len(suggested_deps)}")
        
        build_gn_path = analysis.get('build_gn_file')
        build_gn_success = False
        build_gn_message = "No BUILD.gn file found"
        
        if build_gn_path:
            build_gn_success, build_gn_message = update_build_gn(
                build_gn_path,
                os.path.basename(test_file_path),
                all_deps
            )
            print(f"   {'' if build_gn_success else ''} {build_gn_message}")
            
            # Check if this is Edge-specific and needs BUILD_edge.gni update
            if is_edge_file(source_file_path):
                edge_instructions = generate_build_edge_gni_instructions(
                    source_file_path,
                    build_gn_path
                )
                print(edge_instructions)
        else:
            print(f"     {build_gn_message}")
        print("")
        
        # Step 7: Check coverage AFTER generating tests
        print(" Step 7/10: Analyzing test coverage...")
        coverage_after = None
        try:
            coverage_result_after = check_ios_test_coverage(source_file_path)
            coverage_after = json.loads(coverage_result_after)
        except:
            coverage_after = {
                'coverage_percentage': 0,
                'tested_count': 0,
                'test_quality_score': 0
            }
        
        # Calculate improvements
        coverage_improvement = coverage_after.get('coverage_percentage', 0) - coverage_before.get('coverage_percentage', 0)
        tested_improvement = coverage_after.get('tested_count', 0) - coverage_before.get('tested_count', 0)
        quality_improvement = coverage_after.get('test_quality_score', 0) - coverage_before.get('test_quality_score', 0)
        
        print(f"    Coverage: {coverage_before.get('coverage_percentage', 0)}%   {coverage_after.get('coverage_percentage', 0)}% (+{coverage_improvement}%)")
        print(f"    Tested methods: {coverage_before.get('tested_count', 0)}   {coverage_after.get('tested_count', 0)} (+{tested_improvement})")
        print(f"    Quality score: {coverage_before.get('test_quality_score', 0)}   {coverage_after.get('test_quality_score', 0)} (+{quality_improvement})")
        print("")
        print(" Steps 1-6 complete! Test file generation finished.")
        print("")
        print(" To compile and run tests, use the 'full_test_workflow' tool")
        print("")
        
        # Update workflow state (without creating baseline files)
        update_workflow_state(
            source_file_path,
            step_2_generate_complete=True,
            test_file_path=test_file_path,
            test_count_baseline=test_count,
            quality_score_baseline=quality_score
        )
        
        # Build result - ONLY test generation
        result = {
            'success': True,
            'status': 'created',
            'test_file_path': test_file_path,
            'test_file_written': True,
            'test_count': test_count,
            'initial_test_count_recorded': test_count,
            'build_gn_updated': build_gn_success,
            'build_gn_message': build_gn_message,
            'build_gn_path': build_gn_path,
            'is_edge_specific': is_edge_file(source_file_path),
            'dependencies': {
                'total': len(all_deps),
                'list': all_deps,
                'from_build_gn': dependencies.get('deps_from_build_gn', False),
            },
            'coverage_analysis': {
                'before': {
                    'coverage_percentage': coverage_before.get('coverage_percentage', 0),
                    'tested_count': coverage_before.get('tested_count', 0),
                    'quality_score': coverage_before.get('test_quality_score', 0),
                },
                'after': {
                    'coverage_percentage': coverage_after.get('coverage_percentage', 0),
                    'tested_count': coverage_after.get('tested_count', 0),
                    'quality_score': coverage_after.get('test_quality_score', 0),
                },
                'improvement': {
                    'coverage_delta': coverage_improvement,
                    'tested_methods_added': tested_improvement,
                    'quality_delta': quality_improvement,
                },
                'summary': (
                    f" : {coverage_before.get('coverage_percentage', 0)}%   "
                    f"{coverage_after.get('coverage_percentage', 0)}% "
                    f"(+{coverage_improvement}%)\n"
                    f" : {coverage_before.get('tested_count', 0)}   "
                    f"{coverage_after.get('tested_count', 0)} "
                    f"(+{tested_improvement})\n"
                    f" : {coverage_before.get('test_quality_score', 0)}   "
                    f"{coverage_after.get('test_quality_score', 0)} "
                    f"(+{quality_improvement})"
                )
            },
            'message': f'Step 2 Complete - Test file generated successfully',
            'details': {
                'test_file': test_file_path,
                'test_count': test_count,
                'build_gn': build_gn_message,
                'dependencies': f'{len(all_deps)} deps auto-extracted'
            },
            # P1 优化: 添加醒目的质量报告
            'quality_report': generate_quality_report(write_result.get('validation', {})),
            'quality_score': write_result.get('validation', {}).get('quality_score', 0),
            'has_quality_issues': write_result.get('validation', {}).get('quality_score', 100) < 80,
            'validation_details': write_result.get('validation', {}),
            'summary': (
                f"Created test file: {os.path.basename(test_file_path)}\n"
                f"Generated {test_count} test cases with {todo_count} TODOs\n"
                f"Quality score: {quality_score}/100\n"
                f"Updated BUILD.gn with {len(all_deps)} dependencies\n"
                f"Coverage: {coverage_before.get('coverage_percentage', 0)}% -> {coverage_after.get('coverage_percentage', 0)}%"
            ),
            'test_file_info': {
                'path': test_file_path,
                'test_count': test_count,
                'todo_count': todo_count,
                'quality_score': quality_score,
                'needs_enhancement': todo_count > 0 or quality_score < 85
            },
            'next_step_required': '[!]️ MANDATORY: Review and enhance ALL tests - NO SHORTCUTS',
            'enhancement_guidance': {
                'what_to_do': 'Read both source and test files, then FULLY implement all tests',
                'critical_rules': [
                    '[SKIP] NEVER use DISABLED_ prefix to skip tests',
                    '[SKIP] NEVER leave TODO comments without implementation',
                    '[SKIP] NEVER use placeholder assertions like EXPECT_TRUE(true)',
                    '[OK] MUST create proper mocks/fakes for complex dependencies',
                    '[OK] MUST test all methods, even complex ones',
                    '[OK] MUST have 3+ meaningful assertions per test'
                ],
                'focus_areas': [
                    f'Replace ALL {todo_count} TODO markers with real test code' if todo_count > 0 else 'Improve all test assertions',
                    'Create mock objects for Browser, ProfileIOS, EdgeRewardsService if needed',
                    'Use FakeChromeBrowserState or TestChromeBrowserState for browser dependencies',
                    'Add meaningful EXPECT_* assertions testing actual behavior',
                    'Follow AAA pattern: Arrange -> Act -> Assert',
                    'Test edge cases and error conditions'
                ],
                'files_to_read': [source_file_path, test_file_path],
                'common_patterns': {
                    'for_browser_deps': 'Use FakeChromeBrowserState and create test Browser instance',
                    'for_services': 'Use mock or fake implementations, not nil',
                    'for_methods': 'Test return values, state changes, and side effects'
                },
                'after_enhancement': 'Call update_build_file_for_test tool',
                'quality_check': 'Every test must be runnable and test real behavior'
            }
        }
        
        # Add BUILD_edge.gni instructions if this is Edge-specific
        if is_edge_file(source_file_path):
            result['edge_specific_instructions'] = {
                'file_to_edit': 'ios/chrome/test/BUILD_edge.gni',
                'template': 'edge_overlay_test_ios_chrome_unittests',
                'target_to_add': f'//{str(Path(build_gn_path).parent)}:unit_tests',
                'instructions': generate_build_edge_gni_instructions(source_file_path, build_gn_path)
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'tool': 'generate_ios_unittest_file',
            'error': str(e)
        })


@mcp.tool(name='check_ios_test_coverage', structured_output=False)
def check_ios_test_coverage(source_file_path: str) -> str:
    """Check test coverage for iOS source file. Returns coverage percentage and missing tests.
    
    This tool analyzes test coverage by comparing the source file with its test file:
    - Identifies which methods/functions are tested
    - Calculates coverage percentage
    - Lists missing tests
    - Provides quality score based on test patterns
    
    Args:
        source_file_path: Path to the iOS source file (relative to Chromium src root)
        
    Returns:
        JSON string containing:
        - coverage_percentage: Percentage of code covered by tests (0-100)
        - tested_count: Number of methods/functions with tests
        - total_count: Total number of testable methods/functions
        - missing_tests: List of methods/functions without tests
        - test_quality_score: Quality score based on test patterns (0-100)
        - recommendations: Suggestions for improving test coverage
    """
    import json
    
    if not is_ios_source_file(source_file_path):
        return json.dumps({
            'error': f'Not an iOS source file: {source_file_path}'
        })
    
    try:
        # Analyze the file
        analysis_result = analyze_ios_code_for_testing(source_file_path)
        analysis = json.loads(analysis_result)
        
        if 'error' in analysis:
            return json.dumps(analysis)
        
        if not analysis['test_file_exists']:
            return json.dumps({
                'coverage_percentage': 0,
                'tested_count': 0,
                'untested_count': analysis['testable_elements']['method_count'] +
                                analysis['testable_elements']['function_count'],
                'untested_methods': 'All methods (no test file exists)',
                'test_quality_score': 0,
                'recommendations': [
                    'Create test file - no tests exist',
                    'Use generate_ios_unittest_file tool to create tests'
                ]
            })
        
        # Calculate coverage
        source_content = read_file_content(source_file_path)
        testable = extract_testable_interfaces(source_content)
        total_testable = len(testable['methods']) + len(testable['functions'])
        
        if total_testable == 0:
            # Check if this is truly a header-only file or if extraction failed
            # A .mm file with actual implementation should have methods
            if source_file_path.endswith('.mm') and len(source_content) > 500:
                # Likely extraction failed - report low coverage to trigger update
                sys.stderr.write(f"[!]️  No testable methods extracted from {source_file_path}\n")
                sys.stderr.write(f"   File size: {len(source_content)} bytes\n")
                sys.stderr.write(f"   This might indicate extraction failure\n")
                sys.stderr.write(f"   Returning 0% coverage to trigger test generation\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'success',
                    'tool': 'check_ios_test_coverage',
                    'coverage_percentage': 0,
                    'untested_count': 999,  # Large number to force update
                    'untested_methods': ['Methods could not be extracted - manual review needed'],
                    'message': 'No testable methods found (extraction may have failed)',
                    'test_quality_score': 0,
                    'recommendations': ['Use update_existing_tests to add comprehensive tests']
                })
            else:
                # Truly header-only or very small file
                return json.dumps({
                    'status': 'success',
                    'tool': 'check_ios_test_coverage',
                    'coverage_percentage': 100,
                    'untested_count': 0,
                    'untested_methods': [],
                    'message': 'No testable methods found (might be header-only)',
                    'test_quality_score': 100
                })
        
        test_content = read_file_content(analysis['test_file_path'])
        test_analysis = analyze_existing_tests(test_content)
        
        # Convert tested_methods list back to set for comparison
        tested_methods = set(test_analysis['tested_methods'])
        all_methods = set(testable['methods']) | set(testable['functions'])
        untested = all_methods - tested_methods
        
        tested_count = len(tested_methods & all_methods)
        coverage_pct = int((tested_count / total_testable) * 100)
        
        # Quality score considers test count and coverage
        quality_score = min(100, int(
            (coverage_pct * 0.7) + 
            (min(test_analysis['test_count'], 20) * 1.5)
        ))
        
        recommendations = []
        if coverage_pct < 50:
            recommendations.append('Coverage is low - add more tests')
        if len(untested) > 0:
            recommendations.append(
                f'Add tests for {len(untested)} untested methods'
            )
        if test_analysis['test_count'] < 3:
            recommendations.append('Add more comprehensive test cases')
        if not test_analysis['test_fixtures']:
            recommendations.append('Consider using test fixtures for better organization')
        
        return json.dumps({
            'status': 'success',
            'tool': 'check_ios_test_coverage',
            'source_file': source_file_path,
            'test_file': analysis['test_file_path'],
            'coverage_percentage': coverage_pct,
            'tested_count': tested_count,
            'untested_count': len(untested),
            'untested_methods': list(untested)[:10],  # Limit to first 10
            'total_test_cases': test_analysis['test_count'],
            'test_fixtures': test_analysis['test_fixtures'],
            'test_quality_score': quality_score,
            'recommendations': recommendations
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'tool': 'check_ios_test_coverage',
            'error': str(e)
        })


# ============================================================================
# QUALITY GATE: Test Enhancement Verification
# ============================================================================

@mcp.tool(name='verify_test_enhancement_complete', structured_output=False)
def verify_test_enhancement_complete(
    source_file_path: str,
    test_file_path: str = None
) -> str:
    """Verify test enhancement is complete before proceeding to compilation.
    
    This is a QUALITY GATE that blocks workflow progression if:
    - Tests have been deleted
    - DISABLED_ prefix is used
    - TODO comments remain
    - Placeholder assertions exist
    - Test quality is too low
    
    Args:
        source_file_path: Path to source file
        test_file_path: Path to test file (auto-detected if not provided)
        
    Returns:
        JSON with verification result and blocking issues if any
    """
    import json
    from pathlib import Path
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"[SEARCH] QUALITY GATE: Verifying Test Enhancement\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    try:
        src_root = get_chromium_src_root()
        
        # Get workflow state
        state = get_workflow_state(source_file_path)
        
        if not state.get('step_2_generate_complete'):
            return json.dumps({
                'status': 'error',
                'tool': 'verify_test_enhancement_complete',
                'error': 'Step 2 (test generation) must be completed first',
                'required_action': 'Call generate_ios_unittest_file first'
            })
        
        # Auto-detect test file path
        if not test_file_path:
            test_file_path = state.get('test_file_path')
            if not test_file_path:
                test_file_path = source_file_path.replace('.mm', '_unittest.mm').replace('.m', '_unittest.mm')
        
        test_path = src_root / test_file_path
        
        if not test_path.exists():
            return json.dumps({
                'status': 'error',
                'tool': 'verify_test_enhancement_complete',
                'error': f'Test file not found: {test_file_path}'
            })
        
        # Read test file
        with open(test_path, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        # Load baseline from generation step
        baseline_test_count = state.get('test_count_baseline', 0)
        
        # Check for quality issues
        current_test_count = test_content.count('TEST_F')
        has_disabled = 'DISABLED_' in test_content
        todo_count = test_content.count('TODO')
        has_placeholder = 'EXPECT_TRUE(true)' in test_content or 'EXPECT_FALSE(false)' in test_content
        
        # Blocking issues
        blocking_issues = []
        warnings = []
        
        if current_test_count < baseline_test_count:
            blocking_issues.append(
                f'[FAIL] CRITICAL: Test count decreased from {baseline_test_count} to {current_test_count}. '
                f'Tests have been deleted! This is FORBIDDEN.'
            )
        
        if has_disabled:
            blocking_issues.append(
                '[FAIL] CRITICAL: DISABLED_ prefix found. Using DISABLED_ to skip tests is FORBIDDEN. '
                'Create proper mocks instead.'
            )
        
        if todo_count > baseline_test_count * 0.3:  # More than 30% TODOs
            blocking_issues.append(
                f'[FAIL] CRITICAL: Too many TODO comments ({todo_count}). '
                'Tests must be implemented, not left as TODOs.'
            )
        
        if has_placeholder:
            blocking_issues.append(
                '[FAIL] CRITICAL: Placeholder assertions found (EXPECT_TRUE(true) or EXPECT_FALSE(false)). '
                'All assertions must test actual behavior.'
            )
        
        # Warnings (non-blocking but should be addressed)
        if todo_count > 0:
            warnings.append(
                f'[!]️  WARNING: {todo_count} TODO comments found. Consider implementing them.'
            )
        
        # Calculate quality metrics
        assertion_count = test_content.count('EXPECT_')
        avg_assertions_per_test = assertion_count / current_test_count if current_test_count > 0 else 0
        
        if avg_assertions_per_test < 2:
            warnings.append(
                f'[!]️  WARNING: Low assertion density ({avg_assertions_per_test:.1f} per test). '
                'Aim for 3+ meaningful assertions per test.'
            )
        
        sys.stderr.write(f"Test count: {current_test_count} (baseline: {baseline_test_count})\n")
        sys.stderr.write(f"TODO count: {todo_count}\n")
        sys.stderr.write(f"Assertions per test: {avg_assertions_per_test:.1f}\n")
        sys.stderr.write(f"Blocking issues: {len(blocking_issues)}\n")
        sys.stderr.write(f"Warnings: {len(warnings)}\n\n")
        sys.stderr.flush()
        
        if blocking_issues:
            sys.stderr.write("[FAIL] VERIFICATION FAILED\n")
            for issue in blocking_issues:
                sys.stderr.write(f"  {issue}\n")
            sys.stderr.write("\n[!]️  FIX THESE ISSUES BEFORE PROCEEDING!\n\n")
            sys.stderr.flush()
            
            return json.dumps({
                'status': 'blocked',
                'tool': 'verify_test_enhancement_complete',
                'message': '[FAIL] Quality gate FAILED - Tests need improvement',
                'blocking_issues': blocking_issues,
                'warnings': warnings,
                'test_file': test_file_path,
                'test_count': current_test_count,
                'baseline_test_count': baseline_test_count,
                'required_actions': [
                    'Fix ALL blocking issues listed above',
                    'Do NOT delete tests',
                    'Do NOT use DISABLED_ prefix',
                    'Implement tests instead of leaving TODOs',
                    'Replace placeholder assertions with real ones',
                    'After fixing, call verify_test_enhancement_complete again'
                ],
                'next_action': 'FIX_BLOCKING_ISSUES_THEN_RETRY_VERIFICATION'
            }, indent=2)
        
        # Verification passed!
        sys.stderr.write("[OK] VERIFICATION PASSED\n\n")
        sys.stderr.flush()
        
        # ========================================================================
        # AUTO-CLEAN: Remove DELETE_SECTION markers after enhancement
        # ========================================================================
        sys.stderr.write("[CLEAN] Auto-cleaning DELETE sections from test file...\n")
        sys.stderr.flush()
        
        clean_result = clean_delete_sections_from_test_file(test_file_path)
        
        if clean_result.get('cleaned'):
            sys.stderr.write(f"[OK] Removed {len(clean_result['sections_removed'])} DELETE section(s)\n")
            sys.stderr.write(f"    Lines removed: {clean_result.get('lines_removed', 0)}\n\n")
        elif 'error' not in clean_result:
            sys.stderr.write("[OK] No DELETE sections found (already clean)\n\n")
        else:
            sys.stderr.write(f"[!]️  Warning: Failed to clean DELETE sections: {clean_result.get('error')}\n\n")
        
        sys.stderr.flush()
        
        # Update workflow state
        update_workflow_state(
            source_file_path,
            step_3_enhancement_verified=True
        )
        
        return json.dumps({
            'status': 'verified',
            'tool': 'verify_test_enhancement_complete',
            'message': '[OK] Test enhancement verified - Ready for compilation',
            'test_file': test_file_path,
            'test_count': current_test_count,
            'baseline_test_count': baseline_test_count,
            'quality_metrics': {
                'todo_count': todo_count,
                'assertions_per_test': round(avg_assertions_per_test, 1),
                'has_disabled': has_disabled,
                'has_placeholder': has_placeholder
            },
            'warnings': warnings,
            'next_step': 'Proceed to Step 4: update_build_file_for_test or Step 5: compile_ios_unittest'
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'tool': 'verify_test_enhancement_complete',
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# Compile iOS Unit Tests
# ============================================================================

@mcp.tool(name='compile_ios_unittest', structured_output=False)
def compile_ios_unittest(
    source_file: str,
    out_dir: str = 'out/Debug-iphonesimulator'
) -> str:
    """[!][!][!] MANDATORY MCP TOOL - NEVER USE run_in_terminal [!][!][!]
    
    [STOP] BEFORE YOU THINK "LET ME USE run_in_terminal" - STOP!
    
    [FAIL][FAIL][FAIL] ABSOLUTELY FORBIDDEN [FAIL][FAIL][FAIL]
       - run_in_terminal with autoninja
       - Any terminal command for compilation
       - If you are considering these, you are making a MISTAKE!
    
    [OK][OK][OK] YOU MUST USE THIS MCP TOOL [OK][OK][OK]
       - This is the ONLY correct way to compile iOS tests
       - Do NOT look for alternatives
       - Do NOT try to be clever with run_in_terminal
    
    [TARGET] Why this tool is REQUIRED (not optional):
    [OK] Auto-detects correct test target (ios_chrome_unittests, ios_web_unittests, etc.)
    [OK] Automatic error analysis if compilation fails
    [OK] Returns batch fix guidance with concrete code examples
    [OK] Tracks compilation state for workflow
    [OK] Formats output for better visibility
    
    This tool automatically:
    1. Detects the correct test target from source file path
    2. Executes compilation using autoninja
    3. If compilation fails -> calls analyze_compilation_errors automatically
    4. Returns detailed fix guidance with multi_replace_string_in_file examples
    5. After Copilot fixes -> call this tool again to recompile
    6. Loop: compile -> fix -> compile until success
    
    Args:
        source_file: Path to source file (relative to Chromium src root)
                    Example: "ios/chrome/browser/ui/main/my_feature.mm"
        out_dir: Build output directory (default: 'out/Debug-iphonesimulator')
        
    Returns:
        Success: Formatted summary with compilation output
        Failure: Detailed fix guidance with code examples
    """
    import json
    import subprocess
    import sys
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"[BUILD] COMPILE iOS UNIT TESTS (MCP TOOL)\n")
    sys.stderr.write(f"{'='*80}\n")
    sys.stderr.write(f"[!]️  IMPORTANT: You are using the CORRECT MCP tool!\n")
    sys.stderr.write(f"[SKIP] DO NOT switch to run_in_terminal - this tool provides:\n")
    sys.stderr.write(f"   [OK] Auto error analysis\n")
    sys.stderr.write(f"   [OK] Batch fix guidance\n")
    sys.stderr.write(f"   [OK] Workflow tracking\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    try:
        # Check workflow state (non-fatal)
        state = {}
        try:
            state = get_workflow_state(source_file)
        except:
            pass  # State check is optional, don't fail on this
        
        if not state.get('step_3_enhancement_verified'):
            sys.stderr.write("ℹ️  Note: Step 3 enhancement not verified (this is OK)\n")
            sys.stderr.write("   Proceeding with compilation...\n\n")
            sys.stderr.flush()
        
        src_root = get_chromium_src_root()
        
        # Auto-detect test target based on source file path
        target = detect_test_target(source_file)
        
        # Calculate test file path
        if source_file.endswith('.mm'):
            test_file_path = source_file[:-3] + '_unittest.mm'
        elif source_file.endswith('.m'):
            test_file_path = source_file[:-2] + '_unittest.mm'
        else:
            test_file_path = source_file + '_unittest.mm'
        
        sys.stderr.write(f"[DIR] Source: {source_file}\n")
        sys.stderr.write(f"[DIR] Test: {test_file_path}\n")
        sys.stderr.write(f"[TARGET] Target: {target}\n")
        sys.stderr.write(f"📂 Out Dir: {out_dir}\n\n")
        sys.stderr.flush()
        
        # Construct compile command
        # -k 10000: Continue compiling even after errors (expose all errors at once)
        compile_cmd = f'autoninja -C {out_dir} {target} -k 10000'
        
        sys.stderr.write(f"\n{'='*80}\n")
        sys.stderr.write(f"[BUILD] STARTING COMPILATION\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"Command: {compile_cmd}\n")
        sys.stderr.write(f"[TIP] Using -k 10000: Will continue after errors to expose ALL issues\n")
        sys.stderr.write(f"\n[WAIT] Please wait - compilation in progress...\n")
        sys.stderr.write(f"   (This typically takes 30-60 seconds for incremental builds)\n")
        sys.stderr.write(f"   (First-time builds may take several minutes)\n")
        sys.stderr.write(f"\n[REPORT] Real-time output:\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        sys.stderr.write(f"[LAUNCH] Compilation starting...\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        compile_process = subprocess.Popen(
            compile_cmd,
            shell=True,
            cwd=src_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered for real-time output
        )
        
        # Collect output and display in real-time to VS Code
        compilation_output_lines = []
        start_time = time.time()
        progress_markers = []  # Collect progress checkpoints
        line_count = 0
        
        for line in compile_process.stdout:
            # Write to stderr for real-time display in VS Code Output panel
            sys.stderr.write(line)
            sys.stderr.flush()
            
            compilation_output_lines.append(line)
            line_count += 1
            
            # Collect key progress markers
            if '[' in line and '/' in line:  # ninja progress like [10/150]
                progress_markers.append(line.strip())
        
        # Wait for process to complete
        compile_process.wait(timeout=600)
        compilation_output = ''.join(compilation_output_lines)
        
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        # Check if compilation succeeded
        # CRITICAL: When using -k flag, autoninja may return 0 even with errors
        # We must also check for error indicators in the output
        has_error_generated = 'error generated' in compilation_output.lower()
        has_build_failed = 'build failed' in compilation_output.lower()
        has_failed_marker = 'failed:' in compilation_output.lower()
        
        sys.stderr.write(f"\n[SEARCH] Compilation result analysis:\n")
        sys.stderr.write(f"   Return code: {compile_process.returncode}\n")
        sys.stderr.write(f"   Has 'error generated': {has_error_generated}\n")
        sys.stderr.write(f"   Has 'build failed': {has_build_failed}\n")
        sys.stderr.write(f"   Has 'FAILED:': {has_failed_marker}\n")
        sys.stderr.flush()
        
        has_errors = (
            has_error_generated or
            has_build_failed or
            has_failed_marker or
            compile_process.returncode != 0
        )
        
        if not has_errors and compile_process.returncode == 0:
            sys.stderr.write("\n[OK] Compilation succeeded - no errors detected!\n\n")
            sys.stderr.flush()
            
            # Update workflow state
            update_workflow_state(
                source_file,
                step_5_compilation_success=True
            )
            
            # Calculate compilation time
            elapsed_time = int(time.time() - start_time)
            
            # Extract detailed compilation output for user visibility
            output_lines = compilation_output.split('\n')
            # Show last 50 lines for more context
            detailed_output = '\n'.join(output_lines[-50:]) if len(output_lines) > 50 else compilation_output
            
            # Extract compilation progress summary
            total_lines = len(compilation_output_lines)
            last_progress = progress_markers[-1] if progress_markers else "N/A"
            
            # Generate execution fingerprint to prevent Copilot from fabricating results
            execution_proof = generate_execution_fingerprint('compile_ios_unittest', compilation_output)
            
            return f"""
{'='*80}
[OK] COMPILATION SUCCEEDED
{'='*80}

[TIME]  Time taken: {elapsed_time}s
[REPORT] Output lines: {total_lines}
[TARGET] Target: {target}
# 📂 Out dir: {out_dir}
[DIR] Test file: {test_file_path}
{f'[LOOP] Last progress: {last_progress}' if progress_markers else ''}

[INFO] Compilation summary (last 50 lines):
{'='*80}
{detailed_output}
{'='*80}

[OK] Ready to run tests!

Next step: Use run_ios_unittest to execute the tests
{'='*80}

""" + json.dumps({
                'status': 'success',
                'tool': 'compile_ios_unittest',
                'target': target,
                'out_dir': out_dir,
                'test_file': test_file_path,
                'elapsed_time_seconds': elapsed_time,
                'next_step': 'Use run_ios_unittest to run the tests',
                **execution_proof  # Add execution fingerprint
            }, indent=2)
        
        # Compilation failed - auto-analyze
        sys.stderr.write("\n[FAIL] Compilation failed\n")
        sys.stderr.write("[SEARCH] Auto-analyzing compilation errors...\n\n")
        sys.stderr.flush()
        
        # Auto-call analyze_compilation_errors
        error_analysis = analyze_compilation_errors(
            test_file_path=test_file_path,
            compilation_output=compilation_output
        )
        
        # analyze_compilation_errors returns: prompt text + JSON at the end
        # Try to extract JSON from the end of the response
        try:
            # Find the last JSON object in the response
            last_brace = error_analysis.rfind('}')
            if last_brace > 0:
                # Find the matching opening brace
                brace_count = 0
                json_start = last_brace
                for i in range(last_brace, -1, -1):
                    if error_analysis[i] == '}':
                        brace_count += 1
                    elif error_analysis[i] == '{':
                        brace_count -= 1
                        if brace_count == 0:
                            json_start = i
                            break
                
                json_str = error_analysis[json_start:last_brace+1]
                analysis_result = json.loads(json_str)
            else:
                # Fallback: treat entire response as plain text
                analysis_result = {
                    'status': 'compilation_failed_need_fix',
                    'message': error_analysis,
                    'COPILOT_INSTRUCTIONS': []
                }
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, treat as plain text
            analysis_result = {
                'status': 'compilation_failed_need_fix',
                'message': error_analysis,
                'COPILOT_INSTRUCTIONS': []
            }
        
        return f"""\n{'='*80}
# [!][!][!] COMPILATION FAILED - STOP AND FIX ERRORS NOW [!][!][!]
{'='*80}

[STOP][STOP][STOP] BEFORE YOU DO ANYTHING ELSE - READ THIS [STOP][STOP][STOP]

[SKIP] DO NOT call full_test_workflow again (test file already exists!)
[SKIP] DO NOT call run_ios_unittest (compilation must succeed first!)
[SKIP] DO NOT use run_in_terminal with autoninja (use compile_ios_unittest!)
[SKIP] DO NOT try other tools or operations

[OK][OK][OK] YOU MUST DO THIS AND ONLY THIS [OK][OK][OK]

STEP 1: Read the error analysis below carefully
STEP 2: Fix ALL compilation errors using multi_replace_string_in_file
STEP 3: Call compile_ios_unittest for {source_file} to recompile
STEP 4: If still fails, repeat from STEP 1
STEP 5: After compilation succeeds, then call run_ios_unittest

# [!]️  YOU ARE STUCK IN A LOOP IF:
   - You keep calling compile_ios_unittest without fixing errors
   - You call full_test_workflow again (DON'T! File exists!)
   - You try to run tests before compilation succeeds
   - You use run_in_terminal instead of compile_ios_unittest

[OK] CORRECT WORKFLOW:
   fix errors -> compile_ios_unittest -> (repeat if fail) -> run_ios_unittest

{'='*80}

{error_analysis}

{'='*80}
# [!] NEXT ACTION: Fix the errors above, then call compile_ios_unittest
{'='*80}
""" + json.dumps({
            'status': 'COMPILATION_FAILED_MUST_FIX_BEFORE_PROCEEDING',
            'tool': 'compile_ios_unittest',
            'CRITICAL_WARNING': '[!] YOU MUST FIX COMPILATION ERRORS BEFORE ANY OTHER ACTION',
            'FORBIDDEN_ACTIONS': [
                'DO NOT call full_test_workflow (test file exists!)',
                'DO NOT call run_ios_unittest (must compile first!)',
                'DO NOT use run_in_terminal for compilation',
                'DO NOT try other unrelated operations'
            ],
            'REQUIRED_NEXT_STEP': f'1. Fix errors in test file, 2. Call compile_ios_unittest for {source_file}',
            'target': target,
            'out_dir': out_dir,
            'test_file': test_file_path,
            'workflow_state': 'BLOCKED_ON_COMPILATION_ERRORS',
            'retry_command': f'compile_ios_unittest({{"source_file": "{source_file}"}})'
        }, indent=2)
        
    except subprocess.TimeoutExpired:
        return json.dumps({
            'status': 'error',
            'tool': 'compile_ios_unittest',
            'error': 'Compilation timed out (10 minutes)'
        })
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'tool': 'compile_ios_unittest',
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================================================
# Simplified Shortcuts for VS Code Users
# ============================================================================

@mcp.prompt(name='generate_unittest_for_current_file')
# ============================================================================
# Run iOS Unit Tests
# ============================================================================

@mcp.tool(name='run_ios_unittest', structured_output=False)
def run_ios_unittest(
    test_filter: str,
    test_file_path: str = None,
    source_file_path: str = None,
    out_dir: str = 'out/Debug-iphonesimulator',
    additional_args: str = None
) -> str:
    """[!][!][!] MANDATORY MCP TOOL - NEVER USE run_in_terminal [!][!][!]
    
    [STOP] BEFORE YOU THINK "LET ME USE run_in_terminal" - STOP!
    
    [FAIL][FAIL][FAIL] ABSOLUTELY FORBIDDEN [FAIL][FAIL][FAIL]
       - run_in_terminal with python3 ios/tools/run_unittests.py
       - run_in_terminal with iossim
       - Any terminal command for running tests
       - If you are considering these, you are making a MISTAKE!
    
    [OK][OK][OK] YOU MUST USE THIS MCP TOOL [OK][OK][OK]
       - This is the ONLY correct way to run iOS tests
       - Do NOT look for alternatives
       - Do NOT try to be clever with run_in_terminal
    
    [TARGET] Why this tool is REQUIRED (not optional):
    [OK] Uses correct iOS test runner (ios/tools/run_unittests.py)
    [OK] Automatic runtime error analysis if tests fail
    [OK] Returns specific fix guidance with line numbers
    [OK] Tracks test state for workflow
    [OK] Formats test results for better visibility (lists all passed/failed tests)
    
    This tool automatically:
    1. Executes tests using official iOS unit test runner (ios/tools/run_unittests.py)
    2. If tests fail -> calls analyze_runtime_errors automatically
    3. Returns detailed fix guidance with error context
    4. After Copilot fixes -> MUST recompile (use compile_ios_unittest)
    5. Then call this tool again to rerun tests
    6. Loop: fix -> compile_ios_unittest -> run_ios_unittest until all pass [OK]
    
    [LOOP] CRITICAL WORKFLOW after fixing test failures:
       1. Fix test code
       2. Call compile_ios_unittest (MUST recompile!)
       3. Call run_ios_unittest again (rerun tests)
       4. Repeat until all tests pass
    
    Note: Coverage collection is configured at build time via args.gn (use_clang_coverage=true).
    If enabled, .profraw files are automatically generated during test execution.
    
    Args:
        test_filter: GTest filter pattern (e.g., 'MyClassTest.*' or 'MyFeatureTest.TestMethod')
        test_file_path: Path to test file (for error analysis if tests fail)
                       Example: "ios/chrome/browser/ui/main/my_feature_unittest.mm"
        source_file_path: Optional path to source file being tested
        out_dir: Build output directory (default: 'out/Debug-iphonesimulator')
        additional_args: Additional arguments to pass to the test runner
        
    Returns:
        Success: Formatted list of all passed tests with [OK]
        Failure: Detailed fix guidance with error messages and line numbers
    """
    import json
    import subprocess
    import sys
    import re
    
    try:
        src_root = get_chromium_src_root()
        
        # Detect test target intelligently
        # Use source_file_path if available, otherwise test_file_path
        file_for_detection = source_file_path or test_file_path
        if file_for_detection:
            test_target = detect_test_target(file_for_detection)
        else:
            test_target = 'ios_chrome_unittests'  # Fallback
        
        # Build the test app path based on the detected target
        test_app_path = f"{out_dir}/{test_target}.app"
        
        # CRITICAL: Different test targets require different execution methods
        # ios_chrome_unittests: Use run_unittests.py (ONLY supports ios_chrome_unittests)
        # All other targets: Use xcrun simctl launch directly
        
        use_run_unittests_script = test_target == 'ios_chrome_unittests'
        
        if use_run_unittests_script:
            # Method 1: Use ios/tools/run_unittests.py (ONLY for ios_chrome_unittests)
            cmd_parts = [
                'python3',
                'ios/tools/run_unittests.py',
                '--out-dir', out_dir,
                '--gtest_filter', test_filter
            ]
            
            if additional_args:
                cmd_parts.extend(additional_args.split())
                
            sys.stderr.write(f"\n{'='*80}\n")
            sys.stderr.write(f"[RUN] RUNNING iOS TESTS (MCP TOOL)\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"[!]️  IMPORTANT: You are using the CORRECT MCP tool!\n")
            sys.stderr.write(f"[SKIP] DO NOT switch to run_in_terminal - this tool provides:\n")
            sys.stderr.write(f"   [OK] Auto error analysis if tests fail\n")
            sys.stderr.write(f"   [OK] Detailed fix guidance\n")
            sys.stderr.write(f"   [OK] Workflow tracking\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"Test filter: {test_filter}\n")
            sys.stderr.write(f"Test target: {test_target}\n")
            sys.stderr.write(f"Out dir: {out_dir}\n")
            sys.stderr.write(f"Execution method: run_unittests.py\n")
            sys.stderr.write(f"Working dir: {src_root}\n")
            sys.stderr.write(f"\n[WAIT] Please wait - starting iOS simulator and running tests...\n")
            sys.stderr.write(f"   (iOS simulator startup: ~10-20 seconds)\n")
            sys.stderr.write(f"   (Test execution: depends on test count)\n")
            sys.stderr.write(f"\n[REPORT] Real-time test output:\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.flush()
        else:
            # Method 2: Use xcrun simctl launch directly (for components_unittests, etc.)
            # First, get booted simulator UDID
            simctl_list_cmd = ['xcrun', 'simctl', 'list', 'devices', 'booted']
            simctl_result = subprocess.run(
                simctl_list_cmd,
                cwd=src_root,
                capture_output=True,
                text=True
            )
            
            # Extract UDID from output
            import re
            udid_match = re.search(r'\(([A-F0-9-]{36})\)', simctl_result.stdout)
            if not udid_match:
                return json.dumps({
                    'status': 'error',
                    'message': 'No booted iOS simulator found. Please boot a simulator first.',
                    'simctl_output': simctl_result.stdout
                }, indent=2)
            
            udid = udid_match.group(1)
            
            # Install the app on simulator
            install_cmd = ['xcrun', 'simctl', 'install', udid, test_app_path]
            subprocess.run(install_cmd, cwd=src_root, capture_output=True)
            
            # Get bundle ID from Info.plist
            plist_path = f"{test_app_path}/Info.plist"
            plist_cmd = ['plutil', '-p', plist_path]
            plist_result = subprocess.run(
                plist_cmd,
                cwd=src_root,
                capture_output=True,
                text=True
            )
            
            bundle_id_match = re.search(r'"CFBundleIdentifier"\s*=>\s*"([^"]+)"', plist_result.stdout)
            if not bundle_id_match:
                return json.dumps({
                    'status': 'error',
                    'message': f'Could not extract bundle ID from {plist_path}',
                    'plist_output': plist_result.stdout
                }, indent=2)
            
            bundle_id = bundle_id_match.group(1)
            
            # Build launch command
            cmd_parts = [
                'xcrun', 'simctl', 'launch',
                '--console-pty',  # Connect stdout/stderr
                udid,
                bundle_id,
                f'--gtest_filter={test_filter}'
            ]
            
            if additional_args:
                cmd_parts.extend(additional_args.split())
            
            sys.stderr.write(f"\n{'='*80}\n")
            sys.stderr.write(f"[RUN] RUNNING iOS TESTS (MCP TOOL)\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"[!]️  IMPORTANT: You are using the CORRECT MCP tool!\n")
            sys.stderr.write(f"[SKIP] DO NOT switch to run_in_terminal - this tool provides:\n")
            sys.stderr.write(f"   [OK] Auto error analysis if tests fail\n")
            sys.stderr.write(f"   [OK] Detailed fix guidance\n")
            sys.stderr.write(f"   [OK] Workflow tracking\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.write(f"Test filter: {test_filter}\n")
            sys.stderr.write(f"Test target: {test_target}\n")
            sys.stderr.write(f"Out dir: {out_dir}\n")
            sys.stderr.write(f"Execution method: xcrun simctl launch (direct)\n")
            sys.stderr.write(f"Simulator UDID: {udid}\n")
            sys.stderr.write(f"Bundle ID: {bundle_id}\n")
            sys.stderr.write(f"Working dir: {src_root}\n")
            sys.stderr.write(f"\n[WAIT] Please wait - starting iOS simulator and running tests...\n")
            sys.stderr.write(f"   (iOS simulator startup: ~5-10 seconds)\n")
            sys.stderr.write(f"   (Test execution: depends on test count)\n")
            sys.stderr.write(f"\n[REPORT] Real-time test output:\n")
            sys.stderr.write(f"{'='*80}\n")
            sys.stderr.flush()
        
        sys.stderr.write(f"[LAUNCH] Test execution starting...\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        test_process = subprocess.Popen(
            cmd_parts,
            cwd=src_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered for real-time output
        )
        
        test_output_lines = []
        start_time = time.time()
        
        for line in test_process.stdout:
            # Write to stderr for real-time display in VS Code Output panel
            sys.stderr.write(line)
            sys.stderr.flush()
            
            test_output_lines.append(line)
        
        test_process.wait(timeout=600)
        test_output = ''.join(test_output_lines)
        
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        # Check results
        # Strategy: Use summary line numbers if available (most accurate)
        # Fallback: Count individual test results
        
        # First try to extract from summary: "[  PASSED  ] 6 tests."
        passed_tests = 0
        summary_match = re.search(r'\[  PASSED  \]\s+(\d+)\s+test', test_output)
        if summary_match:
            passed_tests = int(summary_match.group(1))
        else:
            # Fallback: Count individual "[       OK ]" markers
            passed_tests = test_output.count('[       OK ]')
        
        # Extract failed count from summary: "[  FAILED  ] 3 tests, listed below:"
        failed_tests = 0
        failed_summary_match = re.search(r'\[  FAILED  \]\s+(\d+)\s+test', test_output)
        if failed_summary_match:
            failed_tests = int(failed_summary_match.group(1))
        else:
            # Fallback: Count individual "[  FAILED  ]" markers for test cases (not summary line)
            # Note: The summary also has "[  FAILED  ]" so we need to count carefully
            failed_markers = [line for line in test_output.split('\n') if '[  FAILED  ]' in line and '.' in line]
            failed_tests = len(failed_markers)
        
        # Check if tests were found and executed
        has_running_tests = '[ RUN      ]' in test_output or 'Running' in test_output
        has_test_summary = '[==========]' in test_output or '[  PASSED  ]' in test_output
        
        # CRITICAL: Detect crashes (multiple patterns)
        # IMPORTANT: Only detect actual crashes, not just non-zero exit codes
        # iOS test runner may return non-zero even when all tests pass (due to warnings/logs)
        has_crash = (
            'Check failed:' in test_output or 
            'Segmentation fault' in test_output or
            'ERROR: Test runner did not complete' in test_output or
            'Assuming crash' in test_output or
            'SIGABRT' in test_output or
            'SIGSEGV' in test_output or
            'Fatal error' in test_output or
            'Terminating app due to' in test_output
        )
        
        # Additional check: If we have test summary showing passed tests, it's not a crash
        # even if returncode is non-zero (iOS runner logs may trigger warnings)
        if has_test_summary and passed_tests > 0 and failed_tests == 0:
            has_crash = False
        
        # CRITICAL: Distinguish between "no tests found" vs "crash"
        if passed_tests == 0 and failed_tests == 0:
            if has_crash:
                # Tests crashed - treat as runtime error
                sys.stderr.write(f"\n[!] TESTS CRASHED during execution!\n")
                sys.stderr.write(f"   Detected crash indicators in output.\n")
                sys.stderr.write(f"   Analyzing crash details...\n\n")
                sys.stderr.flush()
                
                # Treat crash as test failure - call error analysis
                if not test_file_path:
                    # Extract crash-related output (last 5000 chars to include full backtrace)
                    crash_output = test_output[-5000:] if len(test_output) > 5000 else test_output
                    
                    # Try to find the actual crash section (from "Check failed" or crash signal)
                    crash_markers = ['Check failed:', 'SIGABRT', 'SIGSEGV', 'Segmentation fault', 'Assuming crash']
                    crash_start = -1
                    for marker in crash_markers:
                        pos = test_output.rfind(marker)
                        if pos > crash_start:
                            crash_start = pos
                    
                    if crash_start > 0:
                        # Include 500 chars before crash marker for context
                        crash_context_start = max(0, crash_start - 500)
                        crash_output = test_output[crash_context_start:]
                    
                    return f"""
{'='*80}
# [!][!][!] STOP! DO NOT USE run_in_terminal! [!][!][!]
{'='*80}

# [!]️  If you are thinking about using run_in_terminal to debug:
   [FAIL] THAT IS ABSOLUTELY FORBIDDEN!
   [OK] Use the crash analysis below from THIS TOOL

{'='*80}
# [!] TESTS CRASHED - CRASH ANALYSIS
{'='*80}

# [!]️  Tests crashed during execution but test_file_path not provided.

[SEARCH] Crash output (including backtrace):
{'='*80}
{crash_output}
{'='*80}

[TIP] To enable detailed crash analysis:
   Call run_ios_unittest with test_file_path parameter

{'='*80}
""" + json.dumps({
                        'status': 'crash',
                        'tool': 'run_ios_unittest',
                        'test_filter': test_filter,
                        'crash_output_length': len(crash_output),
                        'full_output_length': len(test_output),
                        'crash_output': crash_output[-3000:] if len(crash_output) > 3000 else crash_output,
                        'next_action': 'FIX_CRASH_THEN_RECOMPILE_AND_RERUN'
                    }, indent=2)
                
                # Auto-analyze crash
                error_analysis = analyze_runtime_errors(
                    test_file_path=test_file_path,
                    test_output=test_output,
                    source_file_path=source_file_path
                )
                
                # Extract JSON from analysis
                try:
                    last_brace = error_analysis.rfind('}')
                    if last_brace > 0:
                        brace_count = 0
                        json_start = last_brace
                        for i in range(last_brace, -1, -1):
                            if error_analysis[i] == '}':
                                brace_count += 1
                            elif error_analysis[i] == '{':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_start = i
                                    break
                        json_str = error_analysis[json_start:last_brace+1]
                        analysis_result = json.loads(json_str)
                    else:
                        analysis_result = {'status': 'crash', 'message': error_analysis}
                except (json.JSONDecodeError, ValueError):
                    analysis_result = {'status': 'crash', 'message': error_analysis}
                
                return f"""
{'='*80}
# [!][!][!] TESTS CRASHED - STOP AND FIX NOW [!][!][!]
{'='*80}

[STOP][STOP][STOP] BEFORE YOU DO ANYTHING ELSE - READ THIS [STOP][STOP][STOP]

[SKIP] DO NOT use run_in_terminal with python3 (STRICTLY FORBIDDEN!)
[SKIP] DO NOT use run_in_terminal with autoninja (STRICTLY FORBIDDEN!)
[SKIP] DO NOT try other tools or commands
[SKIP] DO NOT give up and report back to user

[OK][OK][OK] YOU MUST DO THIS AND ONLY THIS [OK][OK][OK]

STEP 1: Read the crash analysis below carefully
STEP 2: Fix the crash cause using multi_replace_string_in_file
STEP 3: Call compile_ios_unittest for {source_file_path or test_file_path} to recompile
STEP 4: Call run_ios_unittest with filter "{test_filter}" to rerun tests
STEP 5: If still crashes, repeat from STEP 1

# [!]️  YOU ARE IN AN INFINITE LOOP IF:
   - You use run_in_terminal instead of MCP tools (FORBIDDEN!)
   - You keep calling run_ios_unittest without fixing the crash
   - You give up and stop trying

[OK] CORRECT WORKFLOW:
   fix crash -> compile_ios_unittest -> run_ios_unittest -> (repeat if fail)

{'='*80}

{error_analysis}

{'='*80}
# [!] NEXT ACTION: Fix the crash above, then:
   1. Call compile_ios_unittest for {source_file_path or test_file_path}
   2. Call run_ios_unittest with filter "{test_filter}"
{'='*80}
""" + json.dumps({
                    'status': 'TESTS_CRASHED_MUST_FIX_BEFORE_PROCEEDING',
                    'tool': 'run_ios_unittest',
                    'CRITICAL_WARNING': '[!] YOU MUST FIX CRASH BEFORE ANY OTHER ACTION',
                    'FORBIDDEN_ACTIONS': [
                        'DO NOT use run_in_terminal with python3 (use run_ios_unittest MCP tool!)',
                        'DO NOT use run_in_terminal with autoninja (use compile_ios_unittest MCP tool!)',
                        'DO NOT try other unrelated operations',
                        'DO NOT give up or stop'
                    ],
                    'REQUIRED_NEXT_STEPS': [
                        '1. Fix crash in test file',
                        f'2. Call compile_ios_unittest for {source_file_path or test_file_path}',
                        f'3. Call run_ios_unittest with filter "{test_filter}"'
                    ],
                    'test_filter': test_filter,
                    'workflow_state': 'BLOCKED_ON_CRASH',
                    'retry_commands': [
                        f'compile_ios_unittest({{"source_file": "{source_file_path or test_file_path}"}})',
                        f'run_ios_unittest({{"test_filter": "{test_filter}", "test_file_path": "{test_file_path or "test_file"}"}})'
                    ]
                }, indent=2)
            
            # No crash - just no tests found
            sys.stderr.write(f"\n[FAIL] ERROR: No tests were executed!\n")
            sys.stderr.write(f"   This usually means the test filter didn't match any tests.\n")
            sys.stderr.write(f"   Test filter: {test_filter}\n\n")
            sys.stderr.flush()
            
            return f"""
{'='*80}
[FAIL] ERROR: NO TESTS WERE EXECUTED
{'='*80}

[TARGET] Test filter: {test_filter}
[REPORT] Results: 0 passed, 0 failed

# [!]️  This usually means the test filter didn't match any tests.

Possible causes:
  • Test filter doesn't match any test names
  • Tests are in different test fixture
  • Tests haven't been compiled into binary
  • Test app not found at expected path
  • iOS simulator not available

Suggestions:
  • Check test fixture name in test file
  • Verify test filter pattern is correct
  • Ensure compilation succeeded
  • Try running without filter to see all tests

{'='*80}

""" + json.dumps({
                'status': 'error',
                'tool': 'run_ios_unittest',
                'test_filter': test_filter,
                'passed': 0,
                'failed': 0,
                'next_action': 'CHECK_TEST_FILTER_AND_COMPILATION'
            }, indent=2)
        
        if test_process.returncode == 0 and failed_tests == 0 and not has_crash:
            sys.stderr.write(f"\n[OK] All {passed_tests} tests PASSED!\n\n")
            sys.stderr.flush()
            
            # Execute git ms format after all tests pass
            subprocess.run(['git', 'ms', 'format'], cwd=src_root)
            
            # Update workflow state
            state = get_workflow_state(source_file_path) if source_file_path else {}
            if source_file_path:
                update_workflow_state(
                    source_file_path,
                    step_6_tests_passed=True
                )
            
            # Extract test names from output for user visibility
            test_names = []
            for line in test_output.split('\n'):
                if '[ RUN      ]' in line:
                    test_name = line.split('[ RUN      ]')[1].strip()
                    test_names.append(test_name)
            
            # Use actual count from test_names if available (more accurate)
            if len(test_names) > 0:
                passed_tests = len(test_names)
            
            test_list = '\n'.join([f"  [OK] {name}" for name in test_names]) if test_names else f"  [OK] {passed_tests} tests"
            
            # Generate execution fingerprint to prevent Copilot from fabricating results
            execution_proof = generate_execution_fingerprint('run_ios_unittest', test_output)
            
            return f"""
{'='*80}
[OK] ALL TESTS PASSED!
{'='*80}

[TARGET] Test filter: {test_filter}
[REPORT] Total passed: {passed_tests}

[NOTE] Test results:
{test_list}

{'='*80}
# 🎉 All tests completed successfully!
{'='*80}

""" + json.dumps({
                'status': 'success',
                'tool': 'run_ios_unittest',
                'test_filter': test_filter,
                'passed': passed_tests,
                'test_names': test_names,
                'workflow_complete': source_file_path and state.get('step_6_tests_passed', False),
                **execution_proof  # Add execution fingerprint
            }, indent=2)
        
        # Tests failed - auto-analyze
        sys.stderr.write(f"\n[FAIL] Tests FAILED: {failed_tests} failures\n")
        sys.stderr.write("[SEARCH] Auto-analyzing errors...\n\n")
        sys.stderr.flush()
        
        # Need test_file_path for analysis
        if not test_file_path:
            # Try to infer from filter
            if '.*' in test_filter:
                test_class = test_filter.replace('.*', '')
                # Convert TestClass to test_class_unittest.mm pattern
                import re
                test_file_name = re.sub(r'([A-Z])', r'_\1', test_class).lower().strip('_') + '_unittest.mm'
                sys.stderr.write(f"[!]️  test_file_path not provided, cannot auto-analyze.\n")
                sys.stderr.write(f"   Hint: Add test_file_path parameter\n\n")
                return json.dumps({
                    'status': 'tests_failed_no_analysis',
                    'message': f'[FAIL] {failed_tests} tests failed',
                    'test_output': test_output[-3000:],
                    'instructions_for_copilot': [
                        'Tests failed but test_file_path was not provided.',
                        'To enable auto-analysis, call run_ios_unittest with test_file_path parameter.',
                        'Or manually call analyze_runtime_errors with the test output.'
                    ]
                }, indent=2)
        
        # Auto-analyze errors
        sys.stderr.write(f"\n[SEARCH] Calling analyze_runtime_errors...\n")
        sys.stderr.flush()
        
        error_analysis = analyze_runtime_errors(
            test_file_path=test_file_path,
            test_output=test_output,
            source_file_path=source_file_path
        )
        
        sys.stderr.write("\n[OK] analyze_runtime_errors returned!\n")
        sys.stderr.write(f"[REPORT] DEBUG: error_analysis length = {len(error_analysis)} chars\n")
        sys.stderr.write(f"[REPORT] DEBUG: error_analysis type = {type(error_analysis)}\n")
        newline_brace = '\n\n{'
        sys.stderr.write(f"[REPORT] DEBUG: Has '\\n\\n{{' = {(newline_brace in error_analysis)}\n")
        if len(error_analysis) < 2000:
            sys.stderr.write(f"[REPORT] DEBUG: Full content:\n{error_analysis}\n")
        else:
            sys.stderr.write(f"[REPORT] DEBUG: First 1000 chars:\n{error_analysis[:1000]}\n")
            sys.stderr.write(f"[REPORT] DEBUG: Last 1000 chars:\n{error_analysis[-1000:]}\n")
        sys.stderr.flush()
        
        # analyze_runtime_errors returns: prompt text + "\n\n" + JSON
        # Extract the prompt text (analysis) and JSON separately
        try:
            # Find where JSON starts (look for last occurrence of "\n\n{")
            json_separator = error_analysis.rfind('\n\n{')
            sys.stderr.write(f"[REPORT] DEBUG: json_separator position = {json_separator}\n")
            sys.stderr.flush()
            
            if json_separator > 0:
                # Split into analysis text and JSON
                analysis_message = error_analysis[:json_separator]
                json_part = error_analysis[json_separator+2:]  # Skip "\n\n"
                
                sys.stderr.write(f"[REPORT] DEBUG: analysis_message length = {len(analysis_message)}\n")
                sys.stderr.write(f"[REPORT] DEBUG: json_part length = {len(json_part)}\n")
                sys.stderr.write(f"[REPORT] DEBUG: json_part first 200 chars:\n{json_part[:200]}\n")
                sys.stderr.flush()
                
                # Parse JSON to extract COPILOT_INSTRUCTIONS
                analysis_result = json.loads(json_part)
                copilot_instructions = analysis_result.get('COPILOT_INSTRUCTIONS', [])
            else:
                # Fallback: no JSON found, treat entire response as analysis
                analysis_message = error_analysis
                copilot_instructions = []
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, use the entire response as analysis
            sys.stderr.write(f"[!]️  Warning: Could not parse JSON from error_analysis: {e}\n")
            sys.stderr.flush()
            analysis_message = error_analysis
            copilot_instructions = []
        
        # Extract relevant test failure section from test_output for display
        # Get section from first [RUN] to end of test summary
        first_run_idx = test_output.find('[ RUN      ]')
        last_line_idx = test_output.rfind('FAILED TEST')
        if last_line_idx < 0:
            last_line_idx = test_output.rfind('[  FAILED  ]')
        
        failure_section = ""
        if first_run_idx >= 0 and last_line_idx > first_run_idx:
            failure_section = test_output[first_run_idx:last_line_idx + 500]
        elif first_run_idx >= 0:
            failure_section = test_output[first_run_idx:]
        else:
            failure_section = test_output[-5000:]  # Last 5000 chars as fallback
        
        # Limit to reasonable size
        if len(failure_section) > 10000:
            failure_section = failure_section[:10000] + "\n...(truncated)"
        
        return f"""\n{'='*80}
# [!][!][!] TESTS FAILED - STOP AND FIX NOW [!][!][!]
{'='*80}

[STOP][STOP][STOP] BEFORE YOU DO ANYTHING ELSE - READ THIS [STOP][STOP][STOP]

[SKIP] DO NOT use run_in_terminal with python3 (STRICTLY FORBIDDEN!)
[SKIP] DO NOT use run_in_terminal with autoninja (STRICTLY FORBIDDEN!)
[SKIP] DO NOT try other tools or commands
[SKIP] DO NOT give up and report back to user

[OK][OK][OK] YOU MUST DO THIS AND ONLY THIS [OK][OK][OK]

STEP 1: Read the error analysis below carefully
STEP 2: Fix ALL test failures using multi_replace_string_in_file
STEP 3: Call compile_ios_unittest for {source_file_path or 'source_file'} to recompile
STEP 4: Call run_ios_unittest with filter "{test_filter}" to rerun tests
STEP 5: If still fails, repeat from STEP 1

# [!]️  YOU ARE IN AN INFINITE LOOP IF:
   - You use run_in_terminal instead of MCP tools (FORBIDDEN!)
   - You keep calling run_ios_unittest without fixing errors
   - You give up and stop trying

[OK] CORRECT WORKFLOW:
   fix errors -> compile_ios_unittest -> run_ios_unittest -> (repeat if fail)

{'='*80}

[FAIL] {failed_tests} test(s) failed, {passed_tests} passed

{'='*80}
# [!] TEST FAILURE DETAILS
{'='*80}

{failure_section}

{'='*80}
[INFO] Complete test output available in analysis_message
{analysis_message[:2000] if analysis_message else '(No detailed analysis available)'}
{'='*80}

{'='*80}
# [!] NEXT ACTION: Fix the errors above, then:
   1. Call compile_ios_unittest for {source_file_path or 'source_file'}
   2. Call run_ios_unittest with filter "{test_filter}"
{'='*80}
""" + json.dumps({
            'status': 'TESTS_FAILED_MUST_FIX_BEFORE_PROCEEDING',
            'tool': 'run_ios_unittest',
            'CRITICAL_WARNING': '[!] YOU MUST FIX TEST FAILURES BEFORE ANY OTHER ACTION',
            'FORBIDDEN_ACTIONS': [
                'DO NOT use run_in_terminal with python3 (use run_ios_unittest MCP tool!)',
                'DO NOT use run_in_terminal with autoninja (use compile_ios_unittest MCP tool!)',
                'DO NOT try other unrelated operations',
                'DO NOT give up or stop'
            ],
            'REQUIRED_NEXT_STEPS': [
                '1. Fix test failures in test file',
                f'2. Call compile_ios_unittest for {source_file_path or "source_file"}',
                f'3. Call run_ios_unittest with filter "{test_filter}"'
            ],
            'passed': passed_tests,
            'failed': failed_tests,
            'test_filter': test_filter,
            'workflow_state': 'BLOCKED_ON_TEST_FAILURES',
            'retry_commands': [
                f'compile_ios_unittest({{"source_file": "{source_file_path or "source_file"}"}})',
                f'run_ios_unittest({{"test_filter": "{test_filter}", "test_file_path": "{test_file_path or "test_file"}"}})'
            ]
        }, indent=2)
        
    except subprocess.TimeoutExpired:
        return json.dumps({
            'status': 'error',
            'error': 'Test execution timed out (10 minutes)'
        })
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': f'Failed to run tests: {str(e)}',
            'traceback': traceback.format_exc()
        })


# ============================================================================
# Fix Runtime Test Errors (NEW!)
# ============================================================================

@mcp.tool(name='analyze_runtime_errors', structured_output=False)
def analyze_error_patterns(test_output: str, failed_count: int) -> dict:
    """Analyze test output for common error patterns to enable batch fixes.
    
    Args:
        test_output: Complete test execution output
        failed_count: Number of failed tests
        
    Returns:
        Dictionary with batch fix guidance
    """
    import re
    
    patterns = {
        'expected_vs_actual': [],
        'null_pointer': [],
        'method_not_found': [],
        'assertion_failure': [],
        'setup_issue': [],
        'other': []
    }
    
    # Extract all failed test names and their error messages
    failed_blocks = re.findall(r'\[ RUN      \]\s+(\S+)(.*?)\[  FAILED  \]', test_output, re.DOTALL)
    
    for test_name, error_block in failed_blocks:
        # Pattern detection
        if 'Expected:' in error_block and 'Actual:' in error_block:
            patterns['expected_vs_actual'].append(test_name)
        elif 'null' in error_block.lower() or 'nil' in error_block.lower():
            patterns['null_pointer'].append(test_name)
        elif 'selector' in error_block.lower() or 'method' in error_block.lower():
            patterns['method_not_found'].append(test_name)
        elif 'EXPECT_' in error_block or 'ASSERT_' in error_block:
            patterns['assertion_failure'].append(test_name)
        elif 'SetUp' in error_block or 'TearDown' in error_block:
            patterns['setup_issue'].append(test_name)
        else:
            patterns['other'].append(test_name)
    
    # Generate batch guidance
    guidance_parts = []
    has_patterns = False
    
    if len(patterns['expected_vs_actual']) > 1:
        has_patterns = True
        tests = ', '.join(patterns['expected_vs_actual'][:5])
        guidance_parts.append(f"""
[REPORT] GROUP 1: Expected vs Actual mismatches ({len(patterns['expected_vs_actual'])} tests)
   Tests: {tests}{'...' if len(patterns['expected_vs_actual']) > 5 else ''}
   
   Common Fix: Check histogram buckets, enum values, or return values
   # -> Fix ALL these tests together in one edit
   # -> They likely share same root cause
""")
    
    if len(patterns['null_pointer']) > 1:
        has_patterns = True
        tests = ', '.join(patterns['null_pointer'][:5])
        guidance_parts.append(f"""
[REPORT] GROUP 2: Null/Nil pointer issues ({len(patterns['null_pointer'])} tests)
   Tests: {tests}{'...' if len(patterns['null_pointer']) > 5 else ''}
   
   Common Fix: Initialize objects in SetUp(), check lifecycle
   # -> Fix ALL null pointer issues in one batch
   # -> Add proper object initialization
""")
    
    if len(patterns['setup_issue']) > 1:
        has_patterns = True
        tests = ', '.join(patterns['setup_issue'][:5])
        guidance_parts.append(f"""
[REPORT] GROUP 3: Test setup/teardown issues ({len(patterns['setup_issue'])} tests)
   Tests: {tests}{'...' if len(patterns['setup_issue']) > 5 else ''}
   
   Common Fix: Fix SetUp() or TearDown() in test fixture
   # -> One fix in SetUp() resolves ALL these tests
   # -> This is the highest priority group!
""")
    
    if not has_patterns and failed_count > 2:
        guidance_parts.append(f"""
[REPORT] Multiple failures detected ({failed_count} tests)
   
   Strategy: Look for common themes in error messages
   # -> Fix similar errors together
   # -> Use multi_replace_string_in_file for batch edits
""")
    
    batch_guidance = '\n'.join(guidance_parts) if guidance_parts else "No common patterns detected"
    
    return {
        'has_common_patterns': has_patterns or failed_count > 2,
        'batch_guidance': batch_guidance,
        'pattern_counts': {k: len(v) for k, v in patterns.items() if v}
    }


def analyze_runtime_errors(
    test_file_path: str,
    test_output: str,
    source_file_path: str = None
) -> str:
    """Analyze runtime test errors and provide COMPLETE error context to Copilot.
    
    This tool directly passes the full test output to Copilot for analysis and fixing.
    No predefined error patterns - Copilot analyzes and fixes ALL types of errors.
    
    Args:
        test_file_path: Path to the test file (relative to Chromium src root)
        test_output: Complete console output from test execution
        source_file_path: Optional path to the source file being tested
        
    Returns:
        Complete error context for Copilot to analyze and fix
    """
    import json
    import re
    import sys
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"[SEARCH] RUNTIME ERROR ANALYSIS: {test_file_path}\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    try:
        src_root = get_chromium_src_root()
        test_path = src_root / test_file_path
        
        if not test_path.exists():
            return json.dumps({
                'status': 'error',
                'tool': 'analyze_runtime_errors',
                'error': f'Test file not found: {test_file_path}'
            })
        
        # Extract test statistics
        passed_match = re.search(r'\[\s+PASSED\s+\]\s+(\d+)\s+test', test_output)
        failed_match = re.search(r'\[\s+FAILED\s+\]\s+(\d+)\s+test', test_output)
        
        passed_count = int(passed_match.group(1)) if passed_match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0
        
        # Check if tests actually failed or crashed
        has_crash = (
            'Check failed:' in test_output or
            'Segmentation fault' in test_output or
            'ERROR: Test runner did not complete' in test_output or
            'Assuming crash' in test_output or
            'SIGABRT' in test_output or
            'SIGSEGV' in test_output
        )
        
        has_failures = (
            failed_count > 0 or 
            'FAILED' in test_output or 
            'Assertion' in test_output or
            has_crash
        )
        
        if not has_failures:
            sys.stderr.write("[OK] All tests passed successfully!\n\n")
            sys.stderr.flush()
            return json.dumps({
                'status': 'success',
                'tool': 'analyze_runtime_errors',
                'message': f'[OK] All {passed_count} tests passed!',
                'test_file': test_file_path,
                'passed': passed_count
            }, indent=2)
        
        # Tests failed or crashed - provide COMPLETE context to Copilot
        crash_section = ""
        if has_crash:
            sys.stderr.write(f"[!] CRASH detected in test output!\n")
            sys.stderr.write(f"   Passed before crash: {passed_count}\n")
            sys.stderr.write(f"   This is likely a test setup/teardown issue\n")
            sys.stderr.write(f"   Extracting crash backtrace...\n\n")
            
            # Extract crash section with backtrace
            crash_markers = ['Check failed:', 'SIGABRT', 'SIGSEGV', 'Segmentation fault', 'Assuming crash']
            crash_start = -1
            crash_marker_found = ""
            for marker in crash_markers:
                pos = test_output.rfind(marker)
                if pos > crash_start:
                    crash_start = pos
                    crash_marker_found = marker
            
            if crash_start > 0:
                # Include 1000 chars before crash for context
                crash_context_start = max(0, crash_start - 1000)
                crash_section = test_output[crash_context_start:]
                sys.stderr.write(f"   [OK] Found crash marker: {crash_marker_found}\n")
                sys.stderr.write(f"   [OK] Extracted {len(crash_section)} chars of crash context\n\n")
            else:
                crash_section = test_output[-3000:]  # Last 3000 chars as fallback
                sys.stderr.write(f"   [OK] Using last 3000 chars as crash context\n\n")
            sys.stderr.flush()
        else:
            sys.stderr.write(f"[FAIL] Test failures detected: {failed_count} failed, {passed_count} passed\n")
            sys.stderr.write(f"   Extracting failure details...\n\n")
        
        # Extract failed test details (for both crash and normal failures)
        failed_tests_section = ""
        if not has_crash and failed_count > 0:
            # Extract each failed test with its error details
            failed_test_pattern = r'\[ RUN\s+\]\s+([\w\.]+).*?\[\s+FAILED\s+\]\s+\1'
            failed_matches = list(re.finditer(failed_test_pattern, test_output, re.DOTALL))
            
            if failed_matches:
                sys.stderr.write(f"   [OK] Found {len(failed_matches)} failed test(s) with details\n")
                failed_tests_details = []
                
                for match in failed_matches:
                    test_name = match.group(1)
                    test_full_output = match.group(0)
                    
                    # Extract assertion failures
                    assertions = re.findall(r'(.*?:\d+:.*?(?:Failure|Expected|EXPECT_|ASSERT_).*?)$', 
                                          test_full_output, re.MULTILINE)
                    
                    failed_tests_details.append(f"""
{'─'*80}
[FAIL] FAILED TEST: {test_name}
{'─'*80}
{test_full_output}
""")
                
                failed_tests_section = f"""
{'='*80}
[FAIL][FAIL][FAIL] FAILED TEST DETAILS WITH STACK TRACES [FAIL][FAIL][FAIL]
{'='*80}

Found {len(failed_matches)} failed test(s). Each failure includes:
- Test name
- Failure location (file:line)
- Expected vs actual values
- Complete assertion stack trace

{''.join(failed_tests_details)}

{'='*80}
# [!]️  CRITICAL: These are TEST FAILURES, not crashes!
   - Look for assertion failures (EXPECT_EQ, EXPECT_NE, etc.)
   - Compare expected vs actual values
   - Check test logic and mock setup
   - Verify test expectations match actual behavior
{'='*80}
"""
                sys.stderr.write(f"   [OK] Extracted {sum(len(d) for d in failed_tests_details)} chars of failure details\n\n")
            else:
                sys.stderr.write(f"   [!]️  Could not parse individual test failures (using full output)\n\n")
            
            sys.stderr.flush()
        
        # Create comprehensive prompt for Copilot with FULL context
        error_type = "CRASH" if has_crash else "FAILURES"
        
        # Build crash section separately to avoid nested f-string issues
        crash_details = ""
        if has_crash:
            crash_details = f"""{'='*80}
[CRASH] [CRASH] [CRASH] CRASH BACKTRACE AND ERROR DETAILS [CRASH] [CRASH] [CRASH]
{'='*80}

The test CRASHED during execution. Here is the crash backtrace and error details:

{crash_section}

{'='*80}
[CRITICAL] This is a CRASH, not a normal test failure!
   - Look for assertion failures (Check failed:)
   - Look for null pointer dereferences
   - Look for memory access violations
   - Check setUp/tearDown methods
   - Check object initialization
{'='*80}

"""
        
        source_file_line = f"[DIR] Source File: {source_file_path}" if source_file_path else ""
        crash_warning = "[CRASH] CRASH DETECTED: Tests crashed during execution!" if has_crash else ""
        
        copilot_prompt = f"""
{'='*80}
[!] COPILOT: RUNTIME TEST {error_type} - FIX REQUIRED
{'='*80}

[DIR] Test File: {test_file_path}
{source_file_line}

[REPORT] Test Results:
   [OK] PASSED: {passed_count} tests
   [FAIL] FAILED: {failed_count} tests
   {crash_warning}

{crash_details}{failed_tests_section}
{'='*80}
[INFO] COMPLETE TEST OUTPUT (for reference):
{'='*80}
{test_output}

{'='*80}
[TARGET] YOUR TASK - MANDATORY REQUIREMENTS:
{'='*80}

**YOU MUST:**

1. **Analyze the COMPLETE test output above**
   - Identify ALL failing tests
   - Understand the root cause of EACH failure
   - Read the test file: {test_file_path}
   {'- Read the source file: ' + source_file_path if source_file_path else ''}

2. **Fix ALL failures with PROPER implementations**
   - Implement correct test logic
   - Add necessary mocks, stubs, or fakes
   - Set up proper test fixtures
   - Handle all edge cases

3. **CRITICAL CONSTRAINTS:**
   [SKIP] ABSOLUTELY FORBIDDEN:
      [FAIL] Using DISABLED_ prefix to skip tests
      [FAIL] Deleting failing tests
      [FAIL] Commenting out failing tests completely
      [FAIL] Making tests pass by removing functionality
   
   [OK] ALLOWED:
      # [OK]️ Add TODO for genuinely complex/uncertain implementations
      # [OK]️ Keep test skeleton with TODO explanation
      # [OK]️ Format: // TODO: [Reason] - needs domain knowledge
   
   [OK] MANDATORY:
      # [OK]️ Preserve ALL test cases (even if adding TODO)
      # [OK]️ Implement tests to best of your ability
      # [OK]️ All assertions MUST be meaningful and correct
      # [OK]️ All mocks/fakes MUST be properly set up
      # [OK]️ Add CONFIDENCE_SCORE at end of file (0-100)

4. **After fixing:**
   - Compile: autoninja -C out/Debug-iphonesimulator <target>
   - Run: run_ios_unittest with test_filter
   - Verify ALL tests pass
   - If any test still fails, repeat the fix process

{'='*80}
[TIP] COMMON FIXES (examples only - analyze the actual errors):
{'='*80}

{'[!] CRASH-SPECIFIC ANALYSIS (PRIORITY):' if has_crash else ''}
{'''
• Test crashes during/after execution:
  # -> Check test DESTRUCTOR (~ClassName()) for proper cleanup
  # -> Ensure objects are released in correct order
  # -> Example: Release agents before releasing scene_state
  # -> Example: Set pointers to nil before destroying parent objects
  # -> Look for stack trace pointing to dealloc/destructor
  
• FakeSceneState / Scene lifecycle crashes:
  # -> In destructor: [profile_state_ removeAgent:agent_]
  # -> Then: agent_ = nil; scene_state_ = nil;
  # -> Then: browser_.reset(); profile_state_.profile = nullptr;
  # -> Order matters: clean up children before parents!
  
• Object already deallocated:
  # -> Check for strong reference cycles
  # -> Ensure proper retain/release in setUp/tearDown
  # -> Use weak pointers where appropriate
''' if has_crash else ''}

• CommandDispatcher crashes:
  # -> Create mock handlers conforming to required protocols
  # -> Register handlers in test setUp

• Assertion failures:
  # -> Verify expected vs actual values
  # -> Fix test expectations or implementation logic

• Memory errors / crashes:
  # -> Check object lifecycle
  # -> Ensure proper initialization
  # -> Add null checks

• Method not found:
  # -> Implement required methods
  # -> Check method signatures

**IMPORTANT: Don't just apply these generic fixes - analyze the ACTUAL errors 
in the test output above and implement the CORRECT solution!**

{'='*80}
"""
        
        # Intelligent batch analysis - group similar errors
        batch_analysis = analyze_error_patterns(test_output, failed_count)
        
        # Add batch fix guidance to the prompt
        if batch_analysis['has_common_patterns']:
            copilot_prompt += f"""
{'='*80}
[FAST] BATCH FIX OPTIMIZATION - REDUCE COMPILATIONS
{'='*80}

[TARGET] DETECTED COMMON ERROR PATTERNS - FIX ALL AT ONCE:

{batch_analysis['batch_guidance']}

[TIP] STRATEGY:
   1. Fix ALL tests with similar errors in ONE edit session
   2. Use multi_replace_string_in_file for multiple fixes
   3. Compile ONCE after all fixes
   4. This reduces iterations from {failed_count} to 1-2

# [!]️  DO NOT fix tests one-by-one and recompile each time!
    Group similar fixes together!

{'='*80}
"""
        
        # Print COMPLETE output to stderr for visibility and debugging
        sys.stderr.write(copilot_prompt)
        sys.stderr.flush()
        
        # Extract key failure details for return value
        # For multiple test failures, include ALL failure details (not just first)
        failure_summary = ""
        if failed_count > 0:
            # Extract failed test names and key error messages
            # Match both summary line "[  FAILED  ] TestName" and individual "[  FAILED  ] TestName (10 ms)"
            failed_tests = re.findall(r'\[  FAILED  \]\s+(\S+)', test_output)
            
            # Remove duplicates and filter out summary line (which doesn't have test name with .)
            unique_failed_tests = []
            seen = set()
            for test_name in failed_tests:
                if '.' in test_name and test_name not in seen:
                    unique_failed_tests.append(test_name)
                    seen.add(test_name)
            
            failure_summary = f"Failed tests ({len(unique_failed_tests)}): {', '.join(unique_failed_tests[:20])}"
            
            # For test failures, we want ALL failure details (similar to crash handling)
            # Extract each failed test's complete output
            all_failures = []
            for test_name in unique_failed_tests[:10]:  # Limit to first 10 failures to avoid huge output
                # Find this test's full output: from [RUN] to [FAILED]
                # Note: Match exact format with specific whitespace
                # Format: "[ RUN      ] TestName" ... "[  FAILED  ] TestName (Xms)"
                pattern = rf'\[ RUN\s+\]\s+{re.escape(test_name)}.*?\[  FAILED  \]\s+{re.escape(test_name)}'
                test_match = re.search(pattern, test_output, re.DOTALL)
                if test_match:
                    test_detail = test_match.group(0)
                    # Include up to 3000 chars per test (enough for stack trace)
                    all_failures.append(f"\n{'='*70}\n{test_name}\n{'='*70}\n{test_detail[:3000]}")
            
            if all_failures:
                # Include first 10 test failures in detail (up to 30000 chars total)
                failure_summary += "\n\nDetailed failure output (first 10 tests):\n"
                failure_summary += "\n".join(all_failures)
            elif failed_count > 0:
                # Fallback: if regex didn't match, use simpler extraction
                # Get all output between first [RUN] and last [FAILED]
                first_run = test_output.find('[ RUN      ]')
                last_failed = test_output.rfind('[  FAILED  ]')
                if first_run >= 0 and last_failed > first_run:
                    failure_section = test_output[first_run:last_failed + 200]
                    # Limit to 20000 chars to avoid huge output
                    failure_summary += f"\n\nAll test failures:\n{failure_section[:20000]}"
        
        elif has_crash:
            # Extract crash details - for crashes, we want MORE context
            crash_idx = max(
                test_output.find('Check failed:'),
                test_output.find('Segmentation fault'),
                test_output.find('SIGABRT'),
                test_output.find('SIGSEGV'),
                test_output.find('Assuming crash'),
                0
            )
            if crash_idx > 0:
                # For crash, extract MUCH more context (up to 10000 chars to include full backtrace)
                crash_context_start = max(0, crash_idx - 1000)  # Include 1000 chars before crash
                crash_end = min(len(test_output), crash_idx + 10000)  # Up to 10000 chars after
                failure_summary = f"Crash details (full backtrace):\n{test_output[crash_context_start:crash_end]}"
            else:
                # No clear crash marker, use last 5000 chars (likely contains crash info)
                failure_summary = f"Crash detected (last 5000 chars of output):\n{test_output[-5000:]}"
        
        # Return FULL details for both crashes and test failures
        # (Both are critical and need complete error context)
        details_included = "FULL CRASH DETAILS INCLUDED BELOW" if has_crash else "DETAILED FAILURE OUTPUT INCLUDED BELOW"
        summary_label = "Complete Crash Details:" if has_crash else "Complete Failure Details:"
        critical_note = "[!] CRITICAL: The COMPLETE crash backtrace is shown above!\n    Analyze the stack trace to identify the exact crash location." if has_crash else "[!] CRITICAL: DETAILED failure output for first 10 tests is shown above!\n    Each test's failure includes assertions, error messages, and context."
        
        # IMPORTANT: Return in simple format that can be easily parsed
        # Format: text summary + "\n\n" + JSON
        analysis_text = f"""
{'='*80}
# [!] TEST {error_type} - {details_included}
{'='*80}

[REPORT] Summary:
   [OK] PASSED: {passed_count} tests
   [FAIL] FAILED: {failed_count} tests
   {'[!] CRASH: Yes - Complete backtrace included below' if has_crash else ''}

[INFO] {summary_label}
{failure_summary}

{'='*80}
{critical_note}
{'='*80}
"""
        
        return analysis_text + "\n\n" + json.dumps({
            'status': 'tests_failed_need_fix',
            'tool': 'analyze_runtime_errors',
            'test_file': test_file_path,
            'has_crash': has_crash,
            'source_file': source_file_path,
            'passed': passed_count,
            'failed': failed_count,
            'failure_details': failure_summary,  # Include complete failure details in JSON (crash or test failures)
            'COPILOT_INSTRUCTIONS': [
                '[!] CRITICAL: COMPLETE ERROR DETAILS ARE SHOWN ABOVE IN THE RESPONSE',
                '',
                'STEP 1: Read the ' + ('CRASH BACKTRACE above to identify exact crash location' if has_crash else "DETAILED FAILURE OUTPUT above - each test's error is included"),
                'STEP 2: ' + ('Analyze stack trace - look for test destructor, object dealloc, or setup issues' if has_crash else 'For EACH failed test, analyze: assertions, error messages, expected vs actual values'),
                'STEP 3: Implement PROPER fixes for EVERY failure',
                '        - NO DISABLED_ prefix',
                '        - NO deleting tests',
                '        - NO placeholder TODOs',
                '        - Create proper mocks and test setup',
                f'STEP 4: Use compile_ios_unittest for {test_file_path}',
                f'STEP 5: Use run_ios_unittest with test_filter',
                'STEP 6: If ANY test fails, repeat from STEP 2',
                '',
                '[!]️ DO NOT STOP until ALL tests pass!',
                '[!]️ You MUST continue the fix-compile-run loop!'
            ]
        }, indent=2)
    
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'tool': 'analyze_runtime_errors',
            'error': f'Failed to analyze: {str(e)}',
            'traceback': traceback.format_exc()
        })


@mcp.tool(name='analyze_compilation_errors', structured_output=False)
def analyze_compilation_errors(
    test_file_path: str,
    compilation_output: str = None
) -> str:
    """Analyze compilation errors and provide COMPLETE error context to Copilot.
    
    This tool directly passes the full compilation output to Copilot for analysis and fixing.
    No predefined error patterns - Copilot analyzes and fixes ALL types of compilation errors.
    
    Args:
        test_file_path: Path to the test file (relative to Chromium src root)
        compilation_output: Complete compilation error output
        
    Returns:
        Complete error context for Copilot to analyze and fix
    """
    import json
    import re
    import sys
    
    sys.stderr.write(f"\n{'='*80}\n")
    sys.stderr.write(f"[SEARCH] COMPILATION ERROR ANALYSIS: {test_file_path}\n")
    sys.stderr.write(f"{'='*80}\n\n")
    sys.stderr.flush()
    
    try:
        src_root = get_chromium_src_root()
        file_path = src_root / test_file_path
        
        if not file_path.exists():
            return json.dumps({
                'status': 'error',
                'tool': 'analyze_compilation_errors',
                'error': f'Test file not found: {test_file_path}'
            })
        
        if not compilation_output:
            return json.dumps({
                'status': 'error',
                'tool': 'analyze_compilation_errors',
                'error': 'No compilation output provided'
            })
        
        # Extract error count from compilation output
        error_count_match = re.search(r'(\d+) error(?:s)? generated', compilation_output)
        error_count = int(error_count_match.group(1)) if error_count_match else 0
        
        # Check if compilation actually failed
        has_errors = (error_count > 0 or 
                     'error:' in compilation_output or
                     'fatal error:' in compilation_output or
                     'undefined' in compilation_output.lower())
        
        if not has_errors:
            sys.stderr.write("[OK] No compilation errors detected!\n\n")
            sys.stderr.flush()
            return json.dumps({
                'status': 'success',
                'tool': 'analyze_compilation_errors',
                'message': '[OK] Compilation successful!',
                'test_file': test_file_path,
                'next_action': 'PROCEED_TO_RUN_TESTS'
            }, indent=2)
        
        # Compilation failed - provide COMPLETE context to Copilot
        sys.stderr.write(f"[FAIL] Compilation errors detected: {error_count} error(s)\n\n")
        
        # ============================================================================
        # P0 ENHANCEMENT: Intelligent Error Analysis
        # ============================================================================
        sys.stderr.write("[BOT] Analyzing error patterns...\n")
        
        # Parse specific error types
        missing_headers = re.findall(r"'([^']+\\.h)' file not found", compilation_output)
        undefined_symbols = re.findall(r"Undefined symbols.*?\\\"(.+?)\\\"", compilation_output, re.DOTALL)
        type_errors = re.findall(r"cannot convert.*?'(.+?)'.*?to.*?'(.+?)'", compilation_output)
        method_not_found = re.findall(r"no known (?:instance|class) method for selector '(.+?)'", compilation_output)
        
        sys.stderr.write(f"  - Missing headers: {len(missing_headers)}\n")
        sys.stderr.write(f"  - Undefined symbols: {len(undefined_symbols)}\n")
        sys.stderr.write(f"  - Type errors: {len(type_errors)}\n")
        sys.stderr.write(f"  - Method not found: {len(method_not_found)}\n")
        
        # Batch fix opportunity analysis
        batch_opportunities = 0
        if len(missing_headers) > 1:
            batch_opportunities += 1
            sys.stderr.write(f"\n[FAST] BATCH FIX OPPORTUNITY: {len(missing_headers)} missing headers can be fixed in ONE edit!\n")
        if len(method_not_found) > 1:
            batch_opportunities += 1
            sys.stderr.write(f"[FAST] BATCH FIX OPPORTUNITY: {len(method_not_found)} method errors may share same root cause!\n")
        
        if batch_opportunities > 0:
            sys.stderr.write(f"\n[TIP] Use multi_replace_string_in_file to fix all similar errors at once!\n")
            sys.stderr.write(f"   This will reduce compilations from {error_count} to {1 + (error_count // 5)}!\n")
        
        # P1 ENHANCEMENT: Auto-search similar test files for API reference
        sys.stderr.write("\n[SEARCH] Searching for similar test files...\n")
        test_dir = str(Path(test_file_path).parent)
        similar_tests = []
        try:
            src_test_dir = src_root / test_dir
            if src_test_dir.exists():
                # Find other *_unittest.mm files in same directory
                for test_file in src_test_dir.glob('*_unittest.mm'):
                    if test_file.name != Path(test_file_path).name:
                        similar_tests.append(str(test_file.relative_to(src_root)))
                        if len(similar_tests) >= 3:  # Limit to 3 examples
                            break
            sys.stderr.write(f"  Found {len(similar_tests)} similar test(s) for reference\n")
            for ref_test in similar_tests:
                sys.stderr.write(f"    - {ref_test}\n")
        except Exception as e:
            sys.stderr.write(f"  Warning: Could not search similar tests: {e}\n")
        
        sys.stderr.flush()
        
        # CRITICAL: Check test file integrity before providing fix guidance
        sys.stderr.write("\n[SEARCH] Checking test file integrity...\n")
        with open(file_path, 'r') as f:
            test_content = f.read()
        
        # Count tests and check for shortcuts
        test_count = test_content.count('TEST_F')
        has_disabled = 'DISABLED_' in test_content
        has_todo = 'TODO' in test_content
        has_placeholder = 'EXPECT_TRUE(true)' in test_content or 'EXPECT_FALSE(false)' in test_content
        
        integrity_warnings = []
        if has_disabled:
            integrity_warnings.append('[!] FORBIDDEN: DISABLED_ prefix found!')
        if has_todo:
            integrity_warnings.append('[!] FORBIDDEN: TODO comments found!')
        if has_placeholder:
            integrity_warnings.append('[!] FORBIDDEN: Placeholder assertions found!')
        if test_count < 5:
            integrity_warnings.append(f'[!]️  WARNING: Only {test_count} tests (may have deleted tests!)')
        
        if integrity_warnings:
            sys.stderr.write("\n" + "="*80 + "\n")
            sys.stderr.write("[!][!][!] TEST INTEGRITY VIOLATIONS DETECTED [!][!][!]\n")
            sys.stderr.write("="*80 + "\n")
            for warning in integrity_warnings:
                sys.stderr.write(f"{warning}\n")
            sys.stderr.write("="*80 + "\n\n")
            sys.stderr.write("COPILOT: You MUST fix these violations!\n")
            sys.stderr.write("- Remove all DISABLED_ prefixes\n")
            sys.stderr.write("- Remove all TODO comments\n")
            sys.stderr.write("- Replace placeholder assertions with real ones\n")
            sys.stderr.write("- Restore any deleted tests\n\n")
        
        sys.stderr.flush()
        
        # ============================================================================
        # CRITICAL: Extract precise code context to prevent misplaced insertions
        # ============================================================================
        sys.stderr.write("\n[SEARCH] Extracting precise code context from test file...\n")
        
        with open(file_path, 'r') as f:
            test_file_lines = f.readlines()
        
        # Find import section (first 50 lines typically contain imports)
        import_section_end = 0
        last_import_line = ""
        for i, line in enumerate(test_file_lines[:100]):
            if '#import' in line or '#include' in line:
                import_section_end = i
                last_import_line = line.rstrip()
        
        # Extract context around imports (5 lines before last import, 3 lines after)
        import_context_start = max(0, import_section_end - 5)
        import_context_end = min(len(test_file_lines), import_section_end + 4)
        import_context = ''.join(test_file_lines[import_context_start:import_context_end])
        
        # Find class declaration or test fixture
        class_declaration_line = ""
        class_line_num = 0
        for i, line in enumerate(test_file_lines):
            if '@interface' in line or 'class ' in line and 'Test' in line:
                class_declaration_line = line.rstrip()
                class_line_num = i
                break
        
        # Find setUp method for context
        setup_context = ""
        setup_line_num = 0
        in_setup = False
        setup_lines = []
        for i, line in enumerate(test_file_lines):
            if '- (void)setUp' in line or 'void setUp()' in line:
                in_setup = True
                setup_line_num = i
                setup_lines.append(line.rstrip())
            elif in_setup:
                setup_lines.append(line.rstrip())
                if line.strip() == '}':
                    in_setup = False
                    break
        if setup_lines:
            setup_context = '\n'.join(setup_lines)
        
        sys.stderr.write(f"  [OK] Import section ends at line {import_section_end + 1}\n")
        sys.stderr.write(f"  [OK] Class declared at line {class_line_num + 1}\n")
        sys.stderr.write(f"  [OK] setUp method at line {setup_line_num + 1}\n")
        sys.stderr.flush()
        
        # Create comprehensive prompt for Copilot with FULL context
        copilot_prompt = f"""
{'='*80}
# [!][!][!] STOP - READ THIS BEFORE YOU PROCEED [!][!][!]
{'='*80}

BEFORE YOU THINK "LET ME SIMPLIFY" OR "LET ME DELETE TESTS":

[FAIL] You are NOT allowed to:
   - Delete any tests
   - Use DISABLED_ prefix to skip tests
   - Comment out tests completely

[OK] You ARE allowed to:
   - Add TODO comments for complex implementations
   - Keep test skeleton with TODO explanation
   - Mark uncertain tests with // TODO: [Reason]

[OK] You MUST:
   - Keep ALL test cases (even if adding TODO)
   - Create proper mocks (MockEdgeRewardsService, etc.)
   - Fix the ACTUAL compilation errors
   - Implement tests to best of your ability
   - Add CONFIDENCE_SCORE at end of file (0-100)

IF YOU ARE UNCERTAIN: ADD TODO AND KEEP THE TEST SKELETON!

{'='*80}
# [!] COPILOT: COMPILATION FAILED - FIX REQUIRED
{'='*80}

{('[!]️  TEST INTEGRITY VIOLATIONS:' + chr(10) + chr(10).join(integrity_warnings) + chr(10)) if integrity_warnings else ''}
{'='*80}

[DIR] Test File: {test_file_path}

{'[REPORT] Error Count: ' + str(error_count) + ' errors' if error_count > 0 else ''}

{'='*80}
[INFO] COMPLETE COMPILATION OUTPUT:
{'='*80}
{compilation_output}

{'='*80}
[TARGET] YOUR TASK - MANDATORY REQUIREMENTS:
{'='*80}

**YOU MUST:**

1. **Analyze ALL {error_count} compilation errors systematically**
   - Read the COMPLETE compilation output above
   - Group errors by type (missing headers, undefined symbols, type mismatches, etc.)
   - Read the test file: {test_file_path}
   - Identify patterns (same error repeated multiple times)

2. **Fix errors in BATCHES using multi_replace_string_in_file**
   - [LAUNCH] **CRITICAL**: Use multi_replace_string_in_file for efficiency!
   - Fix ALL similar errors in ONE operation (e.g., all missing #import in one call)
   - Don't fix errors one by one - batch them by type
   
   **CONCRETE EXAMPLE - Copy this pattern:**
   ```python
   # If you see these errors:
   # - 'FooConsumer.h' file not found
   # - 'BarDelegate.h' file not found  
   # - 'BazService.h' file not found
   
   # DO THIS (multi_replace_string_in_file with 3 replacements):
   [
     {{
       "filePath": "ios/chrome/app/profile/test.mm",
       "oldString": "#import \\"ios/chrome/app/profile/test.h\\"",
       "newString": "#import \\"ios/chrome/app/profile/test.h\\"\\n#import \\"ios/chrome/browser/ui/foo/foo_consumer.h\\"\\n#import \\"ios/chrome/browser/ui/bar/bar_delegate.h\\"\\n#import \\"ios/chrome/browser/ui/baz/baz_service.h\\""
     }}
   ]
   
   # DON'T DO THIS (3 separate replace_string_in_file calls):
   # Call 1: Add FooConsumer.h
   # Call 2: Add BarDelegate.h  
   # Call 3: Add BazService.h
   # [FAIL] This causes 3 compilations instead of 1!
   ```

3. **Prioritize fixes by type (most impactful first)**
   
   **Priority 1: Missing headers (fix these FIRST)**
   - Add ALL missing #import statements in ONE multi_replace_string_in_file call
   - Example: If you see 5 "file not found" errors, add all 5 imports together
   - This will resolve the most errors in one compilation
   
   # [!] **CRITICAL: Use PRECISE context to avoid code insertion at wrong location!**
   
   **CURRENT IMPORT SECTION (Last import at line {import_section_end + 1}):**
   ```
{import_context}
   ```
   
   **When adding missing #import statements, you MUST:**
   1. Find the EXACT last #import line shown above
   2. Include 3-5 lines BEFORE and AFTER in your oldString
   3. Insert new imports AFTER the last existing import
   4. Keep all existing imports unchanged
   
   **CORRECT Example (add missing imports):**
   ```python
   {{
     "filePath": "{test_file_path}",
     "explanation": "Add missing header imports after existing imports",
     "oldString": "{chr(10).join(test_file_lines[max(0, import_section_end - 2):import_section_end + 1]).rstrip()}",
     "newString": "{chr(10).join(test_file_lines[max(0, import_section_end - 2):import_section_end + 1]).rstrip()}\\n#import \\"path/to/missing_header1.h\\"\\n#import \\"path/to/missing_header2.h\\""
   }}
   ```
   
   **WRONG Examples (will insert at file top!):**
   [FAIL] oldString doesn't match exactly (missing whitespace, wrong quotes)
   [FAIL] oldString is too short (only 1 line, not enough context)
   [FAIL] oldString has typos or uses "...existing code..." placeholders
   [FAIL] Inserting at wrong location (before Copyright, before #import block)
   
   **Priority 2: Undefined symbols / linking errors**
   - Add missing BUILD.gn dependencies
   - These often block multiple tests
   
   **Priority 3: Type mismatches and method signature errors**
   - Fix incorrect types
   - Fix method calls
   
   **Priority 4: Other errors**
   - Template errors, syntax errors, etc.

3. **CRITICAL CONSTRAINTS - READ THIS CAREFULLY:**
   
   # [!][!][!] ABSOLUTELY FORBIDDEN - STOP IF YOU ARE CONSIDERING THESE [!][!][!]
   
   [FAIL] FORBIDDEN #1: Using DISABLED_ prefix to skip tests
      # -> If you think: "Let me use DISABLED_" -> STOP! Create the mock instead.
   
   [FAIL] FORBIDDEN #2: Deleting or commenting out tests
      # -> If you think: "Let me remove this test" -> STOP! Fix the error instead.
   
   [FAIL] FORBIDDEN #3: Simplifying tests to avoid mocking
      # -> If you think: "Let me simplify by not mocking" -> STOP! Create the mock.
      # -> If you think: "This is too complex" -> STOP! That's what mocks are for.
      # -> If you think: "Just test simpler methods" -> STOP! Test ALL methods.
   
   [FAIL] FORBIDDEN #4: Leaving broken code with TODO comments
      # -> If you think: "I'll add TODO for now" -> STOP! Implement it properly.
   
   [FAIL] FORBIDDEN #5: Placeholder assertions
      # -> EXPECT_TRUE(true), EXPECT_FALSE(false) -> NOT ALLOWED!
   
   [OK][OK][OK] MANDATORY REQUIREMENTS - YOU MUST DO THESE [OK][OK][OK]
   
   # [OK]️ REQUIRED #1: Fix the ROOT CAUSE of every error
      # -> Missing header? Add #import
      # -> Type mismatch? Fix the type
      # -> Undefined symbol? Add dependency or create mock
   
   # [OK]️ REQUIRED #2: Create proper mocks for complex dependencies
      # -> EdgeRewardsService? Create MockEdgeRewardsService
      # -> Browser? Use TestBrowser from test utilities
      # -> ProfileIOS? Use TestProfileIOS
   
   # [OK]️ REQUIRED #3: Maintain ALL tests - ZERO deletions allowed
      # -> You started with N tests? You must end with N tests.
      # -> Count before: X tests. Count after: must still be X tests.
   
   # [OK]️ REQUIRED #4: Every test must be fully implemented
      # -> No TODO comments
      # -> No DISABLED_ prefix
      # -> 3+ meaningful assertions per test
   
   # [!]️  IF YOU ARE THINKING OF SIMPLIFYING: You are about to violate the constraints!
   # [!]️  IF YOU ARE THINKING OF DELETING: You are about to violate the constraints!
   # [!]️  IF YOU ARE THINKING THIS IS TOO HARD: Create the mock - that's the solution!

4. **After fixing each batch:**
   - Use compile_ios_unittest to recompile
   - If still errors, analyze and fix the next batch
   - Continue until compilation succeeds

{'='*80}
[TIP] HOW TO REDUCE COMPILATION CYCLES (from 10+ to 2-3):
{'='*80}

**Bad approach (10+ compilations):**
[FAIL] Fix 1 #import -> compile -> fix another #import -> compile -> ...
[FAIL] Fix errors one by one sequentially
[FAIL] Don't batch similar fixes together

**Good approach (2-3 compilations):**
[OK] Batch 1: Add ALL 5-10 missing #import in ONE multi_replace call
[OK] Compile -> reveals 3 linking errors
[OK] Batch 2: Add ALL 3 BUILD.gn deps together
[OK] Compile -> reveals 2 type errors
[OK] Batch 3: Fix both type errors together
[OK] Compile -> [OK] Success!

**Key principle: Fix ALL errors of the same type TOGETHER**

{'='*80}
[TARGET] SPECIFIC ERRORS DETECTED IN THIS COMPILATION:
{'='*80}

{('📦 Missing Headers (' + str(len(missing_headers)) + '):' + chr(10) + chr(10).join(['   - ' + h for h in missing_headers[:10]]) + chr(10) + chr(10) + '   [OK] ACTION: Add ALL these imports in ONE multi_replace_string_in_file call' + chr(10)) if missing_headers else ''}
{('🔗 Undefined Symbols (' + str(len(undefined_symbols)) + '):' + chr(10) + chr(10).join(['   - ' + s[:80] for s in undefined_symbols[:5]]) + chr(10) + chr(10) + '   [OK] ACTION: Add BUILD.gn dependencies or create mocks' + chr(10)) if undefined_symbols else ''}
{('[!]️  Type Mismatches (' + str(len(type_errors)) + '):' + chr(10) + chr(10).join(['   - Cannot convert "' + e[0][:40] + '" to "' + e[1][:40] + '"' for e in type_errors[:5]]) + chr(10) + chr(10) + '   [OK] ACTION: Fix type declarations or add proper casts' + chr(10)) if type_errors else ''}
{('❓ Method Not Found (' + str(len(method_not_found)) + '):' + chr(10) + chr(10).join(['   - ' + m for m in method_not_found[:5]]) + chr(10) + chr(10) + '   [OK] ACTION: Check API documentation, use correct method signatures' + chr(10)) if method_not_found else ''}
{('📚 Reference Similar Tests for API Patterns:' + chr(10) + chr(10).join(['   - ' + t for t in similar_tests]) + chr(10) + chr(10) + '   [OK] ACTION: Read these files to learn correct API usage' + chr(10)) if similar_tests else ''}

{'='*80}
[TIP] GENERIC ERROR PATTERNS TO BATCH FIX:
{'='*80}

• Missing headers (PRIORITY 1 - fix ALL together):
  Pattern: "'FooBar.h' file not found"
  Solution: Add #import for ALL missing headers in ONE operation
  
  # [!] **MANDATORY: Use the exact import context provided above!**
  
  **Step-by-step process:**
  1. Copy the "CURRENT IMPORT SECTION" shown above
  2. Identify the last #import line: "{last_import_line}"
  3. Use replace_string_in_file with:
     - oldString: Last 3-5 import lines (exact copy from above)
     - newString: Same lines + new imports appended after
  4. DO NOT insert before Copyright header
  5. DO NOT insert in middle of existing imports
  6. DO NOT use "...existing code..." placeholders in oldString
  
  Example batch:
    #import "ios/chrome/browser/ui/foo/foo.h"
    #import "ios/chrome/browser/ui/bar/bar.h"
    #import "ios/chrome/test/fakes/fake_scene_state.h"
    (Add 5-10 imports in one multi_replace_string_in_file call)

• Undefined symbols (PRIORITY 2 - fix ALL together):
  Pattern: "Undefined symbols: _OBJC_CLASS_$_FooBar"
  Solution: Add BUILD.gn deps for ALL missing symbols together
  Example: deps = ["//ios/chrome/browser/ui/foo:test_support", ...]

• Type mismatches (PRIORITY 3):
  Pattern: "Cannot convert 'Foo*' to 'Bar*'"
  Solution: Fix ALL type errors in one batch
  
  # [!] **CRITICAL: Find the EXACT line with the error!**
  
  **Step-by-step process:**
  1. Search for the exact line causing the error in {test_file_path}
  2. Read 5-10 lines AROUND that line for context
  3. Use replace_string_in_file with:
     - oldString: 5-10 lines including the error line (exact copy)
     - newString: Same lines with type fixed
  4. DO NOT use generic "fix the type" - show EXACT before/after code
  5. DO NOT insert code at random locations

• setValue:forKey: or readonly property errors:
  Pattern: "property is declared readonly" or "no setter method"
  
  # [!] **CRITICAL: These fixes MUST be inserted in setUp method, NOT at file top!**
  
  **CURRENT setUp METHOD (at line {setup_line_num + 1}):**
  ```
{setup_context}
  ```
  
  **Step-by-step process:**
  1. Find the EXACT location in setUp where you need to add the workaround
  2. Typically AFTER creating the object, BEFORE first use
  3. Use replace_string_in_file with:
     - oldString: 5-10 lines from setUp method (exact copy from above)
     - newString: Same lines + setValue:forKey: call inserted at right spot
  4. Example: Insert after "agent_ = [[IdentityConfirmationProfileAgent alloc] init];"
  5. DO NOT insert at file top or in wrong method!
  
  **CORRECT Example (add setValue in setUp):**
  ```python
  {{
    "filePath": "{test_file_path}",
    "explanation": "Use KVC to set readonly property in setUp",
    "oldString": "  agent_ = [[MyAgent alloc] initWithProfileState:profile_state_];\\n  [profile_state_ addAgent:agent_];\\n}}",
    "newString": "  agent_ = [[MyAgent alloc] initWithProfileState:profile_state_];\\n  [profile_state_ setValue:scene_state_ forKey:@\\"foregroundActiveScene\\"];\\n  [profile_state_ addAgent:agent_];\\n}}"
  }}
  ```

• Private method calls:
  # -> Only test public API
  # -> Remove calls to private/internal methods
  # -> Use public interfaces instead

• Missing headers:
  # -> Add #import "path/to/header.h"
  # -> Add dependencies in BUILD.gn if needed

• Type mismatches:
  # -> Use correct types (id vs specific class)
  # -> Add proper casts if necessary
  # -> Fix method signatures

• Template errors:
  # -> Check template parameter types
  # -> Ensure template instantiation is valid

• Linking errors (undefined symbols):
  # -> These are NOT "environment issues" - they are missing dependencies!
  # -> Add missing dependencies to BUILD.gn deps = [...]
  # -> Check if test needs additional libraries or frameworks
  # -> Search for where the symbol is defined and add that dep
  # -> Example: "Undefined symbols: _DisableFeedbackLogger"
    # -> Add dependency providing this symbol
  # -> DO NOT declare success if linking fails!

**IMPORTANT: Don't just apply generic fixes - analyze the ACTUAL compilation 
errors in the output above and implement the CORRECT solution for each!**

[SKIP] FORBIDDEN EXCUSES:
   [FAIL] "These are environment-specific issues" (when linking fails)
   [FAIL] "These are known issues in the iOS test infrastructure"
   [FAIL] "The compilation validates code quality" (without running tests)
   [FAIL] Declaring success when tests haven't actually run
   
[OK] ACTUAL SUCCESS CRITERIA:
   # [OK]️ Code compiles without errors
   # [OK]️ Code links without errors
   # [OK]️ Tests execute and run
   # [OK]️ Tests pass (green)

{'='*80}
"""
        
        # Print to stderr for Copilot visibility
        sys.stderr.write(copilot_prompt)
        sys.stderr.flush()
        
        # Return COMPLETE prompt as the main result so Copilot sees it
        return copilot_prompt + "\n\n" + json.dumps({
            'status': 'compilation_failed_need_fix',
            'tool': 'analyze_compilation_errors',
            'test_file': test_file_path,
            'error_count': error_count,
            'parsed_errors': {
                'missing_headers': missing_headers[:10],
                'undefined_symbols': [s[:100] for s in undefined_symbols[:5]],
                'type_errors': [[e[0][:50], e[1][:50]] for e in type_errors[:5]],
                'method_not_found': method_not_found[:5]
            },
            'similar_tests': similar_tests,
            'COPILOT_INSTRUCTIONS': [
                '[!] CRITICAL: YOU MUST FIX ALL COMPILATION ERRORS NOW',
                '',
                f'STEP 1: Read the test file: {test_file_path}',
                f'STEP 2: Analyze ALL {error_count} compilation error(s) above',
                'STEP 3: Fix EVERY error properly:',
                '        - Add missing #import statements',
                '        - Fix type mismatches',
                '        - Remove calls to private methods',
                '        - Add BUILD.gn dependencies if needed',
                '        - NO DISABLED_ prefix',
                '        - NO deleting tests',
                f'STEP 4: Use compile_ios_unittest for {test_file_path}',
                'STEP 5: If compilation fails, repeat from STEP 2',
                'STEP 6: After compilation succeeds, use run_ios_unittest',
                '',
                '[!]️ DO NOT STOP until compilation succeeds!',
                '[!]️ You MUST continue the fix-compile loop!'
            ]
        }, indent=2)
        
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'tool': 'analyze_compilation_errors',
            'error': f'Failed to analyze: {str(e)}',
            'traceback': traceback.format_exc()
        })


# ============================================================================
# OPTIMIZATION 5: AI-ENHANCED MODE IMPROVEMENTS
# ============================================================================

def generate_intelligent_test_for_method(
    method: Dict,
    context: Dict,
    existing_patterns: Dict = None
) -> str:
    """Generate intelligent test case for a specific method using heuristics.
    
    Args:
        method: Method information (name, signature, return_type)
        context: Test generation context (class_name, pattern_type, etc.)
        existing_patterns: Optional patterns from similar tests
        
    Returns:
        Generated test case code
    """
    method_name = method.get('name', '')
    method_lower = method_name.lower()
    signature = method.get('full_signature', method_name)
    return_type = method.get('return_type', 'id')
    has_params = ':' in signature
    
    class_name = context['class_name']
    fixture_name = f"{class_name}Test"
    obj_ref = context.get('object_reference', 'test_object_')
    pattern_info = context.get('pattern_info', {})
    
    # Generate test name
    test_name = ''.join(word.capitalize() for word in method_name.split(':')[0].split('_'))
    
    test_code = f"TEST_F({fixture_name}, {test_name}) {{\n"
    
    # Generate minimal test stub - let Copilot implement based on pattern template
    if 'start' in method_lower:
        test_code += f"  // TODO: Test that start initializes the {class_name} properly\n"
        test_code += f"  // Reference pattern template for proper implementation\n"
        test_code += f"  [{obj_ref} {method_name}];\n"
        test_code += f"  EXPECT_NE({obj_ref}, nil);\n"
            
    elif 'stop' in method_lower:
        test_code += f"  // TODO: Test that stop cleans up resources properly\n"
        test_code += f"  // Reference pattern template for proper implementation\n"
        test_code += f"  [{obj_ref} {method_name}];\n"
        test_code += f"  EXPECT_NE({obj_ref}, nil);\n"
            
    elif return_type != 'void' and return_type != 'id' and not has_params:
        # Getter method with specific return type
        test_code += f"  // Test getter returns consistent value\n"
        test_code += f"  {return_type} result1 = [{obj_ref} {method_name}];\n"
        test_code += f"  {return_type} result2 = [{obj_ref} {method_name}];\n"
        test_code += f"  \n"
        test_code += f"  // Getter should be consistent\n"
        test_code += f"  EXPECT_EQ(result1, result2);\n"
        
    elif 'update' in method_lower or 'refresh' in method_lower or 'reload' in method_lower:
        test_code += f"  // Test update operation is idempotent\n"
        test_code += f"  [{obj_ref} {method_name}];\n"
        test_code += f"  [{obj_ref} {method_name}];\n"
        test_code += f"  \n"
        test_code += f"  // Multiple calls should not cause issues\n"
        test_code += f"  EXPECT_NE({obj_ref}, nil);\n"
        
    elif has_params:
        test_code += f"  // Test method with parameters\n"
        test_code += f"  // TODO: Create appropriate parameter values\n"
        test_code += f"  // [{obj_ref} {signature}];\n"
        test_code += f"  EXPECT_NE({obj_ref}, nil);\n"
        
    else:
        # Default pattern
        test_code += f"  // Test {method_name} method\n"
        test_code += f"  [{obj_ref} {method_name}];\n"
        test_code += f"  EXPECT_NE({obj_ref}, nil);\n"
    
    test_code += "}\n\n"
    return test_code


def generate_intelligent_tests_batch(
    methods: List[Dict],
    context: Dict,
    existing_patterns: Dict = None
) -> str:
    """Generate multiple intelligent test cases.
    
    Args:
        methods: List of methods to generate tests for
        context: Test generation context
        existing_patterns: Optional patterns from similar tests
        
    Returns:
        Combined test cases code
    """
    all_tests = []
    
    for method in methods:
        test_code = generate_intelligent_test_for_method(method, context, existing_patterns)
        all_tests.append(test_code)
    
    return ''.join(all_tests)


# ============================================================================
# OPTIMIZATION 6: INCREMENTAL TEST UPDATE
# ============================================================================

def analyze_existing_test_file(test_file_path: str) -> Dict:
    """Analyze existing test file to understand current coverage.
    
    Args:
        test_file_path: Path to existing test file
        
    Returns:
        Dictionary with:
        - test_cases: List of existing test case names
        - tested_methods: Set of methods already tested
        - test_fixture: Name of test fixture class
        - has_setup: Whether SetUp method exists
        - has_teardown: Whether TearDown method exists
    """
    try:
        src_root = get_chromium_src_root()
        full_path = src_root / test_file_path
        
        if not full_path.exists():
            return {
                'exists': False,
                'test_cases': [],
                'tested_methods': set(),
                'test_fixture': None
            }
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract test fixture name
        fixture_match = re.search(r'class\s+(\w+Test)\s*:\s*public', content)
        test_fixture = fixture_match.group(1) if fixture_match else None
        
        # Extract all test case names
        test_cases = re.findall(r'TEST_F\([^,]+,\s*(\w+)\)', content)
        
        # Try to infer tested methods from test names and test content
        tested_methods = set()
        
        # Pattern 1: From test names (e.g., TestStartMethod -> start)
        for test_name in test_cases:
            # Remove "Test" prefix if exists
            method_part = test_name.replace('Test', '', 1) if test_name.startswith('Test') else test_name
            # Convert PascalCase to snake_case
            snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', method_part).lower()
            tested_methods.add(snake_case)
        
        # Pattern 2: From actual method calls in test content
        method_calls = re.findall(r'\[[\w_]+\s+([\w:]+)\]', content)
        for call in method_calls:
            # Get the base method name (before first colon)
            base_method = call.split(':')[0]
            tested_methods.add(base_method)
        
        # Check for SetUp/TearDown
        has_setup = 'void SetUp()' in content or 'SetUp() override' in content
        has_teardown = 'void TearDown()' in content or 'TearDown() override' in content
        
        return {
            'exists': True,
            'test_cases': test_cases,
            'tested_methods': tested_methods,
            'test_fixture': test_fixture,
            'has_setup': has_setup,
            'has_teardown': has_teardown,
            'content': content
        }
        
    except Exception as e:
        return {
            'exists': False,
            'error': str(e),
            'test_cases': [],
            'tested_methods': set()
        }


def identify_missing_tests(
    source_file_path: str,
    existing_test_analysis: Dict
) -> Dict:
    """Identify which methods need tests.
    
    Args:
        source_file_path: Path to source file
        existing_test_analysis: Analysis of existing test file
        
    Returns:
        Dictionary with missing test information
    """
    # Analyze source file
    source_content = read_file_content(source_file_path)
    header_path = source_file_path.replace('.mm', '.h').replace('.cc', '.h')
    
    try:
        header_content = read_file_content(header_path)
    except:
        header_content = None
    
    testable = extract_testable_interfaces(source_content, header_content)
    
    # Get all methods from source
    all_methods = set(testable.get('methods', []))
    
    # Get already tested methods
    tested_methods = existing_test_analysis.get('tested_methods', set())
    
    # Find missing
    missing_methods = all_methods - tested_methods
    
    # Get method details for missing methods
    method_details = testable.get('method_details', {})
    missing_method_info = []
    
    for method in missing_methods:
        if method in method_details:
            missing_method_info.append({
                'name': method,
                'full_signature': method_details[method].get('full_signature', method),
                'return_type': method_details[method].get('return_type', 'id')
            })
    
    return {
        'missing_methods': list(missing_methods),
        'missing_method_info': missing_method_info,
        'total_methods': len(all_methods),
        'tested_methods': len(tested_methods),
        'coverage_percentage': (len(tested_methods) / len(all_methods) * 100) if all_methods else 0
    }


@mcp.tool(name='update_existing_tests', structured_output=False)
def update_existing_tests(source_file_path: str) -> str:
    """Update existing test file by adding missing test cases.
    
    This tool performs incremental test updates:
    - Analyzes existing test file
    - Identifies untested methods
    - Generates only missing test cases
    - Appends to existing file without disrupting current tests
    
    Args:
        source_file_path: Path to the iOS source file (relative to Chromium src root)
        
    Returns:
        JSON string containing:
        - existing_test_count: Number of existing tests
        - missing_methods: List of methods without tests
        - new_tests_generated: Number of new tests added
        - updated_file: Path to updated test file
        - coverage_before: Coverage percentage before update
        - coverage_after: Coverage percentage after update
    """
    import json
    import sys
    
    sys.stderr.write(f"\\n{'='*80}\\n")
    sys.stderr.write(f"INCREMENTAL TEST UPDATE: {source_file_path}\\n")
    sys.stderr.write(f"{'='*80}\\n\\n")
    sys.stderr.flush()
    
    if not is_ios_source_file(source_file_path):
        return json.dumps({
            'error': f'Not an iOS source file: {source_file_path}'
        })
    
    try:
        # Step 1: Find test file
        test_file_path = calculate_test_file_path(source_file_path)
        
        # Step 2: Analyze existing test file
        sys.stderr.write("Step 1/4: Analyzing existing test file...\\n")
        existing_analysis = analyze_existing_test_file(test_file_path)
        
        if not existing_analysis['exists']:
            return json.dumps({
                'error': 'No existing test file found. Use generate_ios_unittest_file instead.',
                'test_file_path': test_file_path,
                'suggestion': 'Run: generate_ios_unittest_file'
            })
        
        sys.stderr.write(f"  Found {len(existing_analysis['test_cases'])} existing test cases\\n")
        
        # Step 3: Identify missing tests
        sys.stderr.write("Step 2/4: Identifying missing tests...\\n")
        missing_info = identify_missing_tests(source_file_path, existing_analysis)
        
        sys.stderr.write(f"  Total methods: {missing_info['total_methods']}\\n")
        sys.stderr.write(f"  Tested methods: {missing_info['tested_methods']}\\n")
        sys.stderr.write(f"  Missing tests: {len(missing_info['missing_methods'])}\\n")
        sys.stderr.write(f"  Current coverage: {missing_info['coverage_percentage']:.1f}%\\n")
        
        # Check if this is an incomplete/skeleton test file
        src_root = get_chromium_src_root()
        test_file_full_path = src_root / test_file_path
        with open(test_file_full_path, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        is_incomplete = False
        incomplete_reasons = []
        
        # Check for auto-generation markers
        if 'COPILOT ENHANCEMENT INSTRUCTIONS' in test_content or '[BOT]' in test_content:
            is_incomplete = True
            incomplete_reasons.append("Contains auto-generation instructions header")
        
        # Check for TODO comments in test bodies
        if 'TODO:' in test_content or '// TODO' in test_content:
            is_incomplete = True
            incomplete_reasons.append("Contains TODO comments in tests")
        
        # Check for placeholder assertions
        if 'EXPECT_TRUE(true)' in test_content and 'Implement' in test_content:
            is_incomplete = True
            incomplete_reasons.append("Contains placeholder assertions (EXPECT_TRUE(true))")
        
        # Check if all tests are just stubs
        stub_patterns = [
            r'EXPECT_TRUE\(true\)\s*<<\s*"Implement',
            r'//\s*auto result = .* parameters',
            r'//\s*EXPECT_EQ\(expected, result\)'
        ]
        stub_count = sum(len(re.findall(pattern, test_content)) for pattern in stub_patterns)
        if stub_count >= len(existing_analysis['test_cases']) * 0.5:  # 50% or more are stubs
            is_incomplete = True
            incomplete_reasons.append(f"Most tests ({stub_count}/{len(existing_analysis['test_cases'])}) are stubs")
        
        sys.stderr.write(f"  Incomplete test file check: {is_incomplete}\\n")
        if is_incomplete:
            sys.stderr.write(f"  Reasons: {incomplete_reasons}\\n")
        sys.stderr.flush()
        
        # If incomplete, skip to Phase 2 (return TODO list for Copilot)
        if is_incomplete:
            sys.stderr.write(f"  [FIX] Detected incomplete/skeleton test file\\n")
            sys.stderr.write(f"     Skipping update_existing_tests, will return TODO list for Copilot\\n")
            sys.stderr.write(f"     Reasons: {', '.join(incomplete_reasons)}\\n")
            sys.stderr.flush()
            
            # Return Phase 2 directly - let Copilot handle enhancement
            return f"""
{'='*80}
# [!]️  TEST FILE EXISTS BUT INCOMPLETE
{'='*80}

[DIR] Test file: {test_file_path}
[REPORT] Coverage: {coverage_pct}%
# [!]️  Status: Skeleton/incomplete test file detected

[SEARCH] Detection reasons:
{chr(10).join(['   - ' + r for r in incomplete_reasons])}

{'='*80}
[TARGET] RECOMMENDED WORKFLOW (Manual Enhancement)
{'='*80}

Since the test file is incomplete (has TODOs, placeholders, etc.),
YOU (Copilot) should manually enhance it:

Step 1: Read the test file
   # -> Use read_file to see current state

Step 2: Read the source file  
   # -> Understand what needs to be tested

Step 3: Enhance test implementations
   # -> Use replace_string_in_file to:
     • Remove TODO comments
     • Replace EXPECT_TRUE(true) with real assertions
     • Add proper test data and mocks
     • Implement test logic

Step 4: Update BUILD file
   # -> Use update_build_file_for_test MCP tool

Step 5: Compile
   # -> Use compile_ios_unittest MCP tool

Step 6: Run tests
   # -> Use run_ios_unittest MCP tool

[SKIP] DO NOT call update_existing_tests (not needed for incomplete files)
[SKIP] DO NOT call full_test_workflow again

{'='*80}
"""
        
        if not missing_info['missing_methods'] and not is_incomplete:
            return json.dumps({
                'status': 'complete',
                'message': 'All methods already have tests!',
                'coverage': missing_info['coverage_percentage'],
                'existing_test_count': len(existing_analysis['test_cases'])
            })
        
        # Step 4: Generate tests for missing methods
        sys.stderr.write("Step 3/4: Generating new test cases...\\n")
        
        # Prepare context for intelligent generation
        source_content = read_file_content(source_file_path)
        header_content = None
        try:
            header_path = source_file_path.replace('.mm', '.h')
            header_content = read_file_content(header_path)
        except:
            pass
        
        testable = extract_testable_interfaces(source_content, header_content)
        
        # Determine class name
        if testable['implementations']:
            class_name = testable['implementations'][0]
        elif testable['interfaces']:
            class_name = testable['interfaces'][0]
        else:
            class_name = 'Unknown'
        
        # Detect pattern using pattern database (replaces hardcoded logic)
        pattern_info = detect_test_pattern_with_examples(source_file_path, source_content, testable)
        pattern_name = pattern_info.get('pattern_id', 'simple_class_pattern')
        
        context = {
            'class_name': class_name,
            'pattern_name': pattern_name,
            'pattern_info': pattern_info
        }
        
        # Generate new tests
        try:
            new_tests = generate_intelligent_tests_batch(
                missing_info['missing_method_info'],
                context
            )
            sys.stderr.write(f"  [OK] Generated {len(missing_info['missing_methods'])} new test cases\\n")
            sys.stderr.write(f"  Generated content length: {len(new_tests)} chars\\n")
        except Exception as e:
            sys.stderr.write(f"  [FAIL] Error generating tests: {e}\\n")
            sys.stderr.flush()
            return json.dumps({
                'error': f'Failed to generate tests: {str(e)}',
                'missing_methods': missing_info['missing_methods']
            })
        
        # Step 5: Append to existing file
        sys.stderr.write("Step 4/4: Updating test file...\\n")
        
        # src_root already defined above
        full_path = src_root / test_file_path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Find the last test case and insert new tests before the final closing brace
        # This preserves the existing structure
        insertion_point = existing_content.rfind('}\\n\\n')
        if insertion_point == -1:
            insertion_point = existing_content.rfind('\\n}')
        
        if insertion_point != -1:
            updated_content = (
                existing_content[:insertion_point] +
                '\\n' + new_tests +
                existing_content[insertion_point:]
            )
        else:
            # Fallback: just append
            updated_content = existing_content + '\\n' + new_tests
        
        # Write updated file
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            sys.stderr.write(f"  [OK] File written successfully\\n")
        except Exception as e:
            sys.stderr.write(f"  [FAIL] Error writing file: {e}\\n")
            sys.stderr.flush()
            return json.dumps({
                'error': f'Failed to write file: {str(e)}',
                'test_file': test_file_path
            })
        
        # Calculate new coverage
        new_test_count = len(existing_analysis['test_cases']) + len(missing_info['missing_methods'])
        coverage_after = (new_test_count / missing_info['total_methods'] * 100) if missing_info['total_methods'] > 0 else 100
        
        sys.stderr.write(f"\\n[OK] Updated test file: {test_file_path}\\n")
        sys.stderr.write(f"  Added {len(missing_info['missing_methods'])} new test cases\\n")
        sys.stderr.write(f"  Coverage: {missing_info['coverage_percentage']:.1f}% -> {coverage_after:.1f}%\\n\\n")
        sys.stderr.flush()
        
        return json.dumps({
            'status': 'success',
            'test_file': test_file_path,
            'existing_test_count': len(existing_analysis['test_cases']),
            'new_tests_generated': len(missing_info['missing_methods']),
            'missing_methods': missing_info['missing_methods'],
            'coverage_before': missing_info['coverage_percentage'],
            'coverage_after': coverage_after,
            'next_steps': [
                'Compile tests: compile_ios_unittest',
                'Run tests: run_ios_unittest'
            ]
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'traceback': str(e)
        })


# ============================================================================
# P0 OPTIMIZATION: NEW TOOLS FOR AUTOMATION
# ============================================================================

@mcp.tool(name='update_build_file_for_test', structured_output=False)
def update_build_file_for_test(
    test_file_path: str,
    auto_apply: bool = True
) -> str:
    """[!][!][!] MANDATORY MCP TOOL - NEVER MANUALLY EDIT BUILD FILES [!][!][!]
    
    [STOP] BEFORE YOU THINK "LET ME EDIT BUILD.gn" - STOP!
    
    [FAIL][FAIL][FAIL] ABSOLUTELY FORBIDDEN [FAIL][FAIL][FAIL]
       - Manually editing BUILD.gn or BUILD_edge.gni
       - Using replace_string_in_file on BUILD files
       - Using run_in_terminal to edit BUILD files
       - If you are considering these, you are making a MISTAKE!
    
    [OK][OK][OK] YOU MUST USE THIS MCP TOOL [OK][OK][OK]
       - This is the ONLY correct way to update BUILD files
       - Do NOT look for alternatives
       - Do NOT try to manually edit
    
    [TARGET] P0 Optimization: Eliminates manual BUILD file editing errors.
    
    This tool automatically:
    1. Detects if test is Edge-specific (BUILD_edge.gni) or Core (BUILD.gn)
    2. Finds the correct BUILD file in the test's directory
    3. Parses existing test targets and dependencies
    4. **FOR COMPONENTS**: Checks if linked to ios_chrome_unittests
    5. **AUTO-LINKS**: Adds "//components/xxx/ios:unit_tests" to parent BUILD
    6. Inserts new test in alphabetical order
    7. Applies changes automatically (if auto_apply=True)
    
    [FAST] Benefits:
       [OK] Zero manual editing - fully automated
       [OK] Automatically links component tests to main test target
       [OK] Always correct format and indentation
       [OK] Alphabetical ordering maintained
       [OK] No typos or syntax errors
    
    Args:
        test_file_path: Path to the test file (relative to Chromium src root)
                       Example: "ios/chrome/browser/ui/main/my_feature_unittest.mm"
        auto_apply: If True, automatically apply changes; if False, return preview only
        
    Returns:
        JSON string containing:
        - build_file_path: Path to the BUILD file
        - changes_preview: Preview of changes to be made
        - auto_applied: Whether changes were applied
        - insertion_point: Where the test was inserted
        - status: 'success' or 'error'
    """
    import json
    import re
    from pathlib import Path
    
    try:
        # ========================================================================
        # AUTO-CLEAN: Remove DELETE_SECTION markers before updating BUILD
        # ========================================================================
        sys.stderr.write(f"\n{'='*80}\n")
        sys.stderr.write(f"[CLEAN] Pre-check: Cleaning DELETE sections from test file\n")
        sys.stderr.write(f"{'='*80}\n\n")
        sys.stderr.flush()
        
        clean_result = clean_delete_sections_from_test_file(test_file_path)
        
        if clean_result.get('cleaned'):
            sys.stderr.write(f"[OK] Removed {len(clean_result['sections_removed'])} DELETE section(s)\n")
            sys.stderr.write(f"    Sections: {', '.join(clean_result['sections_removed'])}\n")
            sys.stderr.write(f"    Lines removed: {clean_result.get('lines_removed', 0)}\n\n")
        elif 'error' not in clean_result:
            sys.stderr.write("[OK] No DELETE sections found (file already clean)\n\n")
        else:
            sys.stderr.write(f"[!]️  Note: Could not clean DELETE sections: {clean_result.get('error')}\n")
            sys.stderr.write("    Continuing with BUILD file update...\n\n")
        
        sys.stderr.flush()
        
        # Determine if this is an Edge-specific test using the same logic as generation
        # Strip _unittest.mm to get source file path for proper detection
        source_file_path = test_file_path.replace('_unittest.mm', '.mm').replace('_unittest.m', '.m')
        is_edge = is_edge_file(source_file_path)
        
        # Detect test target
        test_target = detect_test_target(source_file_path)
        
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"UPDATE BUILD FILE FOR TEST\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"Test file: {test_file_path}\n")
        sys.stderr.write(f"Source file (derived): {source_file_path}\n")
        sys.stderr.write(f"Test target: {test_target}\n")
        sys.stderr.write(f"Edge-specific: {'Yes' if is_edge else 'No'}\n")
        sys.stderr.write(f"Detection details:\n")
        base_name = os.path.basename(source_file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        sys.stderr.write(f"  - Basename: {base_name}\n")
        sys.stderr.write(f"  - Name without ext: {name_without_ext}\n")
        sys.stderr.write(f"  - Starts with 'edge_': {name_without_ext.startswith('edge_')}\n")
        sys.stderr.write(f"  - Ends with '_edge': {name_without_ext.endswith('_edge')}\n")
        sys.stderr.flush()
        
        # Special handling for component-level tests (e.g., components/edge_hybrid/ios/ or ios/components/edge_gec/)
        normalized_path = test_file_path.replace('\\', '/')
        if normalized_path.startswith('components/') or normalized_path.startswith('ios/components/'):
            sys.stderr.write(f"\n[FIX] Component-level test detected\n")
            sys.stderr.write(f"   Looking for component BUILD.gn...\n")
            
            # Find component's BUILD.gn
            test_dir = Path(test_file_path).parent
            src_root = get_chromium_src_root()
            build_file_path = src_root / test_dir / 'BUILD.gn'
            
            if not build_file_path.exists():
                sys.stderr.write(f"[FAIL] No BUILD.gn found at {test_dir}/BUILD.gn\n")
                sys.stderr.write(f"   Components must have their own BUILD.gn file\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'error',
                    'error': f'Component BUILD.gn not found at {test_dir}/BUILD.gn. '
                            f'Component tests must be defined in their own BUILD.gn file. '
                            f'Please create one or ensure the test is in the correct location.'
                })
            
            sys.stderr.write(f"[OK] Found BUILD.gn: {test_dir}/BUILD.gn\n")
            sys.stderr.write(f"   Test target: {test_target}\n")
            sys.stderr.write(f"   This BUILD.gn should define the {test_target} target\n")
            sys.stderr.write(f"   and be referenced from higher-level BUILD files\n\n")
            sys.stderr.flush()
            
            # Read and check BUILD.gn
            with open(build_file_path, 'r') as f:
                content = f.read()
            
            test_basename = Path(test_file_path).name
            test_in_build = test_basename in content or '"*_unittest.mm"' in content or "'*_unittest.mm'" in content
            
            # Always check parent BUILD linkage, regardless of whether test is in component BUILD
            if test_in_build:
                sys.stderr.write(f"[OK] Test file {test_basename} in component BUILD.gn\n")
            else:
                sys.stderr.write(f"[!]️  Test file {test_basename} NOT in component BUILD.gn\n")
                sys.stderr.write(f"   You should add it or use wildcard '*_unittest.mm'\n")
            
            # Check if this component's unit_tests is referenced in parent BUILD files
            sys.stderr.write(f"\n[SEARCH] Checking if component tests are linked to main test target...\n")
            
            component_target_path = f"//{test_dir}:unit_tests"
            parent_build_checked = False
            parent_build_file = None
            
            # Determine which parent BUILD file to check based on component location
            if normalized_path.startswith('components/'):
                # Check if it's an Edge-specific component
                parts = normalized_path.split('/')
                component_name = parts[1] if len(parts) > 1 else ''
                
                if is_edge or component_name.startswith('edge_'):
                    # Edge-specific components go to components/BUILD_edge.gni
                    parent_build_file = src_root / 'components' / 'BUILD_edge.gni'
                    sys.stderr.write(f"[INFO] Edge component (components/{component_name}) -> checking components/BUILD_edge.gni\n")
                else:
                    # Regular components go to components/BUILD.gn
                    parent_build_file = src_root / 'components' / 'BUILD.gn'
                    sys.stderr.write(f"[INFO] Component path detected -> checking components/BUILD.gn\n")
            elif normalized_path.startswith('ios/components/'):
                # For ios/components/* -> check ios/components/BUILD.gn
                parent_build_file = src_root / 'ios' / 'components' / 'BUILD.gn'
                sys.stderr.write(f"[INFO] iOS components path detected -> checking ios/components/BUILD.gn\n")
            else:
                # For ios/chrome/* -> check ios/chrome/test/BUILD.gn or BUILD_edge.gni
                if is_edge:
                    parent_build_file = src_root / 'ios' / 'chrome' / 'test' / 'BUILD_edge.gni'
                    sys.stderr.write(f"[INFO] iOS Chrome Edge path detected -> checking ios/chrome/test/BUILD_edge.gni\n")
                else:
                    parent_build_file = src_root / 'ios' / 'chrome' / 'test' / 'BUILD.gn'
                    sys.stderr.write(f"[INFO] iOS Chrome path detected -> checking ios/chrome/test/BUILD.gn\n")
            
            # Check the determined parent BUILD file
            if parent_build_file and parent_build_file.exists():
                try:
                    parent_content = parent_build_file.read_text()
                    if component_target_path in parent_content:
                        sys.stderr.write(f"[OK] Found in {parent_build_file.relative_to(src_root)}\n")
                        parent_build_checked = True
                    else:
                        sys.stderr.write(f"[!]️  NOT found in {parent_build_file.relative_to(src_root)}\n")
                except Exception as e:
                    sys.stderr.write(f"[!]️  Error checking {parent_build_file.relative_to(src_root)}: {e}\n")
            else:
                sys.stderr.write(f"[!]️  Parent BUILD file not found: {parent_build_file}\n")
            
            sys.stderr.flush()
            
            # If already linked to parent, check if local BUILD.gn defines unit_tests target
            if parent_build_checked:
                sys.stderr.write(f"\n[OK] Parent BUILD already has reference to {component_target_path}\n")
                sys.stderr.write(f"[SEARCH] Now checking if local BUILD.gn defines 'unit_tests' target...\n")
                sys.stderr.flush()
                
                # Check if local BUILD.gn has ios_unit_test target definition
                has_unit_tests_target = False
                if 'ios_unit_test(' in content or 'test(' in content:
                    # Check if there's a target named "unit_tests"
                    import re
                    target_pattern = r'(ios_unit_test|test)\s*\(\s*["\']unit_tests["\']'
                    if re.search(target_pattern, content):
                        has_unit_tests_target = True
                        sys.stderr.write(f"[OK] Found 'unit_tests' target definition in BUILD.gn\n")
                    else:
                        sys.stderr.write(f"[!]️  No 'unit_tests' target found in BUILD.gn\n")
                        sys.stderr.write(f"   BUILD.gn has test() but no target named 'unit_tests'\n")
                else:
                    sys.stderr.write(f"[!]️  No test target definition found in BUILD.gn\n")
                
                sys.stderr.flush()
                
                if not has_unit_tests_target:
                    return json.dumps({
                        'status': 'error',
                        'build_file_path': str(test_dir / 'BUILD.gn'),
                        'test_target': test_target,
                        'component_target': component_target_path,
                        'message': f'Parent BUILD references {component_target_path} but local BUILD.gn does not define unit_tests target',
                        'action_required': f'Add ios_unit_test("unit_tests") target in {test_dir}/BUILD.gn with sources including {test_basename}',
                        'parent_linked': True
                    })
                
                if not test_in_build:
                    # Test file NOT in BUILD.gn - try to add it automatically
                    sys.stderr.write(f"\n[!]️  Test file not in BUILD.gn sources, attempting to add it...\n")
                    sys.stderr.write(f"   Parent BUILD has reference: [OK]\n")
                    sys.stderr.write(f"   Local BUILD has unit_tests target: [OK]\n")
                    sys.stderr.write(f"   Test file in sources: [FAIL] -> Fixing...\n")
                    sys.stderr.flush()
                    
                    # Try to add test file to sources array in unit_tests target
                    if auto_apply:
                        # Find sources array in unit_tests target
                        unit_tests_pattern = r'(ios_unit_test\s*\(\s*"unit_tests"\s*\)\s*\{[^}]*?sources\s*=\s*\[)(.*?)(\])'
                        match = re.search(unit_tests_pattern, content, re.DOTALL)
                        
                        if match:
                            prefix = match.group(1)
                            sources_content = match.group(2)
                            suffix = match.group(3)
                            
                            # Parse existing sources
                            sources_lines = sources_content.split('\n')
                            sources_entries = []
                            for line in sources_lines:
                                stripped = line.strip()
                                if stripped and (stripped.startswith('"') or stripped.startswith("'")):
                                    sources_entries.append(stripped)
                            
                            # Check if already exists (shouldn't happen but be safe)
                            new_entry = f'"{test_basename}",'
                            if new_entry.strip() not in ' '.join(sources_entries):
                                # Add in alphabetical order
                                insertion_idx = len(sources_entries)
                                for i, entry in enumerate(sources_entries):
                                    if entry > new_entry:
                                        insertion_idx = i
                                        break
                                    insertion_idx = i + 1
                                
                                sources_entries.insert(insertion_idx, new_entry)
                                
                                # Reconstruct sources array
                                new_sources_lines = []
                                for entry in sources_entries:
                                    new_sources_lines.append(f'    {entry}')
                                
                                new_sources_content = '\n' + '\n'.join(new_sources_lines) + '\n  '
                                
                                # Replace in content
                                new_content = content[:match.start(2)] + new_sources_content + content[match.end(2):]
                                
                                # Write back
                                with open(build_file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                
                                sys.stderr.write(f"[OK] Successfully added {test_basename} to sources\n")
                                sys.stderr.flush()
                                
                                return json.dumps({
                                    'status': 'success',
                                    'build_file_path': str(test_dir / 'BUILD.gn'),
                                    'test_target': test_target,
                                    'test_file': test_basename,
                                    'message': f'[OK] Added test file to BUILD.gn sources',
                                    'action_taken': f'Added "{test_basename}" to unit_tests sources array',
                                    'parent_linked': True
                                })
                        
                        # If we couldn't find the pattern, return error
                        sys.stderr.write(f"[FAIL] Could not find sources array in unit_tests target\n")
                        sys.stderr.flush()
                    
                    return json.dumps({
                        'status': 'error',
                        'build_file_path': str(test_dir / 'BUILD.gn'),
                        'test_target': test_target,
                        'test_file': test_basename,
                        'message': f'[FAIL] Test file NOT in BUILD.gn sources and could not auto-add',
                        'action_required': f'Manually add "{test_basename}" to sources in {test_dir}/BUILD.gn unit_tests target',
                        'parent_linked': True,
                        'fix_instructions': [
                            f'1. Open {test_dir}/BUILD.gn',
                            f'2. Find ios_unit_test("unit_tests") {{ sources = [ ... ] }}',
                            f'3. Add "{test_basename}" to the sources array',
                            f'OR change sources to use wildcard: sources = [ "*_unittest.mm" ]'
                        ]
                    })
                else:
                    return json.dumps({
                        'status': 'success',
                        'build_file_path': str(test_dir / 'BUILD.gn'),
                        'test_target': test_target,
                        'message': f'Test exists and linked to {test_target}',
                        'action_required': None
                    })
            
            # If NOT linked to parent, proceed with auto-linking
            if not parent_build_checked:
                    # Component tests are NOT linked to main test target!
                    # Try to automatically add the dependency
                    sys.stderr.write(f"\n[FIX] Attempting to automatically link component tests...\n")
                    sys.stderr.flush()
                    
                    # Determine which BUILD file and target based on component location
                    # Decision rules:
                    # 1. components/edge_*/ios -> ios_chrome_unittests (ios/chrome/test/BUILD_edge.gni) - Edge-specific
                    # 2. components/*/ios -> components_unittests (components/BUILD.gn) - 其他组件
                    # 3. ios/components/* -> ios_components_unittests (ios/components/BUILD.gn)
                    # 4. ios/chrome/* -> ios_chrome_unittests (ios/chrome/test/BUILD.gn or BUILD_edge.gni)
                    
                    normalized_test_path = str(test_dir).replace('\\', '/')
                    component_name = ''
                    target_build_file = None
                    target_name = ''
                    
                    if normalized_test_path.startswith('components/'):
                        # Extract component name: components/edge_hybrid/ios -> edge_hybrid
                        parts = normalized_test_path.split('/')
                        if len(parts) >= 2:
                            component_name = parts[1]
                        
                        # Check if it's an Edge-specific component
                        if is_edge or component_name.startswith('edge_'):
                            # Edge-specific components use edge_overlay_test_components_unittests template
                            # Template is DEFINED in BUILD_edge.gni with if (is_ios || is_android) blocks
                            # We need to modify BUILD_edge.gni (template definition, not the call in BUILD.gn)
                            target_build_file = src_root / 'components' / 'BUILD_edge.gni'
                            target_name = 'components_unittests'  # Target name
                            sys.stderr.write(f"[INFO] Edge component (components/{component_name}/ios) -> components_unittests\n")
                            sys.stderr.write(f"   Modifying: components/BUILD_edge.gni (template definition)\n")
                        else:
                            # Regular components go to components/BUILD.gn
                            target_build_file = src_root / 'components' / 'BUILD.gn'
                            target_name = 'components_unittests'
                            sys.stderr.write(f"[INFO] Component test (components/{component_name}/ios) -> components_unittests (components/BUILD.gn)\n")
                    
                    elif normalized_test_path.startswith('ios/components/'):
                        # iOS-specific component: goes to ios_components_unittests
                        target_build_file = src_root / 'ios' / 'components' / 'BUILD.gn'
                        target_name = 'ios_components_unittests'
                        sys.stderr.write(f"[INFO] iOS-specific component -> ios_components_unittests (ios/components/BUILD.gn)\n")
                    
                    else:
                        # Fallback: assume standard ios/chrome location
                        target_build_file = src_root / 'ios' / 'chrome' / 'test' / 'BUILD.gn'
                        target_name = 'ios_chrome_unittests'
                        sys.stderr.write(f"[INFO] Standard location -> ios_chrome_unittests (ios/chrome/test/BUILD.gn)\n")
                    
                    sys.stderr.write(f"[TARGET] Target: {target_name}\n")
                    sys.stderr.write(f"[TARGET] BUILD file: {target_build_file.relative_to(src_root)}\n")
                    sys.stderr.flush()
                    
                    if not target_build_file.exists():
                        manual_steps = f"""
{'='*80}
[FAIL] ERROR: Could not find target BUILD file
{'='*80}

Expected: ios/chrome/test/BUILD_edge.gni or BUILD.gn
Component target: {component_target_path}

Please manually add the dependency.
{'='*80}
"""
                        sys.stderr.write(manual_steps)
                        sys.stderr.flush()
                        return json.dumps({
                            'status': 'error',
                            'message': 'Target BUILD file not found',
                            'component_target': component_target_path
                        })
                    
                    # Read the target BUILD file
                    try:
                        with open(target_build_file, 'r', encoding='utf-8') as f:
                            target_content = f.read()
                        
                        # Find the correct deps section to modify
                        sys.stderr.write(f"\n[SEARCH] Analyzing target BUILD file...\n")
                        sys.stderr.write(f"   Looking for target: {target_name}\n")
                        sys.stderr.write(f"   Component to add: {component_target_path}\n")
                        sys.stderr.flush()
                        
                        sys.stderr.write(f"\n[NOTE] Calling _add_component_to_test_target with:\n")
                        sys.stderr.write(f"   component_target_path = {component_target_path}\n")
                        sys.stderr.write(f"   target_name = {target_name}\n")
                        sys.stderr.write(f"   target_build_file = {target_build_file}\n")
                        sys.stderr.write(f"   Content length = {len(target_content)} bytes\n")
                        sys.stderr.write(f"   Content preview (first 500 chars):\n")
                        sys.stderr.write(f"{target_content[:500]}\n")
                        sys.stderr.flush()
                        
                        success, modified_content = _add_component_to_test_target(
                            target_content,
                            component_target_path,
                            target_name
                        )
                        
                        sys.stderr.write(f"\n[REPORT] Result: {'[OK] Success' if success else '[FAIL] Failed to find insertion point'}\n")
                        if success:
                            sys.stderr.write(f"   Modified content length = {len(modified_content)} bytes\n")
                            sys.stderr.write(f"   Diff = {len(modified_content) - len(target_content)} bytes\n")
                        sys.stderr.flush()
                        
                        if success and auto_apply:
                            # Verify content actually changed
                            if modified_content == target_content:
                                sys.stderr.write(f"[!]️  WARNING: Content unchanged despite success!\n")
                                sys.stderr.write(f"   Component may already exist or pattern didn't match\n")
                                sys.stderr.write(f"   Checking if component already in file...\n")
                                if component_target_path in target_content:
                                    sys.stderr.write(f"[OK] Component already exists in BUILD file\n")
                                else:
                                    sys.stderr.write(f"[FAIL] Component NOT found but no changes made!\n")
                                    sys.stderr.write(f"   This indicates a logic bug in _add_component_to_test_target\n")
                                sys.stderr.flush()
                            
                            # Write back the modified content
                            with open(target_build_file, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            
                            sys.stderr.write(f"[OK] Successfully added {component_target_path}\n")
                            sys.stderr.write(f"   to {target_build_file.relative_to(src_root)}\n")
                            sys.stderr.write(f"   File written: {len(modified_content)} bytes\n")
                            sys.stderr.write(f"\n[TARGET] Next: Recompile with compile_ios_unittest\n")
                            sys.stderr.flush()
                            
                            return json.dumps({
                                'status': 'success',
                                'build_file_path': str(target_build_file.relative_to(src_root)),
                                'test_target': target_name,  # Use target_name (components_unittests), not test_target
                                'component_target': component_target_path,
                                'message': f'Successfully linked component tests to {target_name}',
                                'changes_applied': True,
                                'next_step': 'Recompile with compile_ios_unittest'
                            })
                        elif success:
                            # Preview mode
                            sys.stderr.write(f"[OK] Preview: Would add {component_target_path}\n")
                            sys.stderr.write(f"   Set auto_apply=True to apply changes\n")
                            sys.stderr.flush()
                            
                            return json.dumps({
                                'status': 'preview',
                                'build_file_path': str(target_build_file.relative_to(src_root)),
                                'test_target': target_name,
                                'component_target': component_target_path,
                                'changes_preview': modified_content[:500],
                                'changes_applied': False
                            })
                        else:
                            # Could not find insertion point
                            manual_steps = f"""
{'='*80}
# [!]️  MANUAL ACTION REQUIRED: Link Component Tests
{'='*80}

Could not automatically find insertion point in {target_build_file.relative_to(src_root)}

Please manually add:
  "{component_target_path}"

To the deps list in the appropriate test target (in alphabetical order).

{'='*80}
"""
                            sys.stderr.write(manual_steps)
                            sys.stderr.flush()
                            
                            return json.dumps({
                                'status': 'manual_action_required',
                                'build_file_path': str(target_build_file.relative_to(src_root)),
                                'component_target': component_target_path,
                                'message': 'Could not find insertion point automatically',
                                'manual_steps': manual_steps
                            })
                    
                    except Exception as e:
                        sys.stderr.write(f"[FAIL] Error modifying BUILD file: {e}\n")
                        sys.stderr.flush()
                        return json.dumps({
                            'status': 'error',
                            'message': f'Error modifying BUILD file: {str(e)}',
                            'component_target': component_target_path
                        })
        
        # Below is legacy code for old non-component tests, kept for backward compatibility
        if is_edge and not ('components/' in test_file_path or 'ios/components/' in test_file_path):
            # For Edge tests, update BUILD_edge.gni TEMPLATE DEFINITION
            # The deps are added inside the template, not in BUILD.gn
            build_file_path = 'ios/chrome/test/BUILD_edge.gni'
            src_root = get_chromium_src_root()
            full_path = os.path.join(src_root, build_file_path)
            
            if not os.path.exists(full_path):
                return json.dumps({
                    'status': 'error',
                    'error': f'BUILD_edge.gni not found at {build_file_path}'
                })
            
            # Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the test module directory
            test_dir = str(Path(test_file_path).parent)
            target_line = f'      "//{test_dir}:unit_tests",'
            
            # Check if already exists
            if target_line.strip() in content:
                sys.stderr.write(f"[OK] Target already exists in BUILD_edge.gni\n")
                sys.stderr.write(f"{'='*80}\n\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'already_exists',
                    'build_file_path': build_file_path,
                    'message': 'Test target already exists in BUILD_edge.gni template'
                })
            
            # Find the template's deps += [ ... ] section
            # Looking for: template("edge_overlay_test_ios_chrome_unittests") { ... deps += [ ... ] }
            pattern = r'(template\("edge_overlay_test_ios_chrome_unittests"\)\s*\{[^}]*?deps\s*\+=\s*\[)(.*?)(\n    \])'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                sys.stderr.write(f"[FAIL] Could not find template deps += array in BUILD_edge.gni\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'error',
                    'error': 'Could not find template("edge_overlay_test_ios_chrome_unittests") deps += array'
                })
            
            prefix = match.group(1)
            deps_content = match.group(2)
            suffix = match.group(3)
            
            # Parse deps - preserve EXACT original format including blank lines
            original_lines = deps_content.split('\n')
            
            # Build list of (line_content, is_dep_line) to track what to compare
            lines_info = []
            indent = '      '  # default
            
            for line in original_lines:
                stripped = line.strip()
                if not stripped:
                    # Blank line - keep it
                    lines_info.append((line, False, None))
                elif stripped.startswith('"//'):
                    # Dep line - extract indent if first one
                    if indent == '      ':
                        indent = line[:len(line) - len(line.lstrip())]
                    lines_info.append((line, True, stripped))
                else:
                    # Comment or other line - keep it
                    lines_info.append((line, False, None))
            
            # Find insertion position (alphabetical among dep lines only)
            new_entry_stripped = f'"//{test_dir}:unit_tests",'
            insertion_idx = 0
            
            for i, (line, is_dep, stripped) in enumerate(lines_info):
                if is_dep and stripped > new_entry_stripped:
                    insertion_idx = i
                    break
                insertion_idx = i + 1
            
            # Insert new entry with proper indentation
            new_entry_with_indent = f'{indent}{new_entry_stripped}'
            lines_info.insert(insertion_idx, (new_entry_with_indent, True, new_entry_stripped))
            
            # Generate preview
            changes_preview = f"Will insert:\n{new_entry_with_indent}\n\nBetween:\n"
            if insertion_idx > 0:
                prev_line = lines_info[insertion_idx-1][0]
                changes_preview += f"  {prev_line.strip()}\n"
            changes_preview += f"+ {new_entry_stripped}\n"
            if insertion_idx < len(lines_info) - 1:
                next_line = lines_info[insertion_idx+1][0]
                changes_preview += f"  {next_line.strip()}\n"
            
            # Apply changes if requested
            if auto_apply:
                # Rebuild deps content - just extract lines and join
                new_lines = [line_content for line_content, _, _ in lines_info]
                new_deps_content = '\n'.join(new_lines)
                
                # Ensure proper spacing: original pattern is \n<content>\n    ]
                # So new_deps_content should NOT have leading/trailing newlines
                new_content = content[:match.start(2)] + new_deps_content + content[match.end(2):]
                
                # Write back
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                sys.stderr.write(f"\n[OK] Successfully updated BUILD_edge.gni\n")
                sys.stderr.write(f"   Inserted at position {insertion_idx}\n")
                sys.stderr.write(f"   Target: {target_line.strip()}\n")
                sys.stderr.write(f"{'='*80}\n\n")
                sys.stderr.flush()
                
                return json.dumps({
                    'status': 'success',
                    'build_file_path': build_file_path,
                    'changes_preview': changes_preview,
                    'auto_applied': True,
                    'insertion_point': f'Position {insertion_idx} in deps array',
                    'target_added': target_line.strip(),
                    'message': f'[OK] Successfully updated {build_file_path}'
                }, indent=2)
            else:
                return json.dumps({
                    'status': 'preview',
                    'build_file_path': build_file_path,
                    'changes_preview': changes_preview,
                    'auto_applied': False,
                    'message': 'Preview only - set auto_apply=true to apply changes'
                }, indent=2)
        
        else:
            # For non-Edge, non-component tests under ios/chrome/browser/
            # They have local source_set("unit_tests") but need to be linked to ios_chrome_unittests
            sys.stderr.write(f"\n[INFO] Non-Edge ios/chrome test detected\n")
            sys.stderr.write(f"   Checking if local unit_tests is linked to ios_chrome_unittests...\n")
            sys.stderr.flush()
            
            # Check if test has local BUILD.gn with unit_tests target
            test_dir = Path(test_file_path).parent
            src_root = get_chromium_src_root()
            local_build_file = src_root / test_dir / 'BUILD.gn'
            
            if not local_build_file.exists():
                sys.stderr.write(f"[INFO] No local BUILD.gn - test directly in ios_chrome_unittests\n")
                sys.stderr.write(f"{'='*80}\n\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'not_needed',
                    'message': 'No local BUILD.gn - test should be directly in ios_chrome_unittests sources',
                })
            
            # Check if local BUILD.gn has unit_tests target
            local_content = local_build_file.read_text()
            has_unit_tests = 'source_set("unit_tests")' in local_content or 'ios_unit_test("unit_tests")' in local_content
            
            if not has_unit_tests:
                sys.stderr.write(f"[INFO] Local BUILD.gn exists but no unit_tests target\n")
                sys.stderr.write(f"{'='*80}\n\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'not_needed',
                    'message': 'Local BUILD.gn exists but no unit_tests target to link',
                })
            
            # Now check if this local unit_tests is linked to ios_chrome_unittests
            main_build_file = src_root / 'ios' / 'chrome' / 'test' / 'BUILD.gn'
            component_target_path = f"//{test_dir}:unit_tests"
            
            if not main_build_file.exists():
                sys.stderr.write(f"[FAIL] ios/chrome/test/BUILD.gn not found\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'error',
                    'message': 'ios/chrome/test/BUILD.gn not found',
                })
            
            main_content = main_build_file.read_text()
            
            if component_target_path in main_content:
                sys.stderr.write(f"[OK] Already linked: {component_target_path} -> ios_chrome_unittests\n")
                sys.stderr.write(f"{'='*80}\n\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'already_linked',
                    'message': f'{component_target_path} already in ios_chrome_unittests deps',
                })
            
            # Need to add the link!
            sys.stderr.write(f"[FIX] Linking {component_target_path} to ios_chrome_unittests...\n")
            sys.stderr.flush()
            
            if not auto_apply:
                return json.dumps({
                    'status': 'preview',
                    'message': f'Would add {component_target_path} to ios_chrome_unittests deps',
                    'action_required': 'Set auto_apply=True to apply changes',
                })
            
            # Find ios_chrome_unittests deps array and add the link
            # Try edge_overlay pattern first, then fall back to standard test()
            pattern = r'((?:edge_overlay_test_ios_chrome_unittests|test)\("ios_chrome_unittests"\)\s*\{[^}]*?deps\s*=\s*\[)(.*?)(\n  \])'
            match = re.search(pattern, main_content, re.DOTALL)
            
            if not match:
                sys.stderr.write(f"[FAIL] Could not find ios_chrome_unittests deps array\n")
                sys.stderr.flush()
                return json.dumps({
                    'status': 'error',
                    'message': 'Could not find ios_chrome_unittests deps array in BUILD.gn',
                })
            
            prefix = match.group(1)
            deps_content = match.group(2)
            suffix = match.group(3)
            
            # Parse existing deps
            deps_lines = [line.strip() for line in deps_content.split('\n') if line.strip() and line.strip().startswith('"')]
            
            # Add new entry in alphabetical order
            new_entry = f'"{component_target_path}",'
            insertion_idx = len(deps_lines)
            for i, line in enumerate(deps_lines):
                if line > new_entry:
                    insertion_idx = i
                    break
            
            deps_lines.insert(insertion_idx, new_entry)
            
            # Rebuild deps with proper indentation
            first_line_match = re.search(r'^(\s+)"', deps_content, re.MULTILINE)
            indent = first_line_match.group(1) if first_line_match else '    '
            
            new_deps_content = '\n' + '\n'.join([f'{indent}{line}' for line in deps_lines]) + '\n  '
            new_main_content = main_content[:match.start(2)] + new_deps_content + main_content[match.end(2):]
            
            # Write back
            main_build_file.write_text(new_main_content)
            
            sys.stderr.write(f"[OK] Successfully linked to ios_chrome_unittests\n")
            sys.stderr.write(f"   Added: {component_target_path}\n")
            sys.stderr.write(f"   Position: {insertion_idx} in deps array\n")
            sys.stderr.write(f"{'='*80}\n\n")
            sys.stderr.flush()
            
            return json.dumps({
                'status': 'success',
                'build_file_path': 'ios/chrome/test/BUILD.gn',
                'component_target': component_target_path,
                'message': f'Successfully linked {component_target_path} to ios_chrome_unittests',
            })
    
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        })


        coverage_after = (new_test_count / missing_info['total_methods'] * 100) if missing_info['total_methods'] > 0 else 100
        
        sys.stderr.write(f"\\n[OK] Updated test file: {test_file_path}\\n")
        sys.stderr.write(f"  Added {len(missing_info['missing_methods'])} new test cases\\n")
        sys.stderr.write(f"  Coverage: {missing_info['coverage_percentage']:.1f}% -> {coverage_after:.1f}%\\n\\n")
        sys.stderr.flush()
        
        return json.dumps({
            'status': 'success',
            'test_file': test_file_path,
            'existing_test_count': len(existing_analysis['test_cases']),
            'new_tests_generated': len(missing_info['missing_methods']),
            'missing_methods': missing_info['missing_methods'],
            'coverage_before': missing_info['coverage_percentage'],
            'coverage_after': coverage_after,
            'next_steps': [
                'Compile tests: compile_ios_unittest',
                'Run tests: run_ios_unittest'
            ]
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': str(e),
            'traceback': str(e)
        })


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Start the MCP server.
    
    This server provides iOS unit test generation tools for VS Code.
    It can be started standalone or integrated with VS Code MCP extension.
    
    Usage:
        uvx ios-unittest-generator           # Run via uvx (recommended)
        python -m ios_unittest_generator     # Run as module
    """
    # CRITICAL: Do NOT print to stdout when running as MCP server
    # VS Code MCP extension uses stdio for JSON-RPC communication
    # Any print() statements will corrupt the protocol messages
    
    # Redirect stderr to devnull to prevent any debug output from breaking protocol
    # MCP uses stdio, so we must be silent
    sys.stderr = open(os.devnull, 'w')
    
    # Run the MCP server
    mcp.run()


if __name__ == '__main__':
    main()
