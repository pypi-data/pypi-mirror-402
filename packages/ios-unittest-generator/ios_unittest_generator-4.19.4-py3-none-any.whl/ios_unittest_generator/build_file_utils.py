#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""BUILD file manipulation utilities.

This module provides functions for updating BUILD.gn and BUILD_edge.gni files.
Refactored from the monolithic _add_component_to_test_target function.
"""

import re
import sys
from typing import List, Optional, Tuple


class BuildFileUpdater:
    """Handles BUILD file updates with strategy pattern."""
    
    def __init__(self, build_content: str, component_target: str, target_name: str):
        """Initialize the updater.
        
        Args:
            build_content: Content of the BUILD file
            component_target: Target path like "//components/xxx/ios:unit_tests"
            target_name: Test target name ('ios_chrome_unittests', etc.)
        """
        self.build_content = build_content
        self.component_target = component_target
        self.target_name = target_name
    
    def update(self) -> Tuple[bool, str]:
        """Update BUILD file using appropriate strategy.
        
        Returns:
            (success, modified_content) tuple
        """
        # Try strategies in order
        strategies = [
            self._strategy_edge_components_template,
            self._strategy_edge_ios_template,
            self._strategy_direct_target,
        ]
        
        for strategy in strategies:
            success, content = strategy()
            if success:
                return True, content
        
        return False, self.build_content
    
    def _strategy_edge_components_template(self) -> Tuple[bool, str]:
        """Strategy 0: edge_overlay_test_components_unittests template."""
        if self.target_name != 'components_unittests':
            return False, self.build_content
        
        if 'edge_overlay_test_components_unittests' not in self.build_content:
            return False, self.build_content
        
        sys.stderr.write(f"\n[STRATEGY 0] Edge components template\n")
        sys.stderr.flush()
        
        # Find template definition
        template_match = self._find_template_definition('edge_overlay_test_components_unittests')
        if not template_match:
            sys.stderr.write(f"[FAIL] Template not found\n")
            sys.stderr.flush()
            return False, self.build_content
        
        template_content = template_match.group(1)
        template_start = template_match.start(1)
        
        # Find if (is_ios || is_android) block
        ios_block = self._find_ios_conditional_block(template_content)
        if not ios_block:
            sys.stderr.write(f"[FAIL] iOS conditional block not found\n")
            sys.stderr.flush()
            return False, self.build_content
        
        ios_content, ios_start, ios_end = ios_block
        
        # Find or create deps += array
        deps_match = re.search(r'(deps\s*\+=\s*\[)(.*?)(\])', ios_content, re.DOTALL)
        
        if deps_match:
            # Insert into existing deps
            return self._insert_into_deps_array(
                template_start + ios_start + deps_match.start(2),
                template_start + ios_start + deps_match.end(2),
                deps_match.group(2),
                indent='        '
            )
        else:
            # Create new deps += array
            insert_pos = template_start + ios_start
            new_deps = f'\n      deps += [\n        "{self.component_target}",\n      ]'
            new_content = self.build_content[:insert_pos] + new_deps + self.build_content[insert_pos:]
            sys.stderr.write(f"[OK] Created new deps += section\n")
            sys.stderr.flush()
            return True, new_content
    
    def _strategy_edge_ios_template(self) -> Tuple[bool, str]:
        """Strategy 1: edge_overlay_test_ios_chrome_unittests template."""
        if self.target_name != 'ios_chrome_unittests':
            return False, self.build_content
        
        if 'edge_overlay_test_ios_chrome_unittests' not in self.build_content:
            return False, self.build_content
        
        sys.stderr.write(f"\n[STRATEGY 1] Edge iOS template\n")
        sys.stderr.flush()
        
        pattern = r'(edge_overlay_test_ios_chrome_unittests\s*\([^)]+\)\s*\{[^}]*?deps\s*(?:\+)?=\s*\[)(.*?)(\])'
        match = re.search(pattern, self.build_content, re.DOTALL)
        
        if not match:
            return False, self.build_content
        
        return self._insert_into_deps_array(
            match.start(2),
            match.end(2),
            match.group(2),
            indent='      '
        )
    
    def _strategy_direct_target(self) -> Tuple[bool, str]:
        """Strategy 2: Find target directly by name."""
        sys.stderr.write(f"\n[STRATEGY 2] Direct target search\n")
        sys.stderr.flush()
        
        # Try to find test(...) or source_set(...)
        pattern = rf'((?:source_set|test)\s*\(\s*"{re.escape(self.target_name)}"\s*\)\s*\{{.*?deps\s*(?:\+)?=\s*\[)(.*?)(\])'
        match = re.search(pattern, self.build_content, re.DOTALL)
        
        if not match:
            sys.stderr.write(f"[FAIL] Target not found\n")
            sys.stderr.flush()
            return False, self.build_content
        
        return self._insert_into_deps_array(
            match.start(2),
            match.end(2),
            match.group(2),
            indent='    '
        )
    
    def _find_template_definition(self, template_name: str) -> Optional[re.Match]:
        """Find template definition in BUILD file."""
        template_pattern = rf'template\s*\(\s*"{template_name}"\s*\)\s*\{{'
        match = re.search(template_pattern, self.build_content)
        
        if not match:
            return None
        
        # Find matching closing brace
        start_pos = match.end()
        brace_count = 1
        pos = start_pos
        
        while pos < len(self.build_content) and brace_count > 0:
            if self.build_content[pos] == '{':
                brace_count += 1
            elif self.build_content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count == 0:
            # Create a match object for the template content
            class TemplateMatch:
                def __init__(self, content, start, end):
                    self._content = content
                    self._start = start
                    self._end = end
                
                def group(self, n):
                    if n == 1:
                        return self._content[self._start:self._end]
                    return None
                
                def start(self, n):
                    return self._start
                
                def end(self, n):
                    return self._end
            
            return TemplateMatch(self.build_content, start_pos, pos - 1)
        
        return None
    
    def _find_ios_conditional_block(self, content: str) -> Optional[Tuple[str, int, int]]:
        """Find if (is_ios || is_android) or if (is_ios) block."""
        # Try is_ios || is_android first
        markers = [
            'if (is_ios || is_android) {',
            'if (is_ios) {',
        ]
        
        for marker in markers:
            pos = content.find(marker)
            if pos != -1:
                block_start = pos + len(marker)
                brace_count = 1
                close_pos = block_start
                
                while close_pos < len(content) and brace_count > 0:
                    if content[close_pos] == '{':
                        brace_count += 1
                    elif content[close_pos] == '}':
                        brace_count -= 1
                    close_pos += 1
                
                if brace_count == 0:
                    block_content = content[block_start:close_pos - 1]
                    return (block_content, block_start, close_pos - 1)
        
        return None
    
    def _insert_into_deps_array(
        self,
        deps_start: int,
        deps_end: int,
        deps_content: str,
        indent: str
    ) -> Tuple[bool, str]:
        """Insert component target into deps array alphabetically.
        
        Args:
            deps_start: Start position of deps content
            deps_end: End position of deps content
            deps_content: Current deps content
            indent: Indentation to use for entries
            
        Returns:
            (success, modified_content) tuple
        """
        # Parse existing deps
        deps_lines = deps_content.split('\n')
        deps_entries = []
        for line in deps_lines:
            stripped = line.strip()
            if stripped and (stripped.startswith('"//') or stripped.startswith('"-=')):
                deps_entries.append(stripped)
        
        # Check if already exists
        new_entry = f'"{self.component_target}",'
        if new_entry.strip() in ' '.join(deps_entries):
            sys.stderr.write(f"[INFO] Component already in deps\n")
            sys.stderr.flush()
            return False, self.build_content
        
        # Find insertion point (alphabetical)
        insertion_idx = len(deps_entries)
        for i, entry in enumerate(deps_entries):
            if '-=' in entry:
                continue
            if entry > new_entry:
                insertion_idx = i
                break
            insertion_idx = i + 1
        
        # Insert new entry
        deps_entries.insert(insertion_idx, new_entry)
        
        # Reconstruct deps
        new_deps_lines = [f'{indent}{entry}' for entry in deps_entries]
        new_deps_content = '\n' + '\n'.join(new_deps_lines) + f'\n{indent[:-2]}'
        
        # Replace in content
        new_content = self.build_content[:deps_start] + new_deps_content + self.build_content[deps_end:]
        sys.stderr.write(f"[OK] Component added to deps\n")
        sys.stderr.flush()
        return True, new_content


def add_component_to_test_target(
    build_content: str,
    component_target: str,
    target_name: str
) -> Tuple[bool, str]:
    """Add component target to the appropriate test target's deps.
    
    Refactored version using strategy pattern.
    
    Args:
        build_content: Content of BUILD file
        component_target: Target path like "//components/xxx/ios:unit_tests"
        target_name: Test target name ('ios_chrome_unittests', etc.)
        
    Returns:
        (success, modified_content) tuple
    """
    updater = BuildFileUpdater(build_content, component_target, target_name)
    return updater.update()
