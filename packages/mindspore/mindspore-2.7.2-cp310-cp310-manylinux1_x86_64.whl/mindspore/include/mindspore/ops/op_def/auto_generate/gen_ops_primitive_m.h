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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_m_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_m_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_m.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimMinimum;
OPS_API extern const PrimitivePtr kPrimMaximum;
OPS_API extern const PrimitivePtr kPrimMSELossGradExt;
OPS_API extern const PrimitivePtr kPrimMaximumGradGrad;
OPS_API extern const PrimitivePtr kPrimMm;
OPS_API extern const PrimitivePtr kPrimMuls;
OPS_API extern const PrimitivePtr kPrimMultiScaleDeformableAttnGrad;
OPS_API extern const PrimitivePtr kPrimMultiScaleDeformableAttn;
OPS_API extern const PrimitivePtr kPrimMSELossExt;
OPS_API extern const PrimitivePtr kPrimMinimumGrad;
OPS_API extern const PrimitivePtr kPrimMatrixDeterminant;
OPS_API extern const PrimitivePtr kPrimMishExt;
OPS_API extern const PrimitivePtr kPrimMaximumGrad;
OPS_API extern const PrimitivePtr kPrimMoeDistributeCombine;
OPS_API extern const PrimitivePtr kPrimMaskedScatter;
OPS_API extern const PrimitivePtr kPrimMishGradExt;
OPS_API extern const PrimitivePtr kPrimMaxUnpool2DExt;
OPS_API extern const PrimitivePtr kPrimMeanExt;
OPS_API extern const PrimitivePtr kPrimMeshgrid;
OPS_API extern const PrimitivePtr kPrimMedianDim;
OPS_API extern const PrimitivePtr kPrimMaxPoolGradWithIndices;
OPS_API extern const PrimitivePtr kPrimMinDim;
OPS_API extern const PrimitivePtr kPrimMaxDim;
OPS_API extern const PrimitivePtr kPrimMultinomialExt;
OPS_API extern const PrimitivePtr kPrimMatMul;
OPS_API extern const PrimitivePtr kPrimMaskedSelectGrad;
OPS_API extern const PrimitivePtr kPrimMla;
OPS_API extern const PrimitivePtr kPrimMedianExt;
OPS_API extern const PrimitivePtr kPrimMatmulReduceScatter;
OPS_API extern const PrimitivePtr kPrimMoeDistributeDispatch;
OPS_API extern const PrimitivePtr kPrimMul;
OPS_API extern const PrimitivePtr kPrimMaskedFill;
OPS_API extern const PrimitivePtr kPrimMaskedFillScalar;
OPS_API extern const PrimitivePtr kPrimMatrixExp;
OPS_API extern const PrimitivePtr kPrimMaskedSelect;
OPS_API extern const PrimitivePtr kPrimMax;
OPS_API extern const PrimitivePtr kPrimMlaPreprocess;
OPS_API extern const PrimitivePtr kPrimMoeTokenPermuteGrad;
OPS_API extern const PrimitivePtr kPrimMin;
OPS_API extern const PrimitivePtr kPrimMoeTokenUnpermuteGrad;
OPS_API extern const PrimitivePtr kPrimMaxPoolWithIndices;
OPS_API extern const PrimitivePtr kPrimMatMulExt;
OPS_API extern const PrimitivePtr kPrimMoeTokenPermute;
OPS_API extern const PrimitivePtr kPrimMv;
OPS_API extern const PrimitivePtr kPrimMaxPoolGradWithMask;
OPS_API extern const PrimitivePtr kPrimMaxPoolWithMask;
OPS_API extern const PrimitivePtr kPrimMatrixInverseExt;
OPS_API extern const PrimitivePtr kPrimMoeFinalizeRouting;
OPS_API extern const PrimitivePtr kPrimMatmulBiasSplitOut3;
OPS_API extern const PrimitivePtr kPrimMatmulSplitOut3;
OPS_API extern const PrimitivePtr kPrimMoeComputeExpertTokens;
OPS_API extern const PrimitivePtr kPrimMoeInitRoutingV2;
OPS_API extern const PrimitivePtr kPrimMatmulSplitSiluMulOut1;
OPS_API extern const PrimitivePtr kPrimMatmulSplitSiluFastgeluAddMulOut1;
OPS_API extern const PrimitivePtr kPrimMoeInitRoutingQuantV2;
OPS_API extern const PrimitivePtr kPrimMatmulSplitSiluOut2;
OPS_API extern const PrimitivePtr kPrimMoeInitRouting;
OPS_API extern const PrimitivePtr kPrimMatmulSplitOut2;
OPS_API extern const PrimitivePtr kPrimMatmulBiasSplitOut2;
OPS_API extern const PrimitivePtr kPrimMatmulAllReduceAddRmsNorm;
OPS_API extern const PrimitivePtr kPrimMatmulBiasSplitSiluOut2;
OPS_API extern const PrimitivePtr kPrimMoeGatingTopKSoftmax;
OPS_API extern const PrimitivePtr kPrimMoeTokenUnpermute;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_m_H_
