# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


from typing import List

import torch
import warp as wp

MODULES = {}


def get_dtype(dtype: str):
    """
    Get the dtype for the given dtype
    WIP
    """
    if dtype.endswith(".float16"):
        return "fp16"
    elif dtype.endswith(".float32"):
        return "fp32"
    elif dtype.endswith(".float64"):
        return "fp64"
    elif dtype.endswith(".int8"):
        return "int8"
    elif dtype.endswith(".int16"):
        return "int16"
    elif dtype.endswith(".int32"):
        return "int32"
    elif dtype.endswith(".int64"):
        return "int64"
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")


def get_warp_module(name: str, dtype: List[str]):
    """
    Get the module for the given name and dtype
    """
    full_name = name + "_" + "_".join(get_dtype(d) for d in dtype)
    if full_name not in MODULES:
        raise ValueError(f"Module {full_name} not found")
    return MODULES[full_name]


def add_warp_module(name: str, dtype: List[str], kernel: wp.Kernel):
    """
    Add the module for the given name and dtype
    """
    full_name = name + "_" + "_".join(get_dtype(d) for d in dtype)
    if full_name not in MODULES:
        MODULES[full_name] = kernel
    return MODULES[full_name]


def list_modules():
    """
    List all modules in the MODULES dictionary
    """
    print("Available modules:")
    for name in MODULES.keys():
        print(f"  - {name}")
    return list(MODULES.keys())


def get_stream(device: torch.device):
    """
    Get the stream for the given device
    """
    if device.type == "cuda":
        return wp.stream_from_torch(torch.cuda.current_stream(device))
    else:
        return None


def get_warp_dtype(dtype: str):
    if dtype.endswith(".float32"):
        return wp.float32
    elif dtype.endswith(".float16"):
        return wp.float16
    elif dtype.endswith(".bfloat16"):
        return wp.bfloat16
    elif dtype.endswith(".float64"):
        return wp.float64
    elif dtype.endswith(".int8"):
        return wp.int8
    elif dtype.endswith(".int16"):
        return wp.int16
    elif dtype.endswith(".int32"):
        return wp.int32
    elif dtype.endswith(".int64"):
        return wp.int64
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")
