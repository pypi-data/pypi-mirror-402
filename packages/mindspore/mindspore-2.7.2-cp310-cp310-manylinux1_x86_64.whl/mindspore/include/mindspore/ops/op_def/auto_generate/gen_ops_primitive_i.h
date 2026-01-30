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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_i_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_i_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_i.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimInplaceClampScalar;
OPS_API extern const PrimitivePtr kPrimIndexFillTensor;
OPS_API extern const PrimitivePtr kPrimInplaceScatterAdd;
OPS_API extern const PrimitivePtr kPrimInplaceScatterSrc;
OPS_API extern const PrimitivePtr kPrimInplaceExp;
OPS_API extern const PrimitivePtr kPrimInplaceMuls;
OPS_API extern const PrimitivePtr kPrimInplaceAddExt;
OPS_API extern const PrimitivePtr kPrimInplaceUniform;
OPS_API extern const PrimitivePtr kPrimInplaceScatterValueReduce;
OPS_API extern const PrimitivePtr kPrimIHFFTN;
OPS_API extern const PrimitivePtr kPrimIm2ColExt;
OPS_API extern const PrimitivePtr kPrimIndex;
OPS_API extern const PrimitivePtr kPrimInplaceErfinv;
OPS_API extern const PrimitivePtr kPrimIndexFillScalar;
OPS_API extern const PrimitivePtr kPrimInplaceBernoulliScalar;
OPS_API extern const PrimitivePtr kPrimIRFFTN;
OPS_API extern const PrimitivePtr kPrimIFFTN;
OPS_API extern const PrimitivePtr kPrimIncreFlashAttention;
OPS_API extern const PrimitivePtr kPrimInplaceDivMods;
OPS_API extern const PrimitivePtr kPrimIsClose;
OPS_API extern const PrimitivePtr kPrimIFFTShift;
OPS_API extern const PrimitivePtr kPrimInplaceSubScalar;
OPS_API extern const PrimitivePtr kPrimInplaceRandom;
OPS_API extern const PrimitivePtr kPrimInplaceHardtanh;
OPS_API extern const PrimitivePtr kPrimInplaceNormal;
OPS_API extern const PrimitivePtr kPrimInplaceTanh;
OPS_API extern const PrimitivePtr kPrimInplaceIndexCopy;
OPS_API extern const PrimitivePtr kPrimInplaceReLU;
OPS_API extern const PrimitivePtr kPrimInplaceStopGradient;
OPS_API extern const PrimitivePtr kPrimIHFFT;
OPS_API extern const PrimitivePtr kPrimInplaceFloor;
OPS_API extern const PrimitivePtr kPrimInplaceMaskedFillTensor;
OPS_API extern const PrimitivePtr kPrimInplaceFloorDivides;
OPS_API extern const PrimitivePtr kPrimInplaceSign;
OPS_API extern const PrimitivePtr kPrimInplaceFillTensor;
OPS_API extern const PrimitivePtr kPrimInnerIndex;
OPS_API extern const PrimitivePtr kPrimInnerNonZero;
OPS_API extern const PrimitivePtr kPrimInplaceMul;
OPS_API extern const PrimitivePtr kPrimInplaceCopy;
OPS_API extern const PrimitivePtr kPrimInplaceSiLU;
OPS_API extern const PrimitivePtr kPrimIHFFT2;
OPS_API extern const PrimitivePtr kPrimInplaceElu;
OPS_API extern const PrimitivePtr kPrimInplaceThreshold;
OPS_API extern const PrimitivePtr kPrimInnerMoeTokenUnpermute;
OPS_API extern const PrimitivePtr kPrimIDCTN;
OPS_API extern const PrimitivePtr kPrimInplaceLog;
OPS_API extern const PrimitivePtr kPrimInplaceIndexFillScalar;
OPS_API extern const PrimitivePtr kPrimInplaceMatmulAdd;
OPS_API extern const PrimitivePtr kPrimInplaceMaskedScatter;
OPS_API extern const PrimitivePtr kPrimInplaceClampTensor;
OPS_API extern const PrimitivePtr kPrimInsertGemV2InBackward;
OPS_API extern const PrimitivePtr kPrimIsNegInf;
OPS_API extern const PrimitivePtr kPrimInplaceIndexFillTensor;
OPS_API extern const PrimitivePtr kPrimInplaceMaskedFillScalar;
OPS_API extern const PrimitivePtr kPrimInnerUnique;
OPS_API extern const PrimitivePtr kPrimIRFFTDouble;
OPS_API extern const PrimitivePtr kPrimInplaceDiv;
OPS_API extern const PrimitivePtr kPrimInplaceDivMod;
OPS_API extern const PrimitivePtr kPrimInplaceDivs;
OPS_API extern const PrimitivePtr kPrimIndexAddExt;
OPS_API extern const PrimitivePtr kPrimInplaceScatterSrcReduce;
OPS_API extern const PrimitivePtr kPrimInplaceIndexAddExt;
OPS_API extern const PrimitivePtr kPrimInplaceScatterValue;
OPS_API extern const PrimitivePtr kPrimInnerInplaceIndexPut;
OPS_API extern const PrimitivePtr kPrimInplaceSigmoid;
OPS_API extern const PrimitivePtr kPrimInplaceZero;
OPS_API extern const PrimitivePtr kPrimImagView;
OPS_API extern const PrimitivePtr kPrimInplaceFloorDivide;
OPS_API extern const PrimitivePtr kPrimInplaceFillScalar;
OPS_API extern const PrimitivePtr kPrimIDCT;
OPS_API extern const PrimitivePtr kPrimInplaceGroupedMatmulAdd;
OPS_API extern const PrimitivePtr kPrimIsFinite;
OPS_API extern const PrimitivePtr kPrimIRFFT;
OPS_API extern const PrimitivePtr kPrimInplaceRemainderTensorTensor;
OPS_API extern const PrimitivePtr kPrimIRFFT2;
OPS_API extern const PrimitivePtr kPrimInplaceAddmm;
OPS_API extern const PrimitivePtr kPrimInplaceRemainderTensorScalar;
OPS_API extern const PrimitivePtr kPrimInplacePut;
OPS_API extern const PrimitivePtr kPrimInplaceAddsExt;
OPS_API extern const PrimitivePtr kPrimInplaceBernoulliTensor;
OPS_API extern const PrimitivePtr kPrimInplaceFillDiagonal;
OPS_API extern const PrimitivePtr kPrimInplaceSubExt;
OPS_API extern const PrimitivePtr kPrimIFFT2;
OPS_API extern const PrimitivePtr kPrimIFFT;
OPS_API extern const PrimitivePtr kPrimIsInf;
OPS_API extern const PrimitivePtr kPrimInplaceIndexPut;
OPS_API extern const PrimitivePtr kPrimIndexSelect;
OPS_API extern const PrimitivePtr kPrimIdentity;
OPS_API extern const PrimitivePtr kPrimInnerCommReduceScatter;
OPS_API extern const PrimitivePtr kPrimInnerCommAllToAllV;
OPS_API extern const PrimitivePtr kPrimInnerCommAllGather;
OPS_API extern const PrimitivePtr kPrimInnerCommIsend;
OPS_API extern const PrimitivePtr kPrimInnerCommIrecv;
OPS_API extern const PrimitivePtr kPrimInnerCommAllReduce;
OPS_API extern const PrimitivePtr kPrimInplaceExponential;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_i_H_
