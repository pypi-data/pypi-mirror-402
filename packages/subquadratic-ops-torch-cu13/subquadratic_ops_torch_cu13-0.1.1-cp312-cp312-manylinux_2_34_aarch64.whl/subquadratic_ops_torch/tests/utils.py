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
from torch import nn


class Conv1DModel(nn.Module):
    def __init__(self, in_dim, width, dtype, skip_bias=False, conv_bias=False):
        super(Conv1DModel, self).__init__()
        self.in_dim = in_dim
        self.conv = nn.Conv1d(
            in_dim,
            in_dim,
            width,
            padding=width - 1,
            groups=in_dim,
            bias=conv_bias,
            dtype=dtype,
            device="cuda:0",
        )
        self.width = width
        self.weight = self.conv.weight.reshape(-1, width)
        if skip_bias:
            self.skip_bias = nn.Parameter(torch.zeros(in_dim, dtype=dtype, device="cuda:0").reshape(1, -1, 1))
        else:
            self.skip_bias = None

    def forward(self, x):
        seqlen = x.shape[-1]
        out = self.conv(x)
        return out[..., :seqlen]


def ref_fft_causal_conv1d(x, weight):
    fft_size = x.shape[-1] * 2
    xf = torch.fft.rfft(x, dim=-1, n=fft_size)
    weightf = torch.fft.rfft(weight.unsqueeze(0), dim=-1, n=fft_size)
    yf = xf * weightf / fft_size
    y = torch.fft.irfft(yf, dim=-1, n=fft_size, norm="forward")
    return y[..., : x.shape[-1]]


def ref_implicit_filter(glogp, R, t):
    h = torch.exp(glogp[..., None] * t)
    h = torch.einsum("do,dot->dt", R, h)
    return h


def ref_fft_conv2d_depthwise(input_tensor: torch.Tensor, kernel: torch.Tensor) -> torch.Tensor:
    """
    Computes 2D depthwise convolution with 'same' padding using FFT.

    Args:
        input_tensor (torch.Tensor): Input tensor of shape [B, H, X_in, Y_in].
        kernel (torch.Tensor): Kernel tensor of shape [H, K_x, K_y].

    Returns:
        torch.Tensor: Output tensor with shape [B, H, X_in, Y_in].
    """
    B, H, X_in, Y_in = input_tensor.shape
    h_k, K_x, K_y = kernel.shape
    assert X_in == K_x and Y_in == K_y, "Input and kernel must have the same shape."
    assert H == h_k, "Input and kernel must have the same number of channels (H)."

    # 1. Determine FFT size for linear convolution (same as 'valid' version)
    fft_shape = (2 * X_in, 2 * Y_in)

    # 2. Compute 2D FFT of the input and kernel
    input_fft = torch.fft.rfft2(input_tensor, s=fft_shape)
    kernel_fft = torch.fft.rfft2(kernel, s=fft_shape)

    # 3. Apply the Convolution Theorem
    conv_fft = input_fft * kernel_fft.unsqueeze(0)

    # 4. Compute the inverse FFT to get the full convolution result
    output_full = torch.fft.irfft2(conv_fft, s=fft_shape)

    # 5. Crop the result to the 'same' size
    # The output should have the same size as the input: (X_in, Y_in)
    # To achieve this, we crop from the full convolution result,
    # starting at an offset that centers the output.
    crop_start_h = (K_x) // 2
    crop_start_w = (K_y) // 2

    output = output_full[:, :, crop_start_h : crop_start_h + X_in, crop_start_w : crop_start_w + Y_in]
    return output
