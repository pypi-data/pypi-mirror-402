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
#ifndef MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_LLAMA_IMPL_H_
#define MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_LLAMA_IMPL_H_

#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include "include/llm/boost_kernel.h"
#include "include/llm/model_interface.h"

namespace mindspore {
namespace internal {
struct OpLlamaModelParam : public BoostParam {
  int batch_size_;
  int seq_length_;
  int head_num_;
  int kv_head_num_;
  int hidden_size_;
  int num_layers_;
  float ln_eps_;
  int vocab_size_;
  int multiple_of_;
  int device_id_;
  int device_num_;
  bool paged_attention_ = false;
  int64_t page_size_;
  int page_num_;
  int table_id_;
  void *hcom_ = nullptr;
};

using OpLlamaModelParamPtr = std::shared_ptr<OpLlamaModelParam>;

class LlamaImpl : public BoostKernel, public ModelInterface {
 public:
  explicit LlamaImpl(const OpLlamaModelParamPtr param);
  virtual ~LlamaImpl();
  bool Init() override;
  void SetDeviceTilingBuf(const DeviceRawBuf &tilingBuf) override;
  int Launch() override;
  uint64_t GetTilingBufSize() override;
  int Tiling(HostRawBuf &tilingBuf) override;
  int InferShape(const std::vector<TensorDesc> &inputs, std::vector<TensorDesc> &outputs) override;
  void PrintModel();
  static int CreateDictFromCKPT(dict *dict, std::string name);
  int AllocTable() override;
  int FreeTable(int table_id) override;
  bool AclInit();

 private:
  bool HcclInit();
  bool AllocKVCacheTable();
  bool BuildLlamaModel();
  bool LlamaAllocateInnerTensors();
  void *AllocateWs(size_t ws_size) override;
  virtual std::vector<uint64_t> GetWorkSpaceSize() override;
  bool SetupWorkspace() override;
  void SetWorkSpace(const std::vector<DeviceRawBuf> &workspace) override;
  int HandleDynamicInput();
  int SetupInputTensors();

  DeviceRawBuf tiling_buf_;

  void *prefil_mode_dev_ = nullptr;
  void *decode_mode_dev_ = nullptr;
  size_t batch_ = 0;
};
}  // namespace internal
}  // namespace mindspore
#endif  // MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_LLAMA_IMPL_H_
