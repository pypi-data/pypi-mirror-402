# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import List, Tuple

import torch
import torch.nn.functional as F
from torch import Tensor

from subquadratic_ops_torch.utils import get_cuda_arch, get_module, next_pow2


def compute_scratch_space_size(seq_length_x: int, seq_length_y: int) -> Tuple[int, int]:
    fft_size_y = 2 * (next_pow2(seq_length_y) + 1)

    return (seq_length_x, fft_size_y)


def compatible_filter_length(filter_length: int) -> int:
    return max(128, next_pow2(filter_length))


@torch.library.custom_op(
    "subquadratic_ops_torch::fft_conv2d_fwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor, weight: Tensor) -> List[Tensor]:
    if x.dim() != 4 or weight.dim() != 3 or x.shape[-1] != weight.shape[-1] or x.shape[-2] != weight.shape[-2]:
        raise ValueError(
            f"Input and weights must be 4D and 3D tensors, {x.shape}, {weight.shape}, and x.shape[-1] and weight.shape[-1] must be equal, and x.shape[-2] and weight.shape[-2] must be equal"
        )
    if x.shape[-1] % 2 == 1:
        raise ValueError(f"Input sequence length must be even, got {x.shape[-1]}")

    x = x.contiguous()
    weight = weight.contiguous()
    y = torch.empty_like(x).contiguous()

    module = get_module("fft_conv2d_fwd", [x.dtype])
    arch = get_cuda_arch(x.device.index)
    stream_id = torch.cuda.current_stream(x.device).stream_id
    scratch_space_size = compute_scratch_space_size(x.shape[-2], x.shape[-1])

    inter_w = torch.empty(
        weight.shape[0],
        scratch_space_size[0],
        scratch_space_size[1],
        device=x.device,
        dtype=x.dtype,
    )

    module(y.detach(), x.detach(), weight.detach(), inter_w.detach(), arch, stream_id)

    return [y, inter_w]


@torch.library.register_fake("subquadratic_ops_torch::fft_conv2d_fwd_primitive")
def _(x: Tensor, weight: Tensor) -> List[Tensor]:
    scratch_space_size = compute_scratch_space_size(x.shape[-2], x.shape[-1])
    return [
        torch.empty_like(x),
        torch.empty(
            weight.shape[0],
            scratch_space_size[0],
            scratch_space_size[1],
            device=x.device,
            dtype=x.dtype,
        ),
    ]


@torch.library.custom_op(
    "subquadratic_ops_torch::fft_conv2d_bwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(grad_out: Tensor, x: Tensor, weight: Tensor, inter_w: Tensor) -> List[Tensor]:
    if x.dim() != 4 or weight.dim() != 3 or x.shape[-1] != weight.shape[-1] or x.shape[-2] != weight.shape[-2]:
        raise ValueError(
            f"Input and weights must be 4D and 3D tensors, {x.shape}, {weight.shape}, and x.shape[-1] and weight.shape[-1] must be equal, and x.shape[-2] and weight.shape[-2] must be equal"
        )
    if x.shape[-1] % 2 == 1:
        raise ValueError(f"Input sequence length must be even, got {x.shape[-1]}")
    if weight.shape[-1] % 2 == 1:
        raise ValueError(f"Filter length must be even, got {weight.shape[-1]}")

    grad_out_y = grad_out
    grad_x = torch.empty_like(x)
    grad_weight = torch.zeros_like(weight)
    x = x.contiguous()
    grad_out_y = grad_out_y.contiguous()
    inter_dw = torch.empty_like(inter_w)

    module = get_module("fft_conv2d_bwd", [x.dtype])
    arch = get_cuda_arch(x.device.index)
    stream_id = torch.cuda.current_stream(x.device).stream_id

    module(
        grad_x.detach(),
        grad_weight.detach(),
        grad_out_y.detach(),
        x.detach(),
        inter_w.detach(),
        inter_dw.detach(),
        arch,
        stream_id,
    )

    return [grad_x, grad_weight]


@torch.library.register_fake("subquadratic_ops_torch::fft_conv2d_bwd_primitive")
def _(grad_out: Tensor, x: Tensor, weight: Tensor, inter_w: Tensor) -> List[Tensor]:
    return [torch.empty_like(x), torch.empty_like(weight)]


@torch.compiler.allow_in_graph
def fft_conv2d_bwd(ctx, grad_out):
    x, weight, inter_w = ctx.saved_tensors
    grad_out_y = grad_out[0].contiguous()
    grad_x, grad_weight = torch.ops.subquadratic_ops_torch.fft_conv2d_bwd_primitive(grad_out_y, x, weight, inter_w)
    return grad_x, grad_weight


@torch.compiler.allow_in_graph
def fft_conv2d_fwd(*args):
    return torch.ops.subquadratic_ops_torch.fft_conv2d_fwd_primitive(*args)


def fft_conv2d_fwd_setup_fwd_context(ctx, inputs, output):
    (x, weight) = inputs
    (_, inter_w) = output
    ctx.save_for_backward(x, weight, inter_w)


torch.library.register_autograd(
    "subquadratic_ops_torch::fft_conv2d_fwd_primitive",
    fft_conv2d_bwd,
    setup_context=fft_conv2d_fwd_setup_fwd_context,
)


def fft_conv2d(x: Tensor, weight: Tensor) -> Tensor:
    r"""
    FFT-based 2D convolution with depthwise separable convolution. This is equivalent to:

    .. code-block:: python

        xf = torch.fft.rfft2(x, s=(2*x.shape[-2], 2*x.shape[-1]))
        wf = torch.fft.rfft2(weight, s=(2*x.shape[-2], 2*x.shape[-1]))
        yf = xf * wf
        y = torch.fft.irfft2(yf, s=(2*x.shape[-2], 2*x.shape[-1]))
        return y[
            ...,
            x.shape[-2]//2 : x.shape[-2]//2 + x.shape[-2],
            x.shape[-1]//2 : x.shape[-1]//2 + x.shape[-1]
        ]

    Args:
        x (torch.Tensor): Input tensor of shape ``(batch_size, hidden_dim, x_dim_seq, y_dim_seq)``.
        weight (torch.Tensor): Weight tensor of shape ``(hidden_dim, x_dim_kernel, y_dim_kernel)``.

    Returns:
        torch.Tensor: Output tensor of shape ``(batch_size, hidden_dim, x_dim_seq, y_dim_seq)``.

    Example:
        .. code-block:: python

            batch_size, hidden_dim, x_dim_seq, y_dim_seq = 2, 4, 10, 10
            x = torch.randn(batch_size, hidden_dim, x_dim_seq, y_dim_seq, device="cuda")
            weight = torch.randn(hidden_dim, x_dim_seq, y_dim_seq, device="cuda")
            y = fft_conv2d(x, weight)
            print(y.shape)  # torch.Size([2, 4, 10, 10])

    .. note::
        The kernel shape should match the input shape.

    """
    is_padding_needed = False
    if x.shape[-1] % 2 == 1:
        x = F.pad(x, (0, 1))
        is_padding_needed = True
        weight = F.pad(weight, (0, 1))
    x = x.contiguous()
    weight = weight.contiguous()
    assert x.shape[-1] == weight.shape[-1] and x.shape[-2] == weight.shape[-2]
    y = torch.ops.subquadratic_ops_torch.fft_conv2d_fwd_primitive(x, weight)[0]
    return y if not is_padding_needed else y[..., :-1]
