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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_LINSPACEEXT_CPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_LINSPACEEXT_CPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/lin_space_ext.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class LinSpaceExtCPU : public pyboost::LinSpaceExt {
 public:
  LinSpaceExtCPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : LinSpaceExt(std::move(primitive), device_context) {}
  ~LinSpaceExtCPU() = default;

  mindspore::tensor::TensorPtr Call(const mindspore::ScalarPtr &start, const mindspore::ScalarPtr &end, const mindspore::Int64ImmPtr &steps, const std::optional<mindspore::Int64ImmPtr> &dtype) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_CPU_KERNEL_PYBOOST_LINSPACEEXT_CPU_H_
