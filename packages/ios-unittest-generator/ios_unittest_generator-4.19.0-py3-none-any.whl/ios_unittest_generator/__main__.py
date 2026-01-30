#!/usr/bin/env python3
# Copyright (C) Microsoft Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Entry point for running the MCP server directly with `python -m ios_unittest_generator`."""

from .server import main

if __name__ == "__main__":
    main()
