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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_QUANTMATMUL_GPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_QUANTMATMUL_GPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/quant_matmul.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class QuantMatmulGPU : public pyboost::QuantMatmul {
 public:
  QuantMatmulGPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : QuantMatmul(std::move(primitive), device_context) {}
  ~QuantMatmulGPU() = default;

  mindspore::tensor::TensorPtr Call(const mindspore::tensor::TensorPtr &x1_tensor, const mindspore::tensor::TensorPtr &x2_tensor, const mindspore::tensor::TensorPtr &scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &pertoken_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &bias_tensor, const std::optional<mindspore::Int64ImmPtr> &output_dtype, const std::optional<mindspore::Int64ImmPtr> &x1_dtype, const std::optional<mindspore::Int64ImmPtr> &x2_dtype, const std::optional<mindspore::Int64ImmPtr> &pertoken_scale_dtype, const std::optional<mindspore::Int64ImmPtr> &scale_dtype, const std::optional<mindspore::ValueTuplePtr> &group_sizes) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_QUANTMATMUL_GPU_H_
