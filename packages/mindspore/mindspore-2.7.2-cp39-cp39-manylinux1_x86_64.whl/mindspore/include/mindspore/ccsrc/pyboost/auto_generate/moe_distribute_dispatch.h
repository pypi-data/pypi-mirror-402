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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_MOEDISTRIBUTEDISPATCH_H_
#define MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_MOEDISTRIBUTEDISPATCH_H_

#include "mindspore/ccsrc/pyboost/op_runner.h"
#include "mindspore/ccsrc/pyboost/op_register.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class PYBOOST_API MoeDistributeDispatch : public pyboost::OpRunner {
 public:
  MoeDistributeDispatch(PrimitivePtr primitive, const DeviceContext *device_context)
      : OpRunner(std::move(primitive), device_context) {}
  ~MoeDistributeDispatch() override = default;

  virtual std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &x_tensor, const mindspore::tensor::TensorPtr &expert_ids_tensor, const mindspore::Int64ImmPtr &ep_world_size, const mindspore::Int64ImmPtr &ep_rank_id, const mindspore::Int64ImmPtr &moe_expert_num, const std::optional<mindspore::tensor::TensorPtr> &expert_scales_tensor, const std::optional<mindspore::tensor::TensorPtr> &scales_tensor, const std::optional<mindspore::tensor::TensorPtr> &x_active_mask_tensor, const std::optional<mindspore::StringImmPtr> &group_ep, const std::optional<mindspore::StringImmPtr> &group_tp, const mindspore::Int64ImmPtr &tp_world_size, const mindspore::Int64ImmPtr &tp_rank_id, const mindspore::Int64ImmPtr &expert_shard_type, const mindspore::Int64ImmPtr &shared_expert_num, const mindspore::Int64ImmPtr &shared_expert_rank_num, const mindspore::Int64ImmPtr &quant_mode, const mindspore::Int64ImmPtr &global_bs, const mindspore::Int64ImmPtr &expert_token_nums_type) = 0;
  bool output_is_tuple() const override { return true; }

 protected:
  static const std::string &op_name() {return op_name_;}

  inline static std::string op_name_ = "MoeDistributeDispatch";
};

}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_MOEDISTRIBUTEDISPATCH_H_
