/**
 * Copyright 2023-2025 Huawei Technologies Co., Ltd
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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_h_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_h_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_h.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimHardtanh;
OPS_API extern const PrimitivePtr kPrimHFFT;
OPS_API extern const PrimitivePtr kPrimHFFT2;
OPS_API extern const PrimitivePtr kPrimHSwishGrad;
OPS_API extern const PrimitivePtr kPrimHardtanhGrad;
OPS_API extern const PrimitivePtr kPrimHSwish;
OPS_API extern const PrimitivePtr kPrimHShrink;
OPS_API extern const PrimitivePtr kPrimHSigmoidGrad;
OPS_API extern const PrimitivePtr kPrimHShrinkGrad;
OPS_API extern const PrimitivePtr kPrimHistcExt;
OPS_API extern const PrimitivePtr kPrimHFFTN;
OPS_API extern const PrimitivePtr kPrimHSigmoid;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_h_H_
