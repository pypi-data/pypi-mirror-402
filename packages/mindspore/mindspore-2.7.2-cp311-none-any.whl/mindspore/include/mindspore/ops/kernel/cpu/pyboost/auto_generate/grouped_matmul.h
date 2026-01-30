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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_GROUPEDMATMUL_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_GROUPEDMATMUL_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/grouped_matmul.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class GroupedMatmulCPU : public pyboost::GroupedMatmul {
 public:
  GroupedMatmulCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : GroupedMatmul(std::move(primitive), device_context) {}
  ~GroupedMatmulCPU() = default;

  std::vector<mindspore::tensor::TensorPtr> Call(const mindspore::ValueTuplePtr &x_tensor_list, const mindspore::ValueTuplePtr &weight_tensor_list, const std::optional<mindspore::ValueTuplePtr> &bias_tensor_list, const std::optional<mindspore::ValueTuplePtr> &scale_tensor_list, const std::optional<mindspore::ValueTuplePtr> &offset_tensor_list, const std::optional<mindspore::ValueTuplePtr> &antiquant_scale_tensor_list, const std::optional<mindspore::ValueTuplePtr> &antiquant_offset_tensor_list, const std::optional<mindspore::tensor::TensorPtr> &group_list_tensor, const mindspore::Int64ImmPtr &split_item, const mindspore::Int64ImmPtr &group_type, const mindspore::BoolImmPtr &transpose_a, const mindspore::BoolImmPtr &transpose_b) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_GROUPEDMATMUL_CPU_H_
