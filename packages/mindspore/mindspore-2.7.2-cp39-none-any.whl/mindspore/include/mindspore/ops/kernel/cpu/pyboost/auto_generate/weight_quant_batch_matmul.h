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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_WEIGHTQUANTBATCHMATMUL_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_WEIGHTQUANTBATCHMATMUL_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/weight_quant_batch_matmul.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class WeightQuantBatchMatmulCPU : public pyboost::WeightQuantBatchMatmul {
 public:
  WeightQuantBatchMatmulCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : WeightQuantBatchMatmul(std::move(primitive), device_context) {}
  ~WeightQuantBatchMatmulCPU() = default;

  mindspore::tensor::TensorPtr Call(const mindspore::tensor::TensorPtr &x_tensor, const mindspore::tensor::TensorPtr &weight_tensor, const mindspore::tensor::TensorPtr &antiquant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &antiquant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &quant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &quant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &bias_tensor, const mindspore::BoolImmPtr &transpose_x, const mindspore::BoolImmPtr &transpose_weight, const mindspore::Int64ImmPtr &antiquant_group_size) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_WEIGHTQUANTBATCHMATMUL_CPU_H_
