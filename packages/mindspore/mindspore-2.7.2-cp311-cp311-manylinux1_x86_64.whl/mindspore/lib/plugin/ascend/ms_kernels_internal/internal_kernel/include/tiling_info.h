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

#ifndef MS_KERNELS_INTERNAL_KERNEL_TILING_INFO_H_
#define MS_KERNELS_INTERNAL_KERNEL_TILING_INFO_H_

#include <sstream>

#include "include/base_type.h"

namespace mindspore {
namespace internal {
class HostRunInfo {
 public:
  HostRunInfo() = default;
  virtual ~HostRunInfo() = default;
  void SetWorkSpaceSize(const std::vector<size_t> &workSpaceSize) { this->ws_size_ = workSpaceSize; }
  std::vector<size_t> GetWorkSpaceSize() const { return this->ws_size_; }
  virtual uint32_t GetBlockDim() const = 0;

 private:
  std::vector<size_t> ws_size_;
};
using HostRunInfoPtr = std::shared_ptr<HostRunInfo>;

class HostRunInfoComm : public HostRunInfo {
 public:
  explicit HostRunInfoComm(uint32_t block_dim);
  ~HostRunInfoComm() = default;

  uint32_t GetBlockDim() const override;

  uint32_t block_dim_{0};
  uint64_t any_value0_{0};
  uint64_t any_value1_{0};
  uint64_t any_value2_{0};
  uint64_t any_value3_{0};
  uint64_t any_value4_{0};
  uint64_t any_value5_{0};
};
using HostRunInfoCommPtr = std::shared_ptr<HostRunInfoComm>;

class TilingInfo {
 public:
  TilingInfo() = default;
  TilingInfo(RawDeviceAddr tiling_addr, const HostRunInfoPtr &host_run_info)
      : tiling_addr_(tiling_addr), host_run_info_{host_run_info} {}
  ~TilingInfo() = default;

  RawDeviceAddr tiling_addr_{nullptr};
  HostRunInfoPtr host_run_info_{nullptr};
};
using TilingInfoPtr = std::shared_ptr<TilingInfo>;
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_TILING_INFO_H_
