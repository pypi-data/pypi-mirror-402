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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_SILENTCHECKV2_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_SILENTCHECKV2_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/silent_check_v2.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class SilentCheckV2CPU : public pyboost::SilentCheckV2 {
 public:
  SilentCheckV2CPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : SilentCheckV2(std::move(primitive), device_context) {}
  ~SilentCheckV2CPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &val_tensor, const mindspore::tensor::TensorPtr &input_grad_tensor, const mindspore::tensor::TensorPtr &sfda_tensor, const mindspore::tensor::TensorPtr &step_tensor, const mindspore::Int64ImmPtr &c_min_steps, const mindspore::FP32ImmPtr &c_thresh_l1, const mindspore::FP32ImmPtr &c_coeff_l1, const mindspore::FP32ImmPtr &c_thresh_l2, const mindspore::FP32ImmPtr &c_coeff_l2, const mindspore::Int64ImmPtr &npu_asd_detect) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_SILENTCHECKV2_CPU_H_
