#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Thread-safe workflow state management.

This module provides thread-safe state management for the test generation workflow.
Uses threading locks to prevent race conditions in concurrent scenarios.
"""

import threading
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class WorkflowState:
    """State for a single test generation workflow."""
    
    source_file: str
    step_1_analyze_complete: bool = False
    step_2_generate_complete: bool = False
    step_3_enhancement_verified: bool = False  # Critical gate
    step_4_build_updated: bool = False
    step_5_compilation_success: bool = False
    step_6_tests_passed: bool = False
    test_file_path: Optional[str] = None
    test_count_baseline: int = 0
    quality_score_baseline: int = 0
    workflow_started: bool = False


class WorkflowStateManager:
    """Thread-safe manager for workflow states.
    
    This class uses a lock to ensure thread-safe access to workflow states,
    preventing race conditions when multiple workflows run concurrently.
    """
    
    def __init__(self):
        """Initialize the state manager with an empty state dictionary and a lock."""
        self._states: Dict[str, WorkflowState] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
    
    def get_state(self, source_file: str) -> WorkflowState:
        """Get or create workflow state for a source file.
        
        Args:
            source_file: Path to the source file
            
        Returns:
            WorkflowState for the source file
        """
        with self._lock:
            if source_file not in self._states:
                self._states[source_file] = WorkflowState(source_file=source_file)
            return self._states[source_file]
    
    def update_state(self, source_file: str, **updates) -> None:
        """Update workflow state for a source file.
        
        Args:
            source_file: Path to the source file
            **updates: Key-value pairs to update in the state
        """
        with self._lock:
            state = self.get_state(source_file)
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)
    
    def clear_state(self, source_file: str) -> None:
        """Clear workflow state for a source file.
        
        Args:
            source_file: Path to the source file
        """
        with self._lock:
            if source_file in self._states:
                del self._states[source_file]
    
    def clear_all_states(self) -> None:
        """Clear all workflow states (useful for testing)."""
        with self._lock:
            self._states.clear()
    
    def get_all_states(self) -> Dict[str, WorkflowState]:
        """Get a copy of all workflow states.
        
        Returns:
            Dictionary mapping source files to their workflow states
        """
        with self._lock:
            return self._states.copy()
    
    def has_state(self, source_file: str) -> bool:
        """Check if a workflow state exists for a source file.
        
        Args:
            source_file: Path to the source file
            
        Returns:
            True if state exists, False otherwise
        """
        with self._lock:
            return source_file in self._states


# Global workflow state manager instance
_state_manager: Optional[WorkflowStateManager] = None
_manager_lock = threading.Lock()


def get_state_manager() -> WorkflowStateManager:
    """Get the global workflow state manager (singleton pattern).
    
    Returns:
        The global WorkflowStateManager instance
    """
    global _state_manager
    if _state_manager is None:
        with _manager_lock:
            if _state_manager is None:  # Double-check locking
                _state_manager = WorkflowStateManager()
    return _state_manager


def reset_state_manager():
    """Reset the state manager (useful for testing)."""
    global _state_manager
    with _manager_lock:
        _state_manager = None


# Convenience functions for backward compatibility
def get_workflow_state(source_file: str) -> WorkflowState:
    """Get or create workflow state for a source file.
    
    Args:
        source_file: Path to the source file
        
    Returns:
        WorkflowState for the source file
    """
    return get_state_manager().get_state(source_file)


def update_workflow_state(source_file: str, **updates) -> None:
    """Update workflow state for a source file.
    
    Args:
        source_file: Path to the source file
        **updates: Key-value pairs to update in the state
    """
    get_state_manager().update_state(source_file, **updates)
