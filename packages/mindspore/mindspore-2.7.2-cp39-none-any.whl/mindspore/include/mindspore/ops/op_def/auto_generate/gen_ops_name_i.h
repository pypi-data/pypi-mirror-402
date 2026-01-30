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
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameIndex = "Index";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
