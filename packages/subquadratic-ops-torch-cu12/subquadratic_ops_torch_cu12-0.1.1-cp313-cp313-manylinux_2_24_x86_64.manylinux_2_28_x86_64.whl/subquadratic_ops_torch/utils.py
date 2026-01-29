# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import warnings
from functools import lru_cache
from typing import List

import torch
from pynvml import nvmlInit, nvmlShutdown, nvmlSystemGetCudaDriverVersion

import subquadratic_ops_torch._ext as ops


def dtype_to_str(dtype: torch.dtype):
    outputs = {
        torch.bfloat16: "bf16",
        torch.float32: "fp32",
        torch.double: "fp64",
        torch.half: "fp16",
    }
    return outputs[dtype]


def get_module(name, dtypes: List[torch.dtype] = None):
    return getattr(ops, name + "_" + "".join(map(dtype_to_str, dtypes)))


def next_pow2(n: int) -> int:
    """Return the next power of 2 greater than or equal to n."""
    if n <= 0:
        return 1
    if n & (n - 1) == 0:  # n is already a power of 2
        return n
    return 1 << (n.bit_length())


@lru_cache(maxsize=None)
def get_cuda_arch(dev_idx: int = 0) -> int:
    props = torch.cuda.get_device_properties(dev_idx)
    return props.major * 100 + props.minor * 10


def get_cuda_driver_version() -> int:
    nvmlInit()
    try:
        v = nvmlSystemGetCudaDriverVersion()  # e.g. 12080 for CUDA 12.8
        return v
    except Exception as e:
        raise RuntimeError(f"Failed to get CUDA driver version: {e}")
    finally:
        nvmlShutdown()


def cuda_driver_warning():
    cuda_driver_version = get_cuda_driver_version()
    if cuda_driver_version < 12080:
        warnings.warn(f"[subquadratic_ops_torch] CUDA driver version {cuda_driver_version} is old. Please update to at least 12.8.")
