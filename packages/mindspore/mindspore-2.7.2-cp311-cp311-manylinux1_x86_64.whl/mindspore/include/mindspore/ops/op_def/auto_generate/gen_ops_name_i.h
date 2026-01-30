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
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameIndex = "Index";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
