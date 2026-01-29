# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import pytest
import torch
from utils import ref_fft_conv2d_depthwise

from subquadratic_ops_torch.fft_conv2d import fft_conv2d

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False


torch.manual_seed(9)


@pytest.mark.parametrize("dtype", ["float32", "float64"])
@pytest.mark.parametrize("in_dim_x", [16, 32, 64, 128, 256, 512, 1024, 2048])
@pytest.mark.parametrize("in_dim_y", [16, 32, 64, 128, 256, 512, 1024, 2048])
@pytest.mark.parametrize("hidden_dim", [3, 4])
def test_fft_conv2d(in_dim_x, in_dim_y, hidden_dim, dtype):
    batch_size = 2
    dtype = getattr(torch, dtype)

    x = 2 * torch.rand(batch_size, hidden_dim, in_dim_x, in_dim_y).cuda().to(dtype) - 1
    weights = 2 * torch.rand(hidden_dim, in_dim_x, in_dim_y).cuda().to(dtype) - 1

    y_predicted = fft_conv2d(x, weights)
    y_actual = ref_fft_conv2d_depthwise(x, weights)
    atol = 1e-5 if dtype == torch.float32 else 1e-7
    rtol = 1e-5 if dtype == torch.float32 else 1e-7
    print(in_dim_x, in_dim_y, hidden_dim, dtype)
    max_val = y_predicted.max()
    min_val = y_predicted.min()
    y_predicted = (y_predicted - min_val) / (max_val - min_val)
    y_actual = (y_actual - min_val) / (max_val - min_val)
    torch.testing.assert_close(y_predicted, y_actual, atol=atol, rtol=rtol)


@pytest.mark.parametrize("dtype", ["float64"])
@pytest.mark.parametrize("in_dim", [16, 32, 64])
@pytest.mark.parametrize("hidden_dim", [1])
def test_fft_conv2d_bwd(in_dim, hidden_dim, dtype):
    batch_size = 1
    dtype = getattr(torch, dtype)

    x = torch.randn(batch_size, hidden_dim, in_dim, in_dim, dtype=dtype).cuda()
    weights = torch.randn(hidden_dim, in_dim, in_dim, dtype=dtype).cuda()

    x.requires_grad = True
    weights.requires_grad = True

    torch.autograd.gradcheck(fft_conv2d, (x, weights))
