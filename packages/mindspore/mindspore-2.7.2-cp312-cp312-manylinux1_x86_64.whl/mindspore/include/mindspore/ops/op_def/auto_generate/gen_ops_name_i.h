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
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameIndex = "Index";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
