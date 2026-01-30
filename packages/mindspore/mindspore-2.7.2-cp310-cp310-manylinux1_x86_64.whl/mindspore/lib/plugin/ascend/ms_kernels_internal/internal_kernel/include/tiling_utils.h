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

#ifndef MS_KERNELS_INTERNAL_KERNEL_TILING_UTILS_H_
#define MS_KERNELS_INTERNAL_KERNEL_TILING_UTILS_H_

#include <cstdint>
#include <functional>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <utility>

#include "include/internal_op.h"
#include "src/log/log.h"

namespace mindspore {
namespace internal {
struct RuningInfo {
  internal::ShapeInfoList input_shapes;
  internal::InputsImmutableInfoList input_infos;
  internal::ShapeInfoList output_shapes;
  internal::InputsImmutableInfoList output_infos;
};
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_TILING_UTILS_H_
