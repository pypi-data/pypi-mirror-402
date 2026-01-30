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
#ifndef MINDSPORE_CORE_OP_NAME_I_H_
#define MINDSPORE_CORE_OP_NAME_I_H_

namespace mindspore::ops {
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameIndex = "Index";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
