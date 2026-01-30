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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_COL2IMEXT_GPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_COL2IMEXT_GPU_H_

#include "mindspore/ccsrc/pyboost/auto_generate/col2im_ext.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class Col2ImExtGPU : public pyboost::Col2ImExt {
 public:
  Col2ImExtGPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : Col2ImExt(std::move(primitive), device_context) {}
  ~Col2ImExtGPU() = default;

  mindspore::tensor::TensorPtr Call(const mindspore::tensor::TensorPtr &input_tensor, const mindspore::ValueTuplePtr &output_size, const mindspore::ValueTuplePtr &kernel_size, const mindspore::ValueTuplePtr &dilation, const mindspore::ValueTuplePtr &padding, const mindspore::ValueTuplePtr &stride) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_COL2IMEXT_GPU_H_
