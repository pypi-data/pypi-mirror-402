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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOETOKENUNPERMUTEGRAD_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOETOKENUNPERMUTEGRAD_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/moe_token_unpermute_grad.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class MoeTokenUnpermuteGradCPU : public pyboost::MoeTokenUnpermuteGrad {
 public:
  MoeTokenUnpermuteGradCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : MoeTokenUnpermuteGrad(std::move(primitive), device_context) {}
  ~MoeTokenUnpermuteGradCPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &permuted_tokens_tensor, const mindspore::tensor::TensorPtr &unpermuted_tokens_grad_tensor, const mindspore::tensor::TensorPtr &sorted_indices_tensor, const std::optional<mindspore::tensor::TensorPtr> &probs_tensor, const mindspore::BoolImmPtr &padded_mode, const std::optional<mindspore::ValueTuplePtr> &restore_shape) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MOETOKENUNPERMUTEGRAD_CPU_H_
