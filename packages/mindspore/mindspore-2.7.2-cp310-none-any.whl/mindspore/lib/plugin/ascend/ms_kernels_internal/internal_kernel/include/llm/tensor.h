/**
 * Copyright (c) Huawei Technologies Co., Ltd. 2023. All rights reserved.
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

#ifndef MS_KERNELS_INTERNAL_KERNEL_SRC_OPS_LLAMA_TENSOR_H_
#define MS_KERNELS_INTERNAL_KERNEL_SRC_OPS_LLAMA_TENSOR_H_
#include <vector>
#include <map>
#include <limits>
#include <iostream>
#include "include/base_type.h"

using DIMS = std::vector<int64_t>;
namespace mindspore::internal {
constexpr size_t HALF_DATA_SIZE = 2;
enum TensorDType : int {
  TENSOR_DTYPE_UNDEFINED = -1,
  TENSOR_DTYPE_FLOAT = 0,
  TENSOR_DTYPE_FLOAT16 = 1,
  TENSOR_DTYPE_INT8 = 2,
  TENSOR_DTYPE_INT32 = 3,
  TENSOR_DTYPE_UINT8 = 4,
  TENSOR_DTYPE_INT16 = 6,
  TENSOR_DTYPE_UINT16 = 7,
  TENSOR_DTYPE_UINT32 = 8,
  TENSOR_DTYPE_INT64 = 9,
  TENSOR_DTYPE_UINT64 = 10,
  TENSOR_DTYPE_DOUBLE = 11,
  TENSOR_DTYPE_BOOL = 12,
  TENSOR_DTYPE_STRING = 13,
  TENSOR_DTYPE_COMPLEX64 = 16,
  TENSOR_DTYPE_COMPLEX128 = 17,
  TENSOR_DTYPE_BF16 = 27
};

static const std::map<TensorDType, size_t> MAP_OF_DTYPE_SIZE = {{TensorDType::TENSOR_DTYPE_UNDEFINED, 0},
                                                                {TensorDType::TENSOR_DTYPE_FLOAT, sizeof(float)},
                                                                {TensorDType::TENSOR_DTYPE_FLOAT16, HALF_DATA_SIZE},
                                                                {TensorDType::TENSOR_DTYPE_INT8, sizeof(int8_t)},
                                                                {TensorDType::TENSOR_DTYPE_INT32, sizeof(int32_t)},
                                                                {TensorDType::TENSOR_DTYPE_UINT8, sizeof(uint8_t)},
                                                                {TensorDType::TENSOR_DTYPE_INT16, sizeof(int16_t)},
                                                                {TensorDType::TENSOR_DTYPE_UINT16, sizeof(uint16_t)},
                                                                {TensorDType::TENSOR_DTYPE_UINT32, sizeof(uint32_t)},
                                                                {TensorDType::TENSOR_DTYPE_INT64, sizeof(int64_t)},
                                                                {TensorDType::TENSOR_DTYPE_UINT64, sizeof(uint64_t)},
                                                                {TensorDType::TENSOR_DTYPE_DOUBLE, sizeof(double)},
                                                                {TensorDType::TENSOR_DTYPE_BOOL, sizeof(bool)},
                                                                {TensorDType::TENSOR_DTYPE_BF16, HALF_DATA_SIZE}};

struct TensorDesc {
  TensorDType dtype = TENSOR_DTYPE_UNDEFINED;
  TensorFormat format = TensorFormat::kFormatUnknown;
  DIMS dims;
  int64_t Numel() const;
};

struct Tensor {
  TensorDesc desc;
  void *data = nullptr;
  void *hostData = nullptr;
  size_t dataSize = 0;
  int64_t Numel() const;
};

size_t GetTensorElementSize(const TensorDType dtype);

}  // namespace mindspore::internal
#endif  // MS_KERNELS_INTERNAL_KERNEL_SRC_OPS_LLAMA_TENSOR_H_
