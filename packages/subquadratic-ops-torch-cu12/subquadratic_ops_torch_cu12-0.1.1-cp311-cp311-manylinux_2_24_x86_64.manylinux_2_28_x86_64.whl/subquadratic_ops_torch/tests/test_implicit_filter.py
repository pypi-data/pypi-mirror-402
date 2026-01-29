# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import math

import pytest
import torch
import warp as wp

from subquadratic_ops_torch.implicit_filter import implicit_filter
from subquadratic_ops_torch.tests.utils import ref_implicit_filter

wp.build.clear_kernel_cache()


@pytest.mark.parametrize("dtype", [torch.float64, torch.float32])
@pytest.mark.parametrize("L", [128, 256, 1024, 8192, 8192 + 3])
@pytest.mark.parametrize("order", [1, 4, 16])
@pytest.mark.parametrize("d_model", [128, 256, 1024, 8192])
def test_implicit_filter(dtype, order, L, d_model):
    torch.manual_seed(9)
    t = torch.arange(L, dtype=dtype).cuda().view(1, 1, -1)
    gamma_min = 0.01
    gamma_max = 0.1
    gamma = torch.rand(d_model, order, dtype=dtype) * (gamma_max - gamma_min) + gamma_min
    gamma = gamma.cuda().log()

    R = 1e-1 * torch.randn(d_model, order, dtype=dtype).cuda() / math.sqrt(order)
    p = -torch.ones(d_model, order, dtype=dtype).cuda()

    logp = -torch.exp(p)
    glogp = logp * torch.exp(gamma)

    y_ref = ref_implicit_filter(glogp, R, t)

    y = implicit_filter(glogp, R, L)

    torch.testing.assert_close(y, y_ref)


@pytest.mark.parametrize("dtype", [torch.float64])
@pytest.mark.parametrize("L", [4, 32])
@pytest.mark.parametrize("order", [1, 4, 16])
@pytest.mark.parametrize("d_model", [1, 8, 32])
def test_implicit_filter_bwd(dtype, order, L, d_model):
    torch.manual_seed(9)
    gamma_min = 0.01
    gamma_max = 0.1
    gamma = torch.rand(d_model, order, dtype=dtype) * (gamma_max - gamma_min) + gamma_min
    gamma = gamma.cuda().log()

    R = 1e-1 * torch.randn(d_model, order, dtype=dtype).cuda() / math.sqrt(order)
    p = -torch.ones(d_model, order, dtype=dtype).cuda()
    logp = -torch.exp(p)
    glogp = logp * torch.exp(gamma).detach().clone()
    glogp.requires_grad = True
    R.requires_grad = True

    torch.autograd.gradcheck(implicit_filter, (glogp, R, L))
