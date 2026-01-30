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
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameIndex = "Index";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
