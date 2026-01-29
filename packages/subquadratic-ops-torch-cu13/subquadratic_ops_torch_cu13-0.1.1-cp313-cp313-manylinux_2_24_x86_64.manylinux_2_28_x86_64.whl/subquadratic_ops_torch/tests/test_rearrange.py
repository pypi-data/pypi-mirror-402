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

from subquadratic_ops_torch.rearrange import rearrange


@pytest.mark.parametrize("bhl_to_lbh", [True, False])
@pytest.mark.parametrize("batch_size", [1, 2, 3])
@pytest.mark.parametrize("hidden_dim", [1024, 2048, 409, 241])
@pytest.mark.parametrize("seq_dim", [1024, 2048, 4096, 1294])
@pytest.mark.parametrize("dtype", [torch.float64, torch.float32, torch.bfloat16, torch.float16])
def test_rearrange(bhl_to_lbh, batch_size, hidden_dim, seq_dim, dtype):
    torch.manual_seed(9)
    x = torch.randn(batch_size, hidden_dim, seq_dim).cuda().to(dtype)
    y = rearrange(x, bhl_to_lbh)
    y_ref = x.permute(2, 0, 1) if bhl_to_lbh else x.permute(1, 2, 0)
    torch.testing.assert_close(y, y_ref)


@pytest.mark.parametrize("bhl_to_lbh", [True, False])
def test_rearrange_bwd(bhl_to_lbh):
    x = torch.randn(2, 2, 3).cuda().double()
    x.requires_grad = True
    torch.autograd.gradcheck(rearrange, (x, bhl_to_lbh))
