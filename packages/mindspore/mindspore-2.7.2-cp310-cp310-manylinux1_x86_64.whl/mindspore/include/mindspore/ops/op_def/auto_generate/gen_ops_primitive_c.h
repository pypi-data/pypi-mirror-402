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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_c_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_c_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_c.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimCumminExt;
OPS_API extern const PrimitivePtr kPrimCross;
OPS_API extern const PrimitivePtr kPrimConvolutionStrGrad;
OPS_API extern const PrimitivePtr kPrimCumsumExt;
OPS_API extern const PrimitivePtr kPrimChunkView;
OPS_API extern const PrimitivePtr kPrimConv1DPadding;
OPS_API extern const PrimitivePtr kPrimCopy;
OPS_API extern const PrimitivePtr kPrimConvolution;
OPS_API extern const PrimitivePtr kPrimConv3DExt;
OPS_API extern const PrimitivePtr kPrimCustomExt;
OPS_API extern const PrimitivePtr kPrimConvolutionGrad;
OPS_API extern const PrimitivePtr kPrimComplex;
OPS_API extern const PrimitivePtr kPrimCol2ImExt;
OPS_API extern const PrimitivePtr kPrimConcat;
OPS_API extern const PrimitivePtr kPrimCos;
OPS_API extern const PrimitivePtr kPrimConstantPadND;
OPS_API extern const PrimitivePtr kPrimCrossEntropyLoss;
OPS_API extern const PrimitivePtr kPrimCdistGrad;
OPS_API extern const PrimitivePtr kPrimCumSum;
OPS_API extern const PrimitivePtr kPrimClone;
OPS_API extern const PrimitivePtr kPrimCummax;
OPS_API extern const PrimitivePtr kPrimCumProd;
OPS_API extern const PrimitivePtr kPrimCast;
OPS_API extern const PrimitivePtr kPrimCummin;
OPS_API extern const PrimitivePtr kPrimClampTensor;
OPS_API extern const PrimitivePtr kPrimConv2DExt;
OPS_API extern const PrimitivePtr kPrimCholesky;
OPS_API extern const PrimitivePtr kPrimChunk;
OPS_API extern const PrimitivePtr kPrimContiguous;
OPS_API extern const PrimitivePtr kPrimConv2DPadding;
OPS_API extern const PrimitivePtr kPrimCeil;
OPS_API extern const PrimitivePtr kPrimCorrelate;
OPS_API extern const PrimitivePtr kPrimConv3DPadding;
OPS_API extern const PrimitivePtr kPrimCeLU;
OPS_API extern const PrimitivePtr kPrimCountNonZero;
OPS_API extern const PrimitivePtr kPrimCol2ImGrad;
OPS_API extern const PrimitivePtr kPrimCdist;
OPS_API extern const PrimitivePtr kPrimConvTranspose2D;
OPS_API extern const PrimitivePtr kPrimCellBackwardHook;
OPS_API extern const PrimitivePtr kPrimCosh;
OPS_API extern const PrimitivePtr kPrimClampScalar;
OPS_API extern const PrimitivePtr kPrimConj;
OPS_API extern const PrimitivePtr kPrimCholeskyInverse;
OPS_API extern const PrimitivePtr kPrimCrossEntropyLossGrad;
OPS_API extern const PrimitivePtr kPrimConvolutionStr;
OPS_API extern const PrimitivePtr kPrimConv1DExt;
OPS_API extern const PrimitivePtr kPrimCholeskyGrad;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_c_H_
