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

#ifndef MS_KERNELS_INTERNAL_KERNEL_BASE_TYPE_H_
#define MS_KERNELS_INTERNAL_KERNEL_BASE_TYPE_H_

#include <vector>
#include <unordered_set>
#include <map>
#include <cstdint>
#include <memory>
#include <limits>
#include <string>
#include <utility>

namespace mindspore {
namespace internal {
constexpr size_t kIndex0 = 0;
constexpr size_t kIndex1 = 1;
constexpr size_t kIndex2 = 2;
constexpr size_t kIndex3 = 3;
constexpr size_t kIndex4 = 4;
constexpr size_t kIndex5 = 5;
constexpr size_t kIndex6 = 6;
constexpr size_t kIndex7 = 7;
constexpr size_t kIndex8 = 8;
constexpr size_t kIndex9 = 9;
constexpr size_t kIndex10 = 10;
constexpr size_t kIndex11 = 11;
constexpr size_t kIndex12 = 12;
constexpr size_t kIndex13 = 13;
constexpr size_t kIndex14 = 14;
constexpr size_t kIndex15 = 15;
constexpr size_t kIndex16 = 16;
constexpr size_t kIndex17 = 17;
constexpr size_t kIndex18 = 18;
constexpr size_t kIndex19 = 19;
constexpr size_t kIndex20 = 20;
// dim of shape
constexpr size_t kDim0 = 0;
constexpr size_t kDim1 = 1;
constexpr size_t kDim2 = 2;
constexpr size_t kDim3 = 3;
constexpr size_t kDim4 = 4;
constexpr size_t kDim5 = 5;
constexpr size_t kDim6 = 6;
constexpr size_t kDim7 = 7;
constexpr size_t kDim8 = 8;
using ShapeInfo = std::vector<int64_t>;

enum DataType : int {
  kTypeUnknown = 0,
  kTypeFloat16,
  kTypeFloat32,
  kTypeFloat64,
  kTypeInt8,
  kTypeInt16,
  kTypeInt32,
  kTypeInt64,
  kTypeUint8,
  kTypeUint16,
  kTypeUint32,
  kTypeUint64,
  kTypeBF16,
  kTypeBool,
  kTypeComplex64,
  kTypeComplex128,
  kTypeString,
  kTypeNone,
  kTypeInt4
};

enum TensorFormat : int {
  kFormatUnknown,
  kFormatND,
  kFormatNCHW,
  kFormatNHWC,
  kFormatNC1HWC0,
  kFormatFRACTAL_Z,
  kFormatNC1HWC0_C04,
  kFormatHWCN,
  kFormatNDHWC,
  kFormatFRACTAL_NZ,
  kFormatNCDHW,
  kFormatNDC1HWC0,
  kFormatFRACTAL_Z_3D
};

enum InternalStatus {
  kInternalOk = 0,
  kInternalError,
};

class ArgImmutableInfo {
 public:
  ArgImmutableInfo(DataType type, TensorFormat format) : d_type_(type), format_(format) {}
  ArgImmutableInfo() {}
  ~ArgImmutableInfo() = default;

  void SetDtype(DataType type) { d_type_ = type; }

  DataType GetDtype() const { return d_type_; }

  void SetFormat(TensorFormat format) { format_ = format; }

  TensorFormat GetFormat() const { return format_; }

 private:
  DataType d_type_{DataType::kTypeUnknown};
  TensorFormat format_{TensorFormat::kFormatUnknown};
};

inline size_t CountNumFromShape(const ShapeInfo &shape) {
  if (shape.empty()) {
    return 0;
  }

  size_t num = 1;
  size_t max_value = std::numeric_limits<size_t>::max();
  for (auto s : shape) {
    if (num > max_value / static_cast<size_t>(s)) {
      return  max_value;
    }
    num *= static_cast<size_t>(s);
  }

  return num;
}

class ArgDesc {
 public:
  explicit ArgDesc(const ArgImmutableInfo &arg_ii) : immutable_info_(arg_ii) {}
  ArgDesc(DataType type, TensorFormat format) : immutable_info_(type, format) {}
  ArgDesc(const ShapeInfo &shape, DataType type, TensorFormat format) : shape_(shape), immutable_info_(type, format) {}

  ~ArgDesc() = default;
  const ShapeInfo &GetShape() const { return shape_; }

  void SetShape(const ShapeInfo &shape) { shape_ = shape; }

  void SetDtype(DataType type) { immutable_info_.SetDtype(type); }

  DataType GetDtype() const {
    return immutable_info_.GetDtype();
  }

  void SetFormat(TensorFormat format) { immutable_info_.SetFormat(format); }

  TensorFormat GetFormat() const {
    return immutable_info_.GetFormat();
  }

  const ArgImmutableInfo &GetImmutableInfo() const { return immutable_info_; }

  inline size_t ElementNum() const { return CountNumFromShape(shape_); }

 private:
  ShapeInfo shape_{0};
  ArgImmutableInfo immutable_info_;
};
using ArgDescPtr = std::shared_ptr<ArgDesc>;

using InputsDescList = std::vector<ArgDesc>;
using OutputsDescList = std::vector<ArgDesc>;
using InputsImmutableInfoList = std::vector<ArgImmutableInfo>;
using OutputsImmutableInfoList = std::vector<ArgImmutableInfo>;
using InputDataTypes = std::vector<DataType>;
using DtypeInfoList = std::vector<DataType>;
using RawDeviceAddr = void *;
using RawHostAddr = void *;
using InputsAddrList = std::vector<RawDeviceAddr>;
using OutputsAddrList = std::vector<RawDeviceAddr>;
using WsAddrList = std::vector<RawDeviceAddr>;
using ShapeInfoList = std::vector<ShapeInfo>;

using InOutDtypesList = std::vector<std::vector<InputDataTypes>>;
using InOutDtypesTargetMap = std::map<std::string, InOutDtypesList>;

using InOutIndicesType = std::pair<std::unordered_set<size_t>, std::unordered_set<size_t>>;
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_BASE_TYPE_H_
