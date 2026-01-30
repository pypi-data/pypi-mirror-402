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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_l_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_l_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_l.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimLeakyReLUExt;
OPS_API extern const PrimitivePtr kPrimL1LossExt;
OPS_API extern const PrimitivePtr kPrimLayerNorm;
OPS_API extern const PrimitivePtr kPrimLpNormV2;
OPS_API extern const PrimitivePtr kPrimLinSpaceExt;
OPS_API extern const PrimitivePtr kPrimLinSpace;
OPS_API extern const PrimitivePtr kPrimLinalgVectorNorm;
OPS_API extern const PrimitivePtr kPrimLerp;
OPS_API extern const PrimitivePtr kPrimLogSigmoid;
OPS_API extern const PrimitivePtr kPrimLayerNormGradGrad;
OPS_API extern const PrimitivePtr kPrimLstsqV2Grad;
OPS_API extern const PrimitivePtr kPrimLayerNormGradV3;
OPS_API extern const PrimitivePtr kPrimLayerNormGradExt;
OPS_API extern const PrimitivePtr kPrimLinalgQr;
OPS_API extern const PrimitivePtr kPrimLayerNormV3;
OPS_API extern const PrimitivePtr kPrimLogMatrixDeterminant;
OPS_API extern const PrimitivePtr kPrimLog1p;
OPS_API extern const PrimitivePtr kPrimLayerNormGrad;
OPS_API extern const PrimitivePtr kPrimLayerNormExt;
OPS_API extern const PrimitivePtr kPrimLeakyReLUGradExt;
OPS_API extern const PrimitivePtr kPrimLogAddExp2;
OPS_API extern const PrimitivePtr kPrimListToTuple;
OPS_API extern const PrimitivePtr kPrimLogicalOr;
OPS_API extern const PrimitivePtr kPrimLerpScalar;
OPS_API extern const PrimitivePtr kPrimLogit;
OPS_API extern const PrimitivePtr kPrimL1LossBackwardExt;
OPS_API extern const PrimitivePtr kPrimLogAddExp;
OPS_API extern const PrimitivePtr kPrimLogicalNot;
OPS_API extern const PrimitivePtr kPrimLog2;
OPS_API extern const PrimitivePtr kPrimLogSoftmaxExt;
OPS_API extern const PrimitivePtr kPrimLogSumExp;
OPS_API extern const PrimitivePtr kPrimLogicalAnd;
OPS_API extern const PrimitivePtr kPrimLessEqual;
OPS_API extern const PrimitivePtr kPrimLogSoftmaxGrad;
OPS_API extern const PrimitivePtr kPrimLogicalXor;
OPS_API extern const PrimitivePtr kPrimLogSoftmax;
OPS_API extern const PrimitivePtr kPrimLog;
OPS_API extern const PrimitivePtr kPrimLogSigmoidGrad;
OPS_API extern const PrimitivePtr kPrimLogitGrad;
OPS_API extern const PrimitivePtr kPrimLstsqV2;
OPS_API extern const PrimitivePtr kPrimLog10;
OPS_API extern const PrimitivePtr kPrimLess;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_l_H_
