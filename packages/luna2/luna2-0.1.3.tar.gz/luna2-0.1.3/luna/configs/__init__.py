#!/usr/bin/env python

# Copyright 2025 LUNA team. All rights reserved.
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
"""LUNA Configuration Module.

This module provides configuration classes for LUNA inference:
- RunConfig: Inference configuration for real robot deployment
"""

from luna.configs.run_config import RunConfig
from luna.policies.pi05 import PI05Config

# Register LUNA policy configs with LeRobot's config registry.
# This ensures `type: pi05` and `type: pi0` in YAML configs resolve
# to LUNA variants that include vlm_config/action_expert_config.
from lerobot.configs.policies import PreTrainedConfig as _LRPreTrainedConfig

_LRPreTrainedConfig._choice_registry["pi05"] = PI05Config

__all__ = ["RunConfig", "PI05Config"]
