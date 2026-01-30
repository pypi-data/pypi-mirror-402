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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_s_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_s_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_s.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimSoftplusExt;
OPS_API extern const PrimitivePtr kPrimScatterNd;
OPS_API extern const PrimitivePtr kPrimSiLUGrad;
OPS_API extern const PrimitivePtr kPrimScalarPow;
OPS_API extern const PrimitivePtr kPrimSplitTensor;
OPS_API extern const PrimitivePtr kPrimSigmoid;
OPS_API extern const PrimitivePtr kPrimScalarUadd;
OPS_API extern const PrimitivePtr kPrimSelectV2;
OPS_API extern const PrimitivePtr kPrimScalarLe;
OPS_API extern const PrimitivePtr kPrimSequenceConcat;
OPS_API extern const PrimitivePtr kPrimSplit;
OPS_API extern const PrimitivePtr kPrimScalarLog;
OPS_API extern const PrimitivePtr kPrimScalarMin;
OPS_API extern const PrimitivePtr kPrimSoftmaxBackward;
OPS_API extern const PrimitivePtr kPrimScalarFloorDiv;
OPS_API extern const PrimitivePtr kPrimSilentCheckV2;
OPS_API extern const PrimitivePtr kPrimSvd;
OPS_API extern const PrimitivePtr kPrimScatterAddExt;
OPS_API extern const PrimitivePtr kPrimScalarLt;
OPS_API extern const PrimitivePtr kPrimScalarGt;
OPS_API extern const PrimitivePtr kPrimSoftShrink;
OPS_API extern const PrimitivePtr kPrimSqrt;
OPS_API extern const PrimitivePtr kPrimStridedSlice;
OPS_API extern const PrimitivePtr kPrimScalarAdd;
OPS_API extern const PrimitivePtr kPrimScalarToTensor;
OPS_API extern const PrimitivePtr kPrimScalarMax;
OPS_API extern const PrimitivePtr kPrimSoftplusGradExt;
OPS_API extern const PrimitivePtr kPrimSolveTriangular;
OPS_API extern const PrimitivePtr kPrimSmoothL1Loss;
OPS_API extern const PrimitivePtr kPrimSoftMarginLoss;
OPS_API extern const PrimitivePtr kPrimScalarEq;
OPS_API extern const PrimitivePtr kPrimScalarMod;
OPS_API extern const PrimitivePtr kPrimSubExt;
OPS_API extern const PrimitivePtr kPrimScalarMul;
OPS_API extern const PrimitivePtr kPrimSearchSorted;
OPS_API extern const PrimitivePtr kPrimSinc;
OPS_API extern const PrimitivePtr kPrimSinh;
OPS_API extern const PrimitivePtr kPrimSplitWithSize;
OPS_API extern const PrimitivePtr kPrimSpeedFusionAttentionGrad;
OPS_API extern const PrimitivePtr kPrimSplitTensorView;
OPS_API extern const PrimitivePtr kPrimSlice;
OPS_API extern const PrimitivePtr kPrimSliceExtView;
OPS_API extern const PrimitivePtr kPrimSumExt;
OPS_API extern const PrimitivePtr kPrimSelect;
OPS_API extern const PrimitivePtr kPrimScalarSub;
OPS_API extern const PrimitivePtr kPrimSwigluGrad;
OPS_API extern const PrimitivePtr kPrimStackExt;
OPS_API extern const PrimitivePtr kPrimSwiglu;
OPS_API extern const PrimitivePtr kPrimSubScalar;
OPS_API extern const PrimitivePtr kPrimScatterValue;
OPS_API extern const PrimitivePtr kPrimSliceExt;
OPS_API extern const PrimitivePtr kPrimSpeedFusionAttention;
OPS_API extern const PrimitivePtr kPrimStd;
OPS_API extern const PrimitivePtr kPrimSeLUExt;
OPS_API extern const PrimitivePtr kPrimStdMean;
OPS_API extern const PrimitivePtr kPrimSquare;
OPS_API extern const PrimitivePtr kPrimSqueeze;
OPS_API extern const PrimitivePtr kPrimSub;
OPS_API extern const PrimitivePtr kPrimScalarBool;
OPS_API extern const PrimitivePtr kPrimSoftShrinkGrad;
OPS_API extern const PrimitivePtr kPrimSiLU;
OPS_API extern const PrimitivePtr kPrimScalarCast;
OPS_API extern const PrimitivePtr kPrimSoftMarginLossGrad;
OPS_API extern const PrimitivePtr kPrimSigmoidGrad;
OPS_API extern const PrimitivePtr kPrimScalarUsub;
OPS_API extern const PrimitivePtr kPrimSplitWithSizeView;
OPS_API extern const PrimitivePtr kPrimSelectExtView;
OPS_API extern const PrimitivePtr kPrimSign;
OPS_API extern const PrimitivePtr kPrimShape;
OPS_API extern const PrimitivePtr kPrimScatter;
OPS_API extern const PrimitivePtr kPrimSortExt;
OPS_API extern const PrimitivePtr kPrimSilentCheckV3;
OPS_API extern const PrimitivePtr kPrimSin;
OPS_API extern const PrimitivePtr kPrimScalarGe;
OPS_API extern const PrimitivePtr kPrimScalarDiv;
OPS_API extern const PrimitivePtr kPrimSoftmax;
OPS_API extern const PrimitivePtr kPrimSmoothL1LossGrad;
OPS_API extern const PrimitivePtr kPrimSqrtGrad;
OPS_API extern const PrimitivePtr kPrimSeluGrad;
OPS_API extern const PrimitivePtr kPrimSwiGLUDynamicQuant;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_s_H_
