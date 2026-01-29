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


def short_fft_is_available(filter_length: int, dtype: torch.dtype) -> bool:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")

    if dtype == torch.float64:
        return filter_length <= 4096

    if get_cuda_arch() < 900:
        return filter_length <= 8192
    else:
        return filter_length <= 16384


def scratch_space_size(filter_length: int) -> Tuple[int, int, int]:
    if filter_length & (filter_length - 1) != 0:
        raise ValueError(f"Filter length {filter_length} is not a power of 2")
    fft_size = filter_length * 2
    bit_length = fft_size.bit_length() - 1
    m = (bit_length + 1) // 2
    n = bit_length - m

    return 1 << m, 1 << n, fft_size


def compatible_filter_length(filter_length: int) -> int:
    return max(128, next_pow2(filter_length))


@torch.library.custom_op(
    "subquadratic_ops_torch::fft_causal_conv1d_fwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor, weight: Tensor) -> Tensor:
    if x.dim() != 3 or weight.dim() != 2 or x.shape[-1] % weight.shape[-1] != 0:
        raise ValueError(f"Input and weights must be 3D and 2D tensors, {x.shape}, {weight.shape}, and x % weight should be 0, but got {x.shape[-1] % weight.shape[-1]}")

    x = x.contiguous()
    weight = weight.contiguous()
    y = torch.empty((x.shape[0], x.shape[1], x.shape[2]), device=x.device, dtype=x.dtype)

    arch = get_cuda_arch(x.device.index)
    module = get_module("fft_causal_conv1d_fwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id
    module(y.detach(), x.detach(), weight.detach(), arch, stream_id)

    return y


@torch.library.register_fake("subquadratic_ops_torch::fft_causal_conv1d_fwd_primitive")
def _(x: Tensor, weight: Tensor) -> Tensor:
    return torch.empty_like(x)


@torch.library.custom_op(
    "subquadratic_ops_torch::fft_causal_conv1d_bwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(grad_out: Tensor, x: Tensor, weight: Tensor) -> List[Tensor]:
    if x.dim() != 3 or weight.dim() != 2:
        raise ValueError(f"Input and weights must be 3D and 2D tensors, {x.shape}, {weight.shape}")

    grad_out_y = grad_out
    grad_x = torch.empty(x.shape, device=x.device, dtype=x.dtype)
    grad_weight = torch.zeros(weight.shape, device=x.device, dtype=x.dtype)
    arch = get_cuda_arch(x.device.index)

    x = x.contiguous()
    weight = weight.contiguous()
    grad_out_y = grad_out_y.contiguous()

    module = get_module("fft_causal_conv1d_bwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id

    module(
        grad_x.detach(),
        grad_weight.detach(),
        grad_out_y.detach(),
        x.detach(),
        weight.detach(),
        arch,
        stream_id,
    )

    return [grad_x, grad_weight]


@torch.library.register_fake("subquadratic_ops_torch::fft_causal_conv1d_bwd_primitive")
def _(grad_out: Tensor, x: Tensor, weight: Tensor) -> List[Tensor]:
    return [torch.empty_like(x), torch.empty_like(weight)]


def fft_causal_conv1d_fwd_setup_fwd_context(ctx, inputs, output):
    (x, weight) = inputs
    ctx.save_for_backward(x, weight)  # Save y_gated along with other tensors


@torch.compiler.allow_in_graph
def fft_causal_conv1d_fwd(*args):
    return torch.ops.subquadratic_ops_torch.fft_causal_conv1d_fwd_primitive(*args)


@torch.compiler.allow_in_graph
def fft_causal_conv1d_bwd(ctx, grad_out):
    x, weight = ctx.saved_tensors

    dx, dw = torch.ops.subquadratic_ops_torch.fft_causal_conv1d_bwd_primitive(grad_out, x, weight)
    return dx, dw


torch.library.register_autograd(
    "subquadratic_ops_torch::fft_causal_conv1d_fwd_primitive",
    fft_causal_conv1d_bwd,
    setup_context=fft_causal_conv1d_fwd_setup_fwd_context,
)


@torch.library.custom_op(
    "subquadratic_ops_torch::long_fft_causal_conv1d_fwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor, weight: Tensor) -> List[Tensor]:
    m, n, _ = scratch_space_size(weight.shape[-1])
    intermediate_size = 2 * (m // 2 + 1) * n
    batch_size, feat_dim, seq_length = x.shape

    x = x.contiguous()
    weight = weight.contiguous()

    inter_dtype = torch.float32 if x.element_size() <= 4 else torch.float64

    inter_x1 = torch.empty((batch_size, feat_dim, intermediate_size), device=x.device, dtype=inter_dtype)
    inter_filter = torch.empty((feat_dim, intermediate_size), device=x.device, dtype=inter_dtype)

    inter_x0 = torch.empty((batch_size, feat_dim, intermediate_size), device=x.device, dtype=inter_dtype)

    module = get_module("long_fft_causal_conv1d_fwd", [x.dtype])
    arch = get_cuda_arch(x.device.index)
    stream_id = torch.cuda.current_stream(x.device).stream_id
    y = torch.empty((batch_size, feat_dim, seq_length), device=x.device, dtype=x.dtype)

    module(
        y.detach(),
        x.detach(),
        weight.detach(),
        inter_x0.detach(),
        inter_x1.detach(),
        inter_filter.detach(),
        arch,
        stream_id,
    )

    return [y, inter_x0, inter_x1, inter_filter]


@torch.library.register_fake("subquadratic_ops_torch::long_fft_causal_conv1d_fwd_primitive")
def _(x: Tensor, weight: Tensor) -> List[Tensor]:
    m, n, _ = scratch_space_size(weight.shape[-1])
    dtype = torch.float32 if x.element_size() <= 4 else torch.float64

    intermediate_size = 2 * (m // 2 + 1) * n
    return [
        torch.empty_like(x),
        torch.empty((x.shape[0], x.shape[1], intermediate_size), device=x.device, dtype=dtype),
        torch.empty((x.shape[0], x.shape[1], intermediate_size), device=x.device, dtype=dtype),
        torch.empty((x.shape[1], intermediate_size), device=x.device, dtype=dtype),
    ]


@torch.library.custom_op(
    "subquadratic_ops_torch::long_fft_causal_conv1d_bwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(grad_out: Tensor, x: Tensor, weight: Tensor, inter_x: Tensor, inter_filter: Tensor) -> List[Tensor]:
    m, n, _ = scratch_space_size(weight.shape[-1])
    intermediate_size = 2 * (m // 2 + 1) * n
    batch_size, feat_dim, seq_length = x.shape

    grad_x = torch.empty((batch_size, feat_dim, seq_length), device=x.device, dtype=x.dtype)
    grad_weight = torch.empty((feat_dim, seq_length), device=x.device, dtype=x.dtype)

    dtype = torch.float32 if x.element_size() <= 4 else torch.float64

    x = x.contiguous()
    weight = weight.contiguous()
    grad_out = grad_out.contiguous()

    inter_dx = torch.empty((batch_size, feat_dim, intermediate_size), device=x.device, dtype=dtype)
    inter_dw = torch.empty((feat_dim, intermediate_size), device=x.device, dtype=dtype)

    module = get_module("long_fft_causal_conv1d_bwd", [x.dtype])
    arch = get_cuda_arch(x.device.index)
    stream_id = torch.cuda.current_stream(x.device).stream_id

    module(
        grad_x.detach(),
        grad_weight.detach(),
        grad_out.detach(),
        inter_x.detach(),
        inter_filter.detach(),
        inter_dx.detach(),
        inter_dw.detach(),
        arch,
        stream_id,
    )

    return [grad_x, grad_weight]


@torch.library.register_fake("subquadratic_ops_torch::long_fft_causal_conv1d_bwd_primitive")
def _(grad_out: Tensor, x: Tensor, weight: Tensor, inter_x: Tensor, inter_filter: Tensor) -> List[Tensor]:
    return [torch.empty_like(x), torch.empty_like(weight)]


@torch.compiler.allow_in_graph
def long_fft_causal_conv1d_fwd(*args):
    return torch.ops.subquadratic_ops_torch.long_fft_causal_conv1d_fwd_primitive(*args)


@torch.compiler.allow_in_graph
def long_fft_causal_conv1d_bwd(ctx, grad_out):
    x, weight, inter_x, inter_filter = ctx.saved_tensors

    grad_out_y = grad_out[0]
    grad_out_y = grad_out_y.contiguous()

    dx, dw = torch.ops.subquadratic_ops_torch.long_fft_causal_conv1d_bwd_primitive(grad_out_y, x, weight, inter_x, inter_filter)
    return dx, dw


def long_fft_causal_conv1d_fwd_setup_fwd_context(ctx, inputs, output):
    (x, weight) = inputs
    (_, inter_x, _, inter_filter) = output
    ctx.save_for_backward(x, weight, inter_x, inter_filter)


torch.library.register_autograd(
    "subquadratic_ops_torch::long_fft_causal_conv1d_fwd_primitive",
    long_fft_causal_conv1d_bwd,
    setup_context=long_fft_causal_conv1d_fwd_setup_fwd_context,
)


def fft_causal_conv1d(x: Tensor, weight: Tensor) -> Tensor:
    r"""
    FFT Causal Conv1d performs convolution in a causal manner, using FFT routines instead of direct summation.

    .. note::
        This is more performant than :func:`~subquadratic_ops_torch.causal_conv1d.causal_conv1d` for kernel sizes >= 128.

    Args:
        x (torch.Tensor): Input tensor of shape ``(batch_size, dim, seq_len)``.
        weight (torch.Tensor): Weight tensor of shape ``(dim, kernel_size)``.

    Returns:
        torch.Tensor: Output tensor of shape ``(batch_size, dim, seq_len)``.

    .. note::
        This is more performant than causal_conv1d for kernel sizes >= 128.
        The user might or might not need to pad the weights (when kernel size is smaller than the input sequence length) to improve performance.

    Example:
        .. code-block:: python

            batch_size, dim, seq_len, kernel_size = 2, 4, 10, 3
            x = torch.randn(batch_size, dim, seq_len, device="cuda")
            weight = torch.randn(dim, kernel_size, device="cuda")
            y = fft_causal_conv1d(x, weight)
            print(y.shape)  # torch.Size([2, 4, 10])

    """
    is_padding_needed = False
    weight_length = weight.shape[-1]

    if short_fft_is_available(weight_length, x.dtype):
        filter_length = compatible_filter_length(weight_length)
        if weight_length != filter_length:
            weight = F.pad(weight, (0, filter_length - weight_length))
        seq_length = x.shape[-1]

        if seq_length < filter_length or seq_length % filter_length != 0:
            is_padding_needed = True
            seq_length_final = ((seq_length + filter_length - 1) // filter_length) * filter_length
            x = F.pad(x, (0, seq_length_final - seq_length))
            diff = seq_length_final - seq_length
            seq_length = x.shape[-1]

        y = torch.ops.subquadratic_ops_torch.fft_causal_conv1d_fwd_primitive(x, weight)
        return y if not is_padding_needed else y[..., :-diff]
    else:
        filter_length = max(
            compatible_filter_length(weight_length),
            compatible_filter_length(x.shape[-1]),
        )
        seq_length = x.shape[-1]

        if weight_length != filter_length:
            weight = F.pad(weight, (0, filter_length - weight_length))

        if seq_length != filter_length:
            x = F.pad(x, (0, filter_length - seq_length))
            is_padding_needed = True
            diff = filter_length - seq_length
        y = torch.ops.subquadratic_ops_torch.long_fft_causal_conv1d_fwd_primitive(x, weight)[0]
        return y if not is_padding_needed else y[..., :-diff]
