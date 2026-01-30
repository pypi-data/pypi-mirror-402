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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOEDISTRIBUTEDISPATCH_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOEDISTRIBUTEDISPATCH_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/moe_distribute_dispatch.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class MoeDistributeDispatchCPU : public pyboost::MoeDistributeDispatch {
 public:
  MoeDistributeDispatchCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : MoeDistributeDispatch(std::move(primitive), device_context) {}
  ~MoeDistributeDispatchCPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &x_tensor, const mindspore::tensor::TensorPtr &expert_ids_tensor, const mindspore::Int64ImmPtr &ep_world_size, const mindspore::Int64ImmPtr &ep_rank_id, const mindspore::Int64ImmPtr &moe_expert_num, const std::optional<mindspore::tensor::TensorPtr> &expert_scales_tensor, const std::optional<mindspore::tensor::TensorPtr> &scales_tensor, const std::optional<mindspore::tensor::TensorPtr> &x_active_mask_tensor, const std::optional<mindspore::StringImmPtr> &group_ep, const std::optional<mindspore::StringImmPtr> &group_tp, const mindspore::Int64ImmPtr &tp_world_size, const mindspore::Int64ImmPtr &tp_rank_id, const mindspore::Int64ImmPtr &expert_shard_type, const mindspore::Int64ImmPtr &shared_expert_num, const mindspore::Int64ImmPtr &shared_expert_rank_num, const mindspore::Int64ImmPtr &quant_mode, const mindspore::Int64ImmPtr &global_bs, const mindspore::Int64ImmPtr &expert_token_nums_type) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOEDISTRIBUTEDISPATCH_CPU_H_
