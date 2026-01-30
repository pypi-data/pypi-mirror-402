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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_t_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_t_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_t.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimToOther;
OPS_API extern const PrimitivePtr kPrimTupleToList;
OPS_API extern const PrimitivePtr kPrimTransposeExtView;
OPS_API extern const PrimitivePtr kPrimTrilExt;
OPS_API extern const PrimitivePtr kPrimTypeAs;
OPS_API extern const PrimitivePtr kPrimTopPRouter;
OPS_API extern const PrimitivePtr kPrimTrunc;
OPS_API extern const PrimitivePtr kPrimThreshold;
OPS_API extern const PrimitivePtr kPrimTransposeView;
OPS_API extern const PrimitivePtr kPrimTanh;
OPS_API extern const PrimitivePtr kPrimTrace;
OPS_API extern const PrimitivePtr kPrimThresholdGrad;
OPS_API extern const PrimitivePtr kPrimTExt;
OPS_API extern const PrimitivePtr kPrimToDevice;
OPS_API extern const PrimitivePtr kPrimTensorCopySlices;
OPS_API extern const PrimitivePtr kPrimTranspose;
OPS_API extern const PrimitivePtr kPrimTanhGrad;
OPS_API extern const PrimitivePtr kPrimTensorScatterElements;
OPS_API extern const PrimitivePtr kPrimTopKRouter;
OPS_API extern const PrimitivePtr kPrimToDtype;
OPS_API extern const PrimitivePtr kPrimTraceV2Grad;
OPS_API extern const PrimitivePtr kPrimTopkExt;
OPS_API extern const PrimitivePtr kPrimTraceV2;
OPS_API extern const PrimitivePtr kPrimTensorShape;
OPS_API extern const PrimitivePtr kPrimTupleToTensor;
OPS_API extern const PrimitivePtr kPrimTake;
OPS_API extern const PrimitivePtr kPrimTraceExt;
OPS_API extern const PrimitivePtr kPrimTriangularSolve;
OPS_API extern const PrimitivePtr kPrimTan;
OPS_API extern const PrimitivePtr kPrimTensorScatterAdd;
OPS_API extern const PrimitivePtr kPrimTile;
OPS_API extern const PrimitivePtr kPrimTriu;
OPS_API extern const PrimitivePtr kPrimTransData;
OPS_API extern const PrimitivePtr kPrimTransposeBatchMatmulTranspose;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_t_H_
