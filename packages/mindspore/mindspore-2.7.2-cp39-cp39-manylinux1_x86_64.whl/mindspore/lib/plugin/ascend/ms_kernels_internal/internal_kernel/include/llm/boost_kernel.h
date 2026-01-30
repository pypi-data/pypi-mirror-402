/**
 * Copyright 2024 Huawei Technologies Co., Ltd
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
#ifndef MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_BOOST_KERNEL_H_
#define MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_BOOST_KERNEL_H_
#include <memory>
#include <vector>
#include "include/llm/tensor.h"

namespace mindspore {
namespace internal {

struct BoostParam {};
struct RawBuf {
  uint64_t size_{0};
  void *addr_{nullptr};
};
using HostRawBuf = RawBuf;
using DeviceRawBuf = RawBuf;

using BoostParamPtr = std::shared_ptr<BoostParam>;

class BoostKernel {
 public:
  BoostKernel(const BoostParamPtr &param) : param_(param){};
  virtual ~BoostKernel() {}
  // this routine will check if this kernel can support the requirements
  // specified in ValidationInfo.
  virtual bool Init() = 0;
  virtual void SetInputs(const std::vector<Tensor *> &inputs) { inputs_ = inputs; }
  virtual void SetOutputs(const std::vector<Tensor *> &outputs) { outputs_ = outputs; }
  virtual void SetWorkSpace(const std::vector<DeviceRawBuf> &workspace) { return; }
  virtual void SetStream(const void *stream_ptr) { stream_ptr_ = const_cast<void *>(stream_ptr); }
  virtual void SetDeviceTilingBuf(const DeviceRawBuf &tilingBuf) = 0;
  virtual int Launch() = 0;
  virtual uint64_t GetTilingBufSize() = 0;
  virtual int Tiling(HostRawBuf &tilingBuf) = 0;
  virtual std::vector<uint64_t> GetWorkSpaceSize() = 0;
  virtual int InferShape(const std::vector<TensorDesc> &inputs, std::vector<TensorDesc> &outputs) = 0;
  virtual bool IsSupported() { return true; }

  virtual std::vector<Tensor *> &get_inputs() { return inputs_; }
  virtual std::vector<Tensor *> &get_outputs() { return outputs_; }

  std::string get_name() { return kernel_name_; }
  void set_name(std::string kernel_name) { kernel_name_ = kernel_name; }

 protected:
  std::string kernel_name_;
  BoostParamPtr param_ = nullptr;
  std::vector<Tensor *> inputs_;
  std::vector<Tensor *> outputs_;
  void *stream_ptr_ = nullptr;
};
using BoostKernelPtr = std::shared_ptr<BoostKernel>;
}  // namespace internal
}  // namespace mindspore
#endif  // MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_BOOST_KERNEL_H_
