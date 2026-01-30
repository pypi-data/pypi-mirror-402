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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_BATCHNORMGATHERSTATSWITHCOUNTS_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_BATCHNORMGATHERSTATSWITHCOUNTS_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/batch_norm_gather_stats_with_counts.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class BatchNormGatherStatsWithCountsCPU : public pyboost::BatchNormGatherStatsWithCounts {
 public:
  BatchNormGatherStatsWithCountsCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : BatchNormGatherStatsWithCounts(std::move(primitive), device_context) {}
  ~BatchNormGatherStatsWithCountsCPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &input_tensor, const mindspore::tensor::TensorPtr &mean_tensor, const mindspore::tensor::TensorPtr &invstd_tensor, const std::optional<mindspore::tensor::TensorPtr> &running_mean_tensor, const std::optional<mindspore::tensor::TensorPtr> &running_var_tensor, const mindspore::FP32ImmPtr &momentum, const mindspore::FP32ImmPtr &eps, const std::optional<mindspore::tensor::TensorPtr> &counts_tensor) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_BATCHNORMGATHERSTATSWITHCOUNTS_CPU_H_
