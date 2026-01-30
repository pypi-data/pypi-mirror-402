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
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameIndex = "Index";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
