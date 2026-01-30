#!/usr/bin/env python

# Copyright 2025 LUNA team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""LUNA Robot Adapters.

This module provides adapters for robots that may not be available in the
standard LeRobot installation, allowing LUNA to work with custom robot
implementations without modifying the base LeRobot library.
"""

# Import bi_piper_follower adapter if available
try:
    from luna.robots.bi_piper_follower_adapter import (  # noqa: F401
        BiPIPERFollower,
        BiPIPERFollowerConfig,
    )
except ImportError:
    # Robot adapter not available
    pass

__all__ = []

