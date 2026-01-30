/**
 * Copyright 2023 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_MOEINITROUTINGQUANTV2_GPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_MOEINITROUTINGQUANTV2_GPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/moe_init_routing_quant_v2.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class MoeInitRoutingQuantV2GPU : public pyboost::MoeInitRoutingQuantV2 {
 public:
  MoeInitRoutingQuantV2GPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : MoeInitRoutingQuantV2(std::move(primitive), device_context) {}
  ~MoeInitRoutingQuantV2GPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &x_tensor, const mindspore::tensor::TensorPtr &expert_idx_tensor, const mindspore::Int64ImmPtr &active_num, const mindspore::Int64ImmPtr &expert_capacity, const mindspore::Int64ImmPtr &expert_num, const mindspore::Int64ImmPtr &drop_pad_mode, const mindspore::Int64ImmPtr &expert_tokens_count_or_cumsum_flag, const mindspore::BoolImmPtr &expert_tokens_before_capacity_flag, const mindspore::Int64ImmPtr &quant_mode, const std::optional<mindspore::tensor::TensorPtr> &scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &offset_tensor) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_MOEINITROUTINGQUANTV2_GPU_H_
