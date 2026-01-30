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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_g_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_g_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_g.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimGeLU;
OPS_API extern const PrimitivePtr kPrimGcd;
OPS_API extern const PrimitivePtr kPrimGeluExt;
OPS_API extern const PrimitivePtr kPrimGatherNdExt;
OPS_API extern const PrimitivePtr kPrimGenerator;
OPS_API extern const PrimitivePtr kPrimGatherDGradV2;
OPS_API extern const PrimitivePtr kPrimGroupTopk;
OPS_API extern const PrimitivePtr kPrimGluGrad;
OPS_API extern const PrimitivePtr kPrimGeqrf;
OPS_API extern const PrimitivePtr kPrimGatherNd;
OPS_API extern const PrimitivePtr kPrimGeluGradExt;
OPS_API extern const PrimitivePtr kPrimGreaterEqual;
OPS_API extern const PrimitivePtr kPrimGather;
OPS_API extern const PrimitivePtr kPrimGroupNorm;
OPS_API extern const PrimitivePtr kPrimGreater;
OPS_API extern const PrimitivePtr kPrimGroupNormGrad;
OPS_API extern const PrimitivePtr kPrimGenerateEodMaskV2;
OPS_API extern const PrimitivePtr kPrimGeLUGrad;
OPS_API extern const PrimitivePtr kPrimGridSampler3DGrad;
OPS_API extern const PrimitivePtr kPrimGreaterEqualScalar;
OPS_API extern const PrimitivePtr kPrimGridSampler3D;
OPS_API extern const PrimitivePtr kPrimGridSampler2DGrad;
OPS_API extern const PrimitivePtr kPrimGatherD;
OPS_API extern const PrimitivePtr kPrimGridSampler2D;
OPS_API extern const PrimitivePtr kPrimGLU;
OPS_API extern const PrimitivePtr kPrimGroupedMatmulV2;
OPS_API extern const PrimitivePtr kPrimGroupedMatmulV4;
OPS_API extern const PrimitivePtr kPrimGroupedMatmul;
OPS_API extern const PrimitivePtr kPrimGmmV2Backward;
OPS_API extern const PrimitivePtr kPrimGmmBackward;
OPS_API extern const PrimitivePtr kPrimGmm;
OPS_API extern const PrimitivePtr kPrimGmmV2BackwardFusion;
OPS_API extern const PrimitivePtr kPrimGmmBackwardFusion;
OPS_API extern const PrimitivePtr kPrimGmmV2;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_g_H_
