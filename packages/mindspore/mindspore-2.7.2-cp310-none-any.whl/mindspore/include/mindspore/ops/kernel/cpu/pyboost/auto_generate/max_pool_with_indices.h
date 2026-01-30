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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MAXPOOLWITHINDICES_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MAXPOOLWITHINDICES_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/max_pool_with_indices.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class MaxPoolWithIndicesCPU : public pyboost::MaxPoolWithIndices {
 public:
  MaxPoolWithIndicesCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : MaxPoolWithIndices(std::move(primitive), device_context) {}
  ~MaxPoolWithIndicesCPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &x_tensor, const mindspore::ValueTuplePtr &kernel_size, const std::optional<mindspore::ValueTuplePtr> &strides, const mindspore::ValueTuplePtr &pads, const mindspore::ValueTuplePtr &dilation, const mindspore::BoolImmPtr &ceil_mode, const mindspore::Int64ImmPtr &argmax_type) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_MAXPOOLWITHINDICES_CPU_H_
