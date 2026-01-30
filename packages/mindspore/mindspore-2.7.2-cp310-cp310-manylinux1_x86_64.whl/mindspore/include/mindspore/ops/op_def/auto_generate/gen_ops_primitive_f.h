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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_f_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_f_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_f.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimFFT2;
OPS_API extern const PrimitivePtr kPrimFlattenExt;
OPS_API extern const PrimitivePtr kPrimFmodTensor;
OPS_API extern const PrimitivePtr kPrimFloor;
OPS_API extern const PrimitivePtr kPrimFillScalar;
OPS_API extern const PrimitivePtr kPrimFusedAddTopKDiv;
OPS_API extern const PrimitivePtr kPrimFFT;
OPS_API extern const PrimitivePtr kPrimFillTensor;
OPS_API extern const PrimitivePtr kPrimFlatten;
OPS_API extern const PrimitivePtr kPrimFFTShapeCopy;
OPS_API extern const PrimitivePtr kPrimFastGeLUGrad;
OPS_API extern const PrimitivePtr kPrimFFTWithSize;
OPS_API extern const PrimitivePtr kPrimFmodScalar;
OPS_API extern const PrimitivePtr kPrimFloorDiv;
OPS_API extern const PrimitivePtr kPrimFFTShift;
OPS_API extern const PrimitivePtr kPrimFastGeLU;
OPS_API extern const PrimitivePtr kPrimFullLike;
OPS_API extern const PrimitivePtr kPrimFFTFreq;
OPS_API extern const PrimitivePtr kPrimFFNExt;
OPS_API extern const PrimitivePtr kPrimFormatCast;
OPS_API extern const PrimitivePtr kPrimFloorMod;
OPS_API extern const PrimitivePtr kPrimFrac;
OPS_API extern const PrimitivePtr kPrimFFTN;
OPS_API extern const PrimitivePtr kPrimFlashAttentionScoreGrad;
OPS_API extern const PrimitivePtr kPrimFloorDivScalar;
OPS_API extern const PrimitivePtr kPrimFFTOrtho;
OPS_API extern const PrimitivePtr kPrimFlashAttentionScore;
OPS_API extern const PrimitivePtr kPrimFusedInferAttentionScore;
OPS_API extern const PrimitivePtr kPrimFusedMatmulElemBinary;
OPS_API extern const PrimitivePtr kPrimFusedMatmulElemUnary;
OPS_API extern const PrimitivePtr kPrimFuncDropoutExt;
OPS_API extern const PrimitivePtr kPrimFuncMaxPool2D;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_f_H_
