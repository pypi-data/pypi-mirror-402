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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_SOFTSHRINKGRAD_ASCEND_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_SOFTSHRINKGRAD_ASCEND_H_

#include "mindspore/ccsrc/pyboost/auto_generate/softshrink_grad.h"
#include "ir/tensor.h"
#include "ir/scalar.h"
#include "mindspore/ops/ops_utils/memory_overlap.h"
#include "kernel/ascend/visible.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class OPS_ASCEND_API SoftShrinkGradAscend : public pyboost::SoftShrinkGrad {
 public:
  SoftShrinkGradAscend(PrimitivePtr primitive, const DeviceContext *device_context)
      : SoftShrinkGrad(std::move(primitive), device_context) {}
  ~SoftShrinkGradAscend() = default;

  mindspore::tensor::TensorPtr Call(const mindspore::tensor::TensorPtr &input_grad_tensor, const mindspore::tensor::TensorPtr &input_x_tensor, const mindspore::FP32ImmPtr &lambd) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_SOFTSHRINKGRAD_ASCEND_H_
