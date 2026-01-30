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
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameIndex = "Index";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
