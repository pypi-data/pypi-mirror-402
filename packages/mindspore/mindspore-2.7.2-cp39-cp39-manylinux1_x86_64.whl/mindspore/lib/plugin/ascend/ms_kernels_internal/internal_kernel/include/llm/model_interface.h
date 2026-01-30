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
#ifndef MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_MODEL_INTERFACE_H_
#define MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_MODEL_INTERFACE_H_

#include <map>
#include <string>
#include "include/llm/tensor.h"

namespace mindspore {
namespace internal {

using dict = std::map<std::string, Tensor *>;
class CacheMgr;
class Graph;

class ModelInterface {
 public:
  ModelInterface(int num_layers, int seq_len, int page_num, int page_size, int head_num, int kv_head_num,
                 int hidden_size);
  virtual ~ModelInterface();
  virtual int AllocTable() = 0;
  virtual int FreeTable(int table_id) = 0;
  virtual void *AllocateWs(size_t ws_size) = 0;
  virtual bool SetupWorkspace() = 0;
  void SetIsFIrstIter(bool is_first_iter) { is_first_iter_ = is_first_iter; }
  void SetupWeights(dict *dict_weights) { dict_weights_ = dict_weights; }

 protected:
  Graph *graph_ = nullptr;
  CacheMgr *cache_mgr_;
  dict *dict_weights_ = nullptr;
  bool is_first_iter_ = true;
  void *workspace_addr_ = nullptr;
  size_t workspace_size_ = 0;
  static constexpr size_t max_ws_size_ = static_cast<size_t>(8000) * (1 << 20);
};
}  // namespace internal
}  // namespace mindspore
#endif  // MS_KERNELS_INTERNAL_KERNEL_INCLUDE_LLM_MODEL_INTERFACE_H_
