#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""iOS Unit Test Generator MCP Server.

This package provides MCP tools to generate unit tests for iOS Edge/Chromium code.
"""

__version__ = "4.19.1"

from .server import mcp, main

__all__ = ["mcp", "main", "__version__"]
