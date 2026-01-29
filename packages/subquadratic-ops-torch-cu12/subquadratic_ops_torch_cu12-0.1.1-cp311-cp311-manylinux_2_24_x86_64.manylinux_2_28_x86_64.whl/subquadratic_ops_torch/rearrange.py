# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import torch
from torch import Tensor

from subquadratic_ops_torch.utils import get_module


@torch.library.custom_op(
    "subquadratic_ops_torch::rearrange_bhl_to_lbh_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor) -> Tensor:
    if x.dim() != 3:
        raise ValueError(f"Input must be a 3D tensor, got {x.shape}")

    x = x.contiguous()
    b, h, l = x.shape
    y = torch.empty((l, b, h), device=x.device, dtype=x.dtype)

    module = get_module("rearrange_conv1d_bhl_to_lbh", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id
    module(y.detach(), x.detach(), stream_id)

    return y


@torch.library.register_fake("subquadratic_ops_torch::rearrange_bhl_to_lbh_primitive")
def _(x: Tensor) -> Tensor:
    b, h, l = x.shape
    return torch.empty((l, b, h), device=x.device, dtype=x.dtype)


@torch.library.custom_op(
    "subquadratic_ops_torch::rearrange_lbh_to_bhl_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor) -> Tensor:
    if x.dim() != 3:
        raise ValueError(f"Input must be a 3D tensor, got {x.shape}")

    x = x.contiguous()
    l, b, h = x.shape
    y = torch.empty((b, h, l), device=x.device, dtype=x.dtype)

    module = get_module("rearrange_conv1d_lbh_to_bhl", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id
    module(y.detach(), x.detach(), stream_id)

    return y


@torch.library.register_fake("subquadratic_ops_torch::rearrange_lbh_to_bhl_primitive")
def _(x: Tensor) -> Tensor:
    l, b, h = x.shape
    y = torch.empty((b, h, l), device=x.device, dtype=x.dtype)
    return y


@torch.compiler.allow_in_graph
def rearrange_bhl_to_lbh_fwd(x: Tensor) -> Tensor:
    return torch.ops.subquadratic_ops_torch.rearrange_bhl_to_lbh_primitive(x)


@torch.compiler.allow_in_graph
def rearrange_lbh_to_bhl_fwd(x: Tensor) -> Tensor:
    return torch.ops.subquadratic_ops_torch.rearrange_lbh_to_bhl_primitive(x)


@torch.compiler.allow_in_graph
def rearrange_bhl_to_lbh_bwd(ctx, grad_out):
    return torch.ops.subquadratic_ops_torch.rearrange_lbh_to_bhl_primitive(grad_out)


@torch.compiler.allow_in_graph
def rearrange_lbh_to_bhl_bwd(ctx, grad_out):
    return torch.ops.subquadratic_ops_torch.rearrange_bhl_to_lbh_primitive(grad_out)


torch.library.register_autograd("subquadratic_ops_torch::rearrange_bhl_to_lbh_primitive", rearrange_bhl_to_lbh_bwd)

torch.library.register_autograd("subquadratic_ops_torch::rearrange_lbh_to_bhl_primitive", rearrange_lbh_to_bhl_bwd)


def rearrange(x: Tensor, bhl_to_lbh: bool) -> Tensor:
    r"""
    Rearrange the tensor dimensions from ``(batch_size, hidden_dim, seq_dim)`` to ``(seq_dim, batch_size, hidden_dim)`` or vice versa.

    Args:
        x (torch.Tensor): Input tensor of shape ``(batch_size, hidden_dim, seq_dim)``.
        bhl_to_lbh (bool): If True, rearrange the tensor from ``(batch_size, hidden_dim, seq_dim)`` to ``(seq_dim, batch_size, hidden_dim)``.

    Returns:
        torch.Tensor: Output tensor of shape ``(seq_dim, batch_size, hidden_dim)`` if ``bhl_to_lbh`` is True, otherwise ``(batch_size, hidden_dim, seq_dim)``.

    Example:
        .. code-block:: python

            x = torch.randn(2, 3, 4)
            y = rearrange(x, bhl_to_lbh=True)
            print(y.shape)  # torch.Size([4, 2, 3])
            y = rearrange(x, bhl_to_lbh=False)
            print(y.shape)  # torch.Size([3, 4, 2])
    """
    if bhl_to_lbh:
        return torch.ops.subquadratic_ops_torch.rearrange_bhl_to_lbh_primitive(x)
    else:
        return torch.ops.subquadratic_ops_torch.rearrange_lbh_to_bhl_primitive(x)
