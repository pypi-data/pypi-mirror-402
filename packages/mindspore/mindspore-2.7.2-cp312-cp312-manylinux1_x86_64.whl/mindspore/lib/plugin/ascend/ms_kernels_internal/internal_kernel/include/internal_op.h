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

#ifndef MS_KERNELS_INTERNAL_KERNEL_INTERNAL_OP_H_
#define MS_KERNELS_INTERNAL_KERNEL_INTERNAL_OP_H_

#include <vector>
#include <string>

#include "include/base_type.h"
#include "include/op_param.h"
#include "include/tiling_info.h"

namespace mindspore {
namespace internal {
enum OpType : int {
  kOpTypeAICore = 0,
  kOpTypeAICpu,
  kOpTypeAIV,
  kOpTypeWriteBack,
  kOpTypeMixAIC,
  kOpTypeMixAIV,
  kOpTypeFFTSPlus,
  kOpTypeDSA,
  kOpTypeDVPP,
  kOpTypeHCCL,
  kOpTypeInvalid
};

class InternalOp {
 public:
  InternalOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
             const std::string &op_name);
  virtual ~InternalOp() = default;
  InternalStatus Init();

  virtual InternalStatus UpdateShape(const ShapeInfoList &inputs_shape, const ShapeInfoList &outputs_shape);
  virtual InternalStatus UpdateParam(const void *) { return kInternalOk; }

  virtual size_t GetTilingSize() const = 0;
  virtual std::vector<size_t> GetWorkspaceSize() const = 0;

  virtual void SetTilingInfo(const TilingInfoPtr &tiling_info);

  virtual InternalStatus Launch(const InputsAddrList &input_ptrs, const OutputsAddrList &output_ptrs,
                                const WsAddrList &ws_ptrs, void *stream, const std::string &op_fullname = "");
  virtual InternalStatus Tiling(RawHostAddr host_ptr, HostRunInfoPtr *run_info_ptr);
  virtual std::string DumpTiling(const RawHostAddr host_ptr) const = 0;

  virtual ShapeInfoList InferShape(const ShapeInfoList &inputs_shape) const = 0;

  virtual InternalStatus TilingFromTuning(const RawDeviceAddr tiling_addr);
  virtual bool IsSupported(const InputDataTypes &dtypes);

  virtual std::string GetOpName() { return "Internal" + op_name_; };
  std::string GetOpNameOrigin() { return op_name_; };
  virtual uint32_t GetLaunchCoreNum() const { return host_run_info_comm_ptr_->block_dim_; };
  virtual OpType GetOpType() = 0;

  // ---- Ops DataBase related functions ----
  // Version: Op implementation version(update when the unnegligible change happens)
  virtual int64_t GetOpVersion() const { return 0; }
  // DataBaseKey: Op information(which can rebuild this op without ambiguity)
  virtual std::vector<int64_t> GetDataBaseKey() const { return std::vector<int64_t>{}; }
  // Tiling
  virtual std::vector<int64_t> GetCurrentTiling() const { return {}; }
  virtual InternalStatus Tiling(const std::vector<int64_t> &tiling, RawHostAddr &tiling_addr,
                                HostRunInfoPtr *run_info_ptr) {
    return kInternalError;
  }
  // ---- Ops DataBase related functions ----

 protected:
  virtual InternalStatus InitImpl();
  virtual InternalStatus TilingImpl(RawHostAddr host_ptr, HostRunInfoPtr *run_info_ptr) = 0;
  virtual InternalStatus LaunchImpl(const InputsAddrList &input_ptrs, const OutputsAddrList &output_ptrs,
                                    const WsAddrList &ws_ptrs, void *stream) = 0;
  void SetHostRunInfoComm(const HostRunInfoComm &, HostRunInfoPtr *);

  InputsImmutableInfoList inputs_ii_;
  OutputsImmutableInfoList outputs_ii_;
  ShapeInfoList inputs_shape_;
  ShapeInfoList outputs_shape_;
  std::string op_name_{"UnknownOp"};
  RawDeviceAddr tiling_device_addr_{nullptr};
  HostRunInfoCommPtr host_run_info_comm_ptr_{nullptr};

 private:
  virtual InternalStatus LaunchWithProfiling(const InputsAddrList &input_ptrs, const OutputsAddrList &output_ptrs,
                                             const WsAddrList &ws_ptrs, void *stream, const std::string &op_fullname);
};

using InternalOpPtr = std::shared_ptr<InternalOp>;

short GetPlatformEnum(const std::string &soc_name);
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_INTERNAL_OP_H_