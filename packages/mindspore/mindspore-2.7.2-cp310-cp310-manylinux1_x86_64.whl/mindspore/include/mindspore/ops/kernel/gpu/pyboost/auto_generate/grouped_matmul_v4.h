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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_GROUPEDMATMULV4_GPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_GROUPEDMATMULV4_GPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/grouped_matmul_v4.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class GroupedMatmulV4GPU : public pyboost::GroupedMatmulV4 {
 public:
  GroupedMatmulV4GPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : GroupedMatmulV4(std::move(primitive), device_context) {}
  ~GroupedMatmulV4GPU() = default;

  std::vector<mindspore::tensor::TensorPtr> Call(const mindspore::ValueTuplePtr &x_tensor_list, const mindspore::ValueTuplePtr &weight_tensor_list, const std::optional<mindspore::ValueTuplePtr> &bias_tensor_list, const std::optional<mindspore::ValueTuplePtr> &scale_tensor_list, const std::optional<mindspore::ValueTuplePtr> &offset_tensor_list, const std::optional<mindspore::ValueTuplePtr> &antiquant_scale_tensor_list, const std::optional<mindspore::ValueTuplePtr> &antiquant_offset_tensor_list, const std::optional<mindspore::ValueTuplePtr> &pre_token_scale_tensor_list, const std::optional<mindspore::tensor::TensorPtr> &group_list_tensor, const std::optional<mindspore::ValueTuplePtr> &activation_input_tensor_list, const std::optional<mindspore::ValueTuplePtr> &activation_quant_scale_tensor_list, const std::optional<mindspore::ValueTuplePtr> &activation_quant_offset_tensor_list, const mindspore::Int64ImmPtr &split_item, const mindspore::Int64ImmPtr &group_type, const mindspore::Int64ImmPtr &group_list_type, const mindspore::Int64ImmPtr &act_type, const std::optional<mindspore::Int64ImmPtr> &output_dtype) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_GROUPEDMATMULV4_GPU_H_
