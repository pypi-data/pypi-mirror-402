# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import List, Optional

import torch
from torch import Tensor

from subquadratic_ops_torch.utils import get_module


@torch.library.custom_op(
    "subquadratic_ops_torch::causal_conv1d_fwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor, weight: Tensor, bias: Tensor, activation: str) -> Tensor:
    if x.dim() != 3 or weight.dim() != 2 or bias.dim() != 1:
        raise ValueError(f"Input, weights, and bias must be 3D, 2D, and 1D tensors, {x.shape}, {weight.shape}, {bias.shape}")
    assert activation in ["silu", "identity"], f"Invalid activation: {activation}"

    x = x.contiguous()
    weight = weight.contiguous()
    bias = bias.contiguous()
    y = torch.empty((x.shape[0], x.shape[1], x.shape[2]), device=x.device, dtype=x.dtype)

    module = get_module("causal_conv1d_fwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id
    module(y.detach(), x.detach(), weight.detach(), bias.detach(), activation, stream_id)

    return y


@torch.library.register_fake("subquadratic_ops_torch::causal_conv1d_fwd_primitive")
def _(x: Tensor, weight: Tensor, bias: Tensor, activation: str) -> Tensor:
    return torch.empty_like(x)


@torch.library.custom_op(
    "subquadratic_ops_torch::causal_conv1d_bwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(grad_out: Tensor, x: Tensor, weight: Tensor, bias: Tensor, activation: str) -> List[Tensor]:
    if x.dim() != 3 or weight.dim() != 2 or bias.dim() != 1:
        raise ValueError(f"Input, weights, and bias must be 3D, 2D, and 1D tensors, {x.shape}, {weight.shape}, {bias.shape}")

    grad_out_y = grad_out

    grad_x = torch.empty(x.shape, device=x.device, dtype=x.dtype)
    grad_weight = torch.zeros(
        weight.shape,
        device=x.device,
        dtype=torch.float32 if x.dtype.itemsize == 2 else x.dtype,
    )
    grad_bias = torch.zeros(
        bias.shape,
        device=x.device,
        dtype=torch.float32 if x.dtype.itemsize == 2 else x.dtype,
    )
    module = get_module("causal_conv1d_bwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id

    x = x.contiguous()
    weight = weight.contiguous()
    bias = bias.contiguous()
    grad_out_y = grad_out_y.contiguous()

    module(
        grad_x.detach(),
        grad_weight.detach(),
        grad_bias.detach(),
        grad_out_y.detach(),
        x.detach(),
        weight.detach(),
        bias.detach(),
        activation,
        stream_id,
    )

    return [grad_x, grad_weight.to(x.dtype), grad_bias.to(x.dtype)]


@torch.library.register_fake("subquadratic_ops_torch::causal_conv1d_bwd_primitive")
def _(grad_out: Tensor, x: Tensor, weight: Tensor, bias: Tensor, activation: str) -> List[Tensor]:
    return [torch.empty_like(x), torch.empty_like(weight), torch.empty_like(bias)]


def causal_conv1d_fwd_setup_fwd_context(ctx, inputs, output):
    (x, weight, bias, activation) = inputs
    ctx.save_for_backward(x, weight, bias)  # Save y_gated along with other tensors
    ctx.activation = activation


@torch.compiler.allow_in_graph
def causal_conv1d_fwd(*args):
    return torch.ops.subquadratic_ops_torch.causal_conv1d_fwd_primitive(*args)


@torch.compiler.allow_in_graph
def causal_conv1d_bwd(ctx, grad_out):
    x, weight, bias = ctx.saved_tensors
    # print(ctx.activation)
    dx, dw, db = torch.ops.subquadratic_ops_torch.causal_conv1d_bwd_primitive(grad_out, x, weight, bias, ctx.activation)
    return dx, dw, db, None


torch.library.register_autograd(
    "subquadratic_ops_torch::causal_conv1d_fwd_primitive",
    causal_conv1d_bwd,
    setup_context=causal_conv1d_fwd_setup_fwd_context,
)


def causal_conv1d(
    x: Tensor,
    weight: Tensor,
    bias: Optional[Tensor] = None,
    activation: str = "identity",
) -> Tensor:
    r"""
    Depthwise causal 1D convolution with optional activation.

    Each channel is convolved with its own kernel. *Causal* means the output at time
    :math:`t` depends only on inputs at times :math:`\le t`.

    .. math::

        y_{b,c,t} =
        \mathrm{activation}\left(
            \sum_{k=0}^{K-1} x_{b,c,t-k} \cdot w_{c,k} + b_c
        \right)

    Args:
        x (torch.Tensor): Input tensor of shape ``(batch_size, dim, seq_len)``.
        weight (torch.Tensor): Weight tensor of shape ``(dim, kernel_size)``.
        bias (torch.Tensor | None): Optional bias tensor of shape ``(dim,)``.
        activation (str): Activation function to apply. Supported: ``"silu"``, ``"identity"``.

    Returns:
        torch.Tensor: Output tensor of shape ``(batch_size, dim, seq_len)``.

    Example:
        .. code-block:: python

            batch_size, dim, seq_len, kernel_size = 2, 4, 10, 3
            x = torch.randn(batch_size, dim, seq_len, device="cuda")
            weight = torch.randn(dim, kernel_size, device="cuda")
            bias = torch.randn(dim, device="cuda")
            y = causal_conv1d(x, weight, bias, activation="silu")
            print(y.shape)  # torch.Size([2, 4, 10])
    """
    assert activation in ["silu", "identity"], f"Invalid activation: {activation}"
    if bias is None:
        bias = torch.zeros(weight.shape[0], device=x.device, dtype=x.dtype)
    return torch.ops.subquadratic_ops_torch.causal_conv1d_fwd_primitive(x, weight, bias, activation)
