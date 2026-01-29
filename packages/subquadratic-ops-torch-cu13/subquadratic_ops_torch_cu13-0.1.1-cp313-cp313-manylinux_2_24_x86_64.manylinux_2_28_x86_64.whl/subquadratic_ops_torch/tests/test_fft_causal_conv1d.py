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
from torch.nn import functional as F
from utils import ref_fft_causal_conv1d as fft_causal_conv1d_ref

from subquadratic_ops_torch.fft_causal_conv1d import fft_causal_conv1d

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False


torch.manual_seed(9)

dtype_fp64 = torch.float64
dtype_fp32 = torch.float32
dtype_bf16 = torch.bfloat16


@pytest.mark.parametrize("dtype", [dtype_fp32])
@pytest.mark.parametrize("in_dim", [16, 32])
@pytest.mark.parametrize("seq_dim", [256, 128, 512, 200, 1239])
@pytest.mark.parametrize("conv_width", [128, 256, 512, 1024, 2048])
def test_fft_causal_conv1d(in_dim, seq_dim, conv_width, dtype):
    batch_size = 2

    x = torch.rand(batch_size, in_dim, seq_dim).cuda()

    weights = torch.rand(in_dim, conv_width).cuda()

    y_predicted = fft_causal_conv1d(x.to(dtype), weights.to(dtype))
    if seq_dim < conv_width:
        x = F.pad(x, (0, conv_width - seq_dim))

    if seq_dim % conv_width != 0:
        padding = conv_width * ((seq_dim + conv_width - 1) // conv_width) - seq_dim
        x = F.pad(x, (0, padding))
    y_actual = fft_causal_conv1d_ref(x.to(dtype), weights.to(dtype))[..., :seq_dim]

    torch.testing.assert_close(y_predicted.to(dtype), y_actual.to(dtype), atol=1e-3, rtol=1e-3)


@pytest.mark.parametrize("dtype", [dtype_fp64, dtype_fp32])
@pytest.mark.parametrize("in_dim", [1, 16])
@pytest.mark.parametrize("seq_dim", [128, 256, 512, 1024, 2039])
@pytest.mark.parametrize("conv_width", [128, 256, 512, 1024, 2048])
def test_fft_causal_conv1d_grad(in_dim, seq_dim, conv_width, dtype):
    batch_size = 4
    x = torch.rand(batch_size, in_dim, seq_dim, dtype=dtype).cuda()
    dy = torch.randn_like(x)
    weights = torch.rand(in_dim, conv_width, dtype=dtype).cuda()
    x.requires_grad = True
    weights.requires_grad = True

    y_predicted = fft_causal_conv1d(x, weights)
    dx_predicted, dw_predicted = torch.autograd.grad(y_predicted, (x, weights), dy)
    x_padded = x
    if seq_dim < conv_width:
        x_padded = F.pad(x, (0, conv_width - seq_dim))

    if seq_dim % conv_width != 0:
        padding = conv_width * ((seq_dim + conv_width - 1) // conv_width) - seq_dim
        x_padded = F.pad(x, (0, padding))
    y_actual = fft_causal_conv1d_ref(x_padded, weights)[..., :seq_dim]
    dx_actual, dw_actual = torch.autograd.grad(y_actual, (x, weights), dy)

    torch.testing.assert_close(dx_actual, dx_predicted, atol=1e-4, rtol=1e-4)
    torch.testing.assert_close(dw_actual, dw_predicted, atol=1e-4, rtol=1e-4)


@pytest.mark.parametrize("dtype", [dtype_fp64])
@pytest.mark.parametrize("in_dim", [2])
@pytest.mark.parametrize("seq_dim", [128, 256])
@pytest.mark.parametrize("conv_width", [128, 256])
def test_fft_causal_conv1d_bwd(in_dim, seq_dim, conv_width, dtype):
    batch_size = 2
    x = torch.rand(batch_size, in_dim, seq_dim, dtype=dtype).cuda()
    weights = torch.rand(in_dim, conv_width, dtype=dtype).cuda()
    x.requires_grad = True
    weights.requires_grad = True

    torch.autograd.gradcheck(fft_causal_conv1d, (x, weights), eps=1e-1, atol=1e-3, rtol=1e-3)


@pytest.mark.parametrize("dtype", [dtype_fp32])
@pytest.mark.parametrize("in_dim", [1, 4])
@pytest.mark.parametrize("seq_dim", [256**2, 512**2, 1024**2])
def test_long_fft_causal_conv1d(in_dim, seq_dim, dtype):
    batch_size = 2

    x = torch.randn(batch_size, in_dim, seq_dim, dtype=dtype).cuda()

    weights = torch.randn(in_dim, seq_dim, dtype=dtype).cuda()

    y_predicted = fft_causal_conv1d(x, weights)
    y_actual = fft_causal_conv1d_ref(x, weights)[..., :seq_dim]

    torch.testing.assert_close(y_predicted, y_actual, atol=1e-2, rtol=1e-2)


@pytest.mark.parametrize("dtype", [dtype_fp64, dtype_fp32])
@pytest.mark.parametrize("in_dim", [1, 16])
@pytest.mark.parametrize("seq_dim", [256**2, 512**2, 1024**2])
def test_long_fft_causal_conv1d_grad(in_dim, seq_dim, dtype):
    batch_size = 4
    x = torch.randn(batch_size, in_dim, seq_dim, dtype=dtype).cuda()
    weights = torch.randn(in_dim, seq_dim, dtype=dtype).cuda()
    x.requires_grad = True
    weights.requires_grad = True

    dy = torch.randn_like(x)

    y_predicted = fft_causal_conv1d(x, weights)
    dx_predicted, dw_predicted = torch.autograd.grad(y_predicted, (x, weights), dy)

    y_actual = fft_causal_conv1d_ref(x, weights)[..., :seq_dim]
    dx_actual, dw_actual = torch.autograd.grad(y_actual, (x, weights), dy)

    torch.testing.assert_close(dx_actual, dx_predicted, atol=1e-2, rtol=1e-2)
    torch.testing.assert_close(dw_actual, dw_predicted, atol=1e-2, rtol=1e-2)
