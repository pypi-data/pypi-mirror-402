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
from utils import Conv1DModel

from subquadratic_ops_torch.b2b_causal_conv1d import b2b_causal_conv1d

torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False


torch.manual_seed(9)

dtype_fp64 = torch.float64
dtype_fp32 = torch.float32
dtype_bf16 = torch.bfloat16


def model(x, model_proj, model_mixer):
    xv = model_proj(x)
    z = xv[:, 1::3, :] * xv[:, 2::3, :]
    y = model_mixer(z) + model_mixer.skip_bias * z
    return y * xv[:, ::3, :]


@pytest.mark.parametrize("dtype", [dtype_fp64])
@pytest.mark.parametrize("in_dim", [1024, 4096])
@pytest.mark.parametrize("seq_dim", [8192, 510])
@pytest.mark.parametrize("proj_conv_width", [3, 4])
@pytest.mark.parametrize("mixer_conv_width", [7, 64])
def test_b2b_causal_conv1d(in_dim, seq_dim, proj_conv_width, mixer_conv_width, dtype):
    model_proj = Conv1DModel(in_dim * 3, proj_conv_width, dtype).cuda()
    model_mixer = Conv1DModel(in_dim, mixer_conv_width, dtype, skip_bias=True).cuda()
    batch_size = 2

    x = torch.randn(batch_size, in_dim * 3, seq_dim).cuda().to(dtype_bf16)
    weights_proj = torch.randn(in_dim * 3, proj_conv_width).cuda().to(dtype_bf16)
    weights_mixer = torch.randn(in_dim, mixer_conv_width).cuda().to(dtype_bf16)
    skip_bias = torch.randn(in_dim).cuda().to(dtype_bf16)

    model_proj.weight.data = weights_proj.to(dtype)
    model_proj.conv.weight.data = weights_proj.reshape(in_dim * 3, 1, proj_conv_width).to(dtype)

    model_mixer.weight.data = weights_mixer.to(dtype)
    model_mixer.conv.weight.data = weights_mixer.reshape(in_dim, 1, mixer_conv_width).to(dtype)
    model_mixer.skip_bias.data = skip_bias.to(dtype).reshape(1, -1, 1)
    y_predicted = b2b_causal_conv1d(
        x.to(dtype),
        weights_proj.to(dtype),
        weights_mixer.to(dtype),
        skip_bias.to(dtype),
    )
    y_actual = model(x.to(dtype), model_proj, model_mixer)

    torch.testing.assert_close(y_predicted.to(dtype), y_actual.to(dtype), atol=1e-6, rtol=1e-6)


@pytest.mark.parametrize("dtype", [dtype_fp64])
@pytest.mark.parametrize("in_dim", [4])
@pytest.mark.parametrize("seq_dim", [8])
@pytest.mark.parametrize("proj_conv_width", [3])
@pytest.mark.parametrize("mixer_conv_width", [7])
def test_b2b_causal_conv1d_bwd(in_dim, seq_dim, proj_conv_width, mixer_conv_width, dtype):
    batch_size = 2

    x = torch.randn(batch_size, in_dim * 3, seq_dim).cuda().to(dtype_bf16)
    weights_proj = torch.randn(in_dim * 3, proj_conv_width).cuda().to(dtype_bf16)
    weights_mixer = torch.randn(in_dim, mixer_conv_width).cuda().to(dtype_bf16)
    skip_bias = torch.randn(in_dim).cuda().to(dtype_bf16)

    x.requires_grad = True
    weights_proj.requires_grad = True
    weights_mixer.requires_grad = True
    skip_bias.requires_grad = True

    torch.autograd.gradcheck(
        b2b_causal_conv1d,
        (
            x.to(dtype),
            weights_proj.to(dtype),
            weights_mixer.to(dtype),
            skip_bias.to(dtype),
        ),
    )
