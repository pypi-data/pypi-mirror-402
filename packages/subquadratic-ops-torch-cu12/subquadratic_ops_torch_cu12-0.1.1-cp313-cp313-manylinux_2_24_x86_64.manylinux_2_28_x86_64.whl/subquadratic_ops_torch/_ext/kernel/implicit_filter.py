# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from typing import Final

import warp as wp

from subquadratic_ops_torch._ext.utils import get_warp_dtype

IMPLICIT_FILTER_L_SEG_SIZE: Final[int] = 512


def generate_implicit_filter_kernels(order: int, dtype: str, fast_math: bool = True):
    wpdtype = get_warp_dtype(dtype)

    def implicit_filter_fwd_kernel(
        glogp: wp.array(dtype=wpdtype, ndim=2),
        R: wp.array(dtype=wpdtype, ndim=2),
        h: wp.array(dtype=wpdtype, ndim=2),
        L: int,
    ):
        id_d, id_l, tidx = wp.tid()
        tile_glogp = wp.tile_load(glogp[id_d], shape=(order), offset=(0))
        tile_r = wp.tile_load(R[id_d], shape=(order), offset=(0))

        for id_l2 in range(4):
            id_l_offset = id_l * 4 + id_l2
            id_output = id_l_offset * 256 + tidx
            if id_output < L:
                tmp = wpdtype(0)
                for id_o in range(order):
                    tmp += wp.exp(tile_glogp[id_o] * wpdtype(id_output)) * tile_r[id_o]

                h[id_d, id_output] = tmp

    def implicit_filter_bwd_kernel(
        glogp: wp.array(dtype=wpdtype, ndim=2),
        R: wp.array(dtype=wpdtype, ndim=2),
        dh: wp.array(dtype=wpdtype, ndim=2),
        dlogp: wp.array(dtype=wpdtype, ndim=2),
        dR: wp.array(dtype=wpdtype, ndim=2),
        L: int,
    ):
        seg_l, id_d, id_o = wp.tid()
        dR_reg = wpdtype(0)
        dlogp_reg = wpdtype(0)
        R_reg = R[id_d, id_o]
        glogp_reg = glogp[id_d, id_o]

        for i in range(IMPLICIT_FILTER_L_SEG_SIZE):
            id_l = seg_l * IMPLICIT_FILTER_L_SEG_SIZE + i
            dh_reg = wp.where(
                id_l >= L,
                wpdtype(0),
                wp.exp(glogp_reg * wpdtype(id_l)) * dh[id_d, id_l],
            )
            dR_reg += dh_reg
            dlogp_reg += dh_reg * R_reg * wpdtype(id_l)
        wp.atomic_add(dR, id_d, id_o, dR_reg)
        wp.atomic_add(dlogp, id_d, id_o, dlogp_reg)

    fwd_key = f"implicit_filter_{order}_fwd_{dtype.split('.')[-1]}"
    bwd_key = f"implicit_filter_bwd_{dtype.split('.')[-1]}"

    fwd_module = wp.context.Module(fwd_key, loader=None)
    bwd_module = wp.context.Module(bwd_key, loader=None)

    fwd_module.options["fast_math"] = fast_math
    fwd_module.options["enable_backward"] = False
    bwd_module.options["fast_math"] = fast_math
    bwd_module.options["enable_backward"] = False

    fwd_kernel = wp.Kernel(implicit_filter_fwd_kernel, key=fwd_key, module=fwd_module)

    bwd_kernel = wp.Kernel(implicit_filter_bwd_kernel, key=bwd_key, module=bwd_module)

    return fwd_kernel, bwd_kernel
