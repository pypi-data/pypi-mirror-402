# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import List

import torch
from torch import Tensor

from subquadratic_ops_torch.utils import get_module


@torch.library.custom_op(
    "subquadratic_ops_torch::b2b_causal_conv1d_fwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(x: Tensor, weight_proj: Tensor, weight_mixer: Tensor, skip_bias: Tensor) -> List[Tensor]:
    if x.dim() != 3 or weight_proj.dim() != 2 or weight_mixer.dim() != 2:
        raise ValueError(f"Input and weights must be 3D and 2D tensors, {x.shape}, {weight_proj.shape}, {weight_mixer.shape}")
    if x.shape[1] % 3 != 0 or x.shape[1] != weight_proj.shape[0] or x.shape[1] != 3 * weight_mixer.shape[0]:
        raise ValueError(
            f"Input width must be divisible by 3, and equal to the number of rows in weight_proj and 3 times the number of rows in weight_mixer, got {x.shape[1]}, {weight_proj.shape[0]}, {weight_mixer.shape[0]}"  # noqa: E501
        )

    if skip_bias.dim() != 1 or skip_bias.shape[0] != x.shape[1] // 3:
        raise ValueError(f"Skip bias must be a 1D tensor with the same number of rows as the input, got {skip_bias.shape}")

    x = x.contiguous()
    weight_proj = weight_proj.contiguous()
    weight_mixer = weight_mixer.contiguous()
    skip_bias = skip_bias.contiguous()
    y = torch.empty((x.shape[0], x.shape[1] // 3, x.shape[2]), device=x.device, dtype=x.dtype)
    y_gated = torch.empty((x.shape[0], x.shape[1] // 3, x.shape[2]), device=x.device, dtype=x.dtype)

    module = get_module("b2b_causal_conv1d_fwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id
    module(
        y.detach(),
        y_gated.detach(),
        x.detach(),
        weight_proj.detach(),
        weight_mixer.detach(),
        skip_bias.detach(),
        stream_id,
    )

    return [y, y_gated]


@torch.library.register_fake("subquadratic_ops_torch::b2b_causal_conv1d_fwd_primitive")
def _(x: Tensor, weight_proj: Tensor, weight_mixer: Tensor, skip_bias: Tensor) -> List[torch.Tensor]:
    return [
        torch.empty((x.shape[0], x.shape[1] // 3, x.shape[2]), device=x.device, dtype=x.dtype),
        torch.empty((x.shape[0], x.shape[1] // 3, x.shape[2]), device=x.device, dtype=x.dtype),
    ]


@torch.library.custom_op(
    "subquadratic_ops_torch::b2b_causal_conv1d_bwd_primitive",
    mutates_args=(),
    device_types="cuda",
)
def _(
    grad_out: List[torch.Tensor],
    x: Tensor,
    weight_proj: Tensor,
    weight_mixer: Tensor,
    skip_bias: Tensor,
    y: Tensor,
) -> List[torch.Tensor]:
    if x.dim() != 3 or weight_proj.dim() != 2 or weight_mixer.dim() != 2:
        raise ValueError(f"Input and weights must be 3D and 2D tensors, {x.shape}, {weight_proj.shape}, {weight_mixer.shape}")
    if skip_bias.dim() != 1 or skip_bias.shape[0] != x.shape[1] // 3:
        raise ValueError(f"Skip bias must be a 1D tensor with the same number of rows as the input, got {skip_bias.shape}")

    grad_out_y, grad_out_y_gated = grad_out

    grad_x = torch.empty(x.shape, device=x.device, dtype=x.dtype)
    grad_weight_proj = torch.zeros(
        weight_proj.shape,
        device=x.device,
        dtype=torch.float32 if x.dtype.itemsize == 2 else x.dtype,
    )
    grad_weight_mixer = torch.zeros(
        weight_mixer.shape,
        device=x.device,
        dtype=torch.float32 if x.dtype.itemsize == 2 else x.dtype,
    )
    grad_skip_bias = torch.zeros(
        skip_bias.shape,
        device=x.device,
        dtype=torch.float32 if x.dtype.itemsize == 2 else x.dtype,
    )
    module = get_module("b2b_causal_conv1d_bwd", [x.dtype])
    stream_id = torch.cuda.current_stream(x.device).stream_id

    grad_out_y_gated = grad_out_y_gated.contiguous()
    x = x.contiguous()
    weight_proj = weight_proj.contiguous()
    weight_mixer = weight_mixer.contiguous()
    skip_bias = skip_bias.contiguous()
    y = y.contiguous()

    module(
        grad_x.detach(),
        grad_weight_proj.detach(),
        grad_weight_mixer.detach(),
        grad_skip_bias.detach(),
        grad_out_y_gated.detach(),
        y.detach(),
        x.detach(),
        weight_proj.detach(),
        weight_mixer.detach(),
        skip_bias.detach(),
        stream_id,
    )

    return [
        grad_x,
        grad_weight_proj.to(x.dtype),
        grad_weight_mixer.to(x.dtype),
        grad_skip_bias.to(x.dtype),
    ]


@torch.library.register_fake("subquadratic_ops_torch::b2b_causal_conv1d_bwd_primitive")
def _(
    grad_out: List[torch.Tensor],
    x: Tensor,
    weight_proj: Tensor,
    weight_mixer: Tensor,
    skip_bias: Tensor,
    y: Tensor,
) -> List[torch.Tensor]:
    return [
        torch.empty_like(x),
        torch.empty_like(weight_proj),
        torch.empty_like(weight_mixer),
        torch.empty_like(skip_bias),
    ]


def b2b_causal_conv1d_fwd_setup_fwd_context(ctx, inputs, output):
    (x, weight_proj, weight_mixer, skip_bias) = inputs
    y, y_gated = output  # Unpack both output tensors
    # Save y_gated along with other tensors
    ctx.save_for_backward(x, weight_proj, weight_mixer, skip_bias, y)


@torch.compiler.allow_in_graph
def b2b_causal_conv1d_fwd(*args):
    return torch.ops.subquadratic_ops_torch.b2b_causal_conv1d_fwd_primitive(*args)


@torch.compiler.allow_in_graph
def b2b_causal_conv1d_bwd(ctx, grad_out):
    x, weight_proj, weight_mixer, skip_bias, y = ctx.saved_tensors

    (
        dx,
        dw_proj,
        dw_mixer,
        db,
    ) = torch.ops.subquadratic_ops_torch.b2b_causal_conv1d_bwd_primitive(grad_out, x, weight_proj, weight_mixer, skip_bias, y)
    return dx, dw_proj, dw_mixer, db


torch.library.register_autograd(
    "subquadratic_ops_torch::b2b_causal_conv1d_fwd_primitive",
    b2b_causal_conv1d_bwd,
    setup_context=b2b_causal_conv1d_fwd_setup_fwd_context,
)


def b2b_causal_conv1d(x: Tensor, weight_proj: Tensor, weight_mixer: Tensor, skip_bias: Tensor) -> Tensor:
    r"""
    Back-to-back causal 1D convolution. Fused kernel performing projection convolution, pre-gating, mixer convolution, and post-gating.
    The operation is performed in a causal manner, meaning each position only attends to previous positions in the sequence.
    In code terms,

    .. code-block:: python

        y_gated = b2b_causal_conv1d(x, weight_proj, weight_mixer, skip_bias)

    is equivalent to,

    .. code-block:: python

        y = conv1d_proj(x)
        z = y[:,1::3, :] * y[:, 2::3, :]
        y_gated = mixer(z) + mixer.skip_bias * z
        y = y[:, ::3, :] * y_gated


    .. note::

        The input tensor is expected to be of shape ``(batch_size, 3*dim, seq_len)`` where ``dim`` is the number of channels in the output.

        If mixer weights are used with FFT based convolution, it should be flipped along the last dimension:

        .. code-block:: python

            weight_mixer = torch.flip(weight_mixer, [-1])

    Args:
        x (torch.Tensor): Input tensor of shape ``(batch_size, 3*dim, seq_len)``.
        weight_proj (torch.Tensor): Projection weight tensor of shape ``(dim, kernel_size)``.
        weight_mixer (torch.Tensor): Mixer weight tensor of shape ``(dim, kernel_size)``.
        skip_bias (torch.Tensor): Skip bias tensor of shape ``(dim,)``.

    Returns:
        torch.Tensor: Output tensor of shape ``(batch_size, dim, seq_len)``.

    Example:
        .. code-block:: python

            batch_size, dim, seq_len, kernel_size = 2, 4, 10, 3
            x = torch.randn(batch_size, 3*dim, seq_len, device="cuda")
            weight_proj = torch.randn(3*dim, kernel_size, device="cuda")
            weight_mixer = torch.randn(dim, kernel_size, device="cuda")
            skip_bias = torch.randn(dim, device="cuda")
            y_gated = b2b_causal_conv1d(x, weight_proj, weight_mixer, skip_bias)
            print(y_gated.shape)  # torch.Size([2, 4, 10])
    """
    _, y_gated = torch.ops.subquadratic_ops_torch.b2b_causal_conv1d_fwd_primitive(x, weight_proj, weight_mixer, skip_bias)
    return y_gated
