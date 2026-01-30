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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_ADDLAYERNORMGRAD_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_ADDLAYERNORMGRAD_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/add_layer_norm_grad.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class AddLayerNormGradCPU : public pyboost::AddLayerNormGrad {
 public:
  AddLayerNormGradCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : AddLayerNormGrad(std::move(primitive), device_context) {}
  ~AddLayerNormGradCPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &dy_tensor, const mindspore::tensor::TensorPtr &x1_tensor, const mindspore::tensor::TensorPtr &x2_tensor, const mindspore::tensor::TensorPtr &rstd_tensor, const mindspore::tensor::TensorPtr &mean_tensor, const mindspore::tensor::TensorPtr &gamma_tensor, const mindspore::tensor::TensorPtr &dsumOptional_tensor) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_ADDLAYERNORMGRAD_CPU_H_
