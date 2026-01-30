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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_b_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_b_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_b.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimBroadcastTo;
OPS_API extern const PrimitivePtr kPrimBinaryCrossEntropyGrad;
OPS_API extern const PrimitivePtr kPrimBincountExt;
OPS_API extern const PrimitivePtr kPrimBernoulliExt;
OPS_API extern const PrimitivePtr kPrimBatchNormGatherStatsWithCounts;
OPS_API extern const PrimitivePtr kPrimBatchNormWithActivation;
OPS_API extern const PrimitivePtr kPrimBiasAddGrad;
OPS_API extern const PrimitivePtr kPrimBatchMatMul;
OPS_API extern const PrimitivePtr kPrimBiasAdd;
OPS_API extern const PrimitivePtr kPrimBinaryCrossEntropy;
OPS_API extern const PrimitivePtr kPrimBitwiseOrTensor;
OPS_API extern const PrimitivePtr kPrimBitwiseXorTensor;
OPS_API extern const PrimitivePtr kPrimBaddbmm;
OPS_API extern const PrimitivePtr kPrimBatchNormGradExt;
OPS_API extern const PrimitivePtr kPrimBitwiseNot;
OPS_API extern const PrimitivePtr kPrimBoolNot;
OPS_API extern const PrimitivePtr kPrimBCEWithLogitsLoss;
OPS_API extern const PrimitivePtr kPrimBatchNorm;
OPS_API extern const PrimitivePtr kPrimBatchNormGradGrad;
OPS_API extern const PrimitivePtr kPrimBinaryCrossEntropyWithLogitsBackward;
OPS_API extern const PrimitivePtr kPrimBatchNormGradWithActivation;
OPS_API extern const PrimitivePtr kPrimBatchNormWithAddAndActivation;
OPS_API extern const PrimitivePtr kPrimBatchNormElemt;
OPS_API extern const PrimitivePtr kPrimBatchMatMulExt;
OPS_API extern const PrimitivePtr kPrimBatchNormGrad;
OPS_API extern const PrimitivePtr kPrimBatchNormStats;
OPS_API extern const PrimitivePtr kPrimBatchNormGradWithAddAndActivation;
OPS_API extern const PrimitivePtr kPrimBitwiseAndScalar;
OPS_API extern const PrimitivePtr kPrimBatchNormReduceGrad;
OPS_API extern const PrimitivePtr kPrimBatchNormElemtGrad;
OPS_API extern const PrimitivePtr kPrimBetainc;
OPS_API extern const PrimitivePtr kPrimBroadcastToView;
OPS_API extern const PrimitivePtr kPrimBitwiseXorScalar;
OPS_API extern const PrimitivePtr kPrimBitwiseOrScalar;
OPS_API extern const PrimitivePtr kPrimBatchNormExt;
OPS_API extern const PrimitivePtr kPrimBitwiseAndTensor;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_b_H_
