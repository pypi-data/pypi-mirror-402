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
constexpr auto kNameIFFT = "IFFT";
constexpr auto kNameIFFTN = "IFFTN";
constexpr auto kNameInplaceIndexPut = "InplaceIndexPut";
constexpr auto kNameInplaceFillDiagonal = "InplaceFillDiagonal";
constexpr auto kNameIncreFlashAttention = "IncreFlashAttention";
constexpr auto kNameInplaceZero = "InplaceZero";
constexpr auto kNameInplaceScatterAdd = "InplaceScatterAdd";
constexpr auto kNameInnerNonZero = "InnerNonZero";
constexpr auto kNameInplaceFillTensor = "InplaceFillTensor";
constexpr auto kNameIndexAddExt = "IndexAddExt";
constexpr auto kNameInplaceGroupedMatmulAdd = "InplaceGroupedMatmulAdd";
constexpr auto kNameInplaceFloor = "InplaceFloor";
constexpr auto kNameInplaceRemainderTensorTensor = "InplaceRemainderTensorTensor";
constexpr auto kNameInplaceBernoulliScalar = "InplaceBernoulliScalar";
constexpr auto kNameIDCT = "IDCT";
constexpr auto kNameInplaceIndexFillScalar = "InplaceIndexFillScalar";
constexpr auto kNameInplaceLog = "InplaceLog";
constexpr auto kNameInplaceStopGradient = "InplaceStopGradient";
constexpr auto kNameIDCTN = "IDCTN";
constexpr auto kNameInplaceAddsExt = "InplaceAddsExt";
constexpr auto kNameInplaceIndexCopy = "InplaceIndexCopy";
constexpr auto kNameIndexFillScalar = "IndexFillScalar";
constexpr auto kNameInplaceMaskedFillScalar = "InplaceMaskedFillScalar";
constexpr auto kNameInplaceMaskedScatter = "InplaceMaskedScatter";
constexpr auto kNameInplaceDivMods = "InplaceDivMods";
constexpr auto kNameInplaceFloorDivides = "InplaceFloorDivides";
constexpr auto kNameInplaceFloorDivide = "InplaceFloorDivide";
constexpr auto kNameInplaceSign = "InplaceSign";
constexpr auto kNameInplacePut = "InplacePut";
constexpr auto kNameInplaceMaskedFillTensor = "InplaceMaskedFillTensor";
constexpr auto kNameInplaceRemainderTensorScalar = "InplaceRemainderTensorScalar";
constexpr auto kNameIndexFillTensor = "IndexFillTensor";
constexpr auto kNameInplaceClampScalar = "InplaceClampScalar";
constexpr auto kNameInplaceDivs = "InplaceDivs";
constexpr auto kNameInplaceTanh = "InplaceTanh";
constexpr auto kNameInnerUnique = "InnerUnique";
constexpr auto kNameInplaceSigmoid = "InplaceSigmoid";
constexpr auto kNameInplaceElu = "InplaceElu";
constexpr auto kNameIHFFT = "IHFFT";
constexpr auto kNameInplaceDivMod = "InplaceDivMod";
constexpr auto kNameInnerInplaceIndexPut = "InnerInplaceIndexPut";
constexpr auto kNameInplaceIndexFillTensor = "InplaceIndexFillTensor";
constexpr auto kNameInplaceThreshold = "InplaceThreshold";
constexpr auto kNameInplaceSiLU = "InplaceSiLU";
constexpr auto kNameInplaceMuls = "InplaceMuls";
constexpr auto kNameInplaceClampTensor = "InplaceClampTensor";
constexpr auto kNameInplaceScatterValueReduce = "InplaceScatterValueReduce";
constexpr auto kNameInplaceReLU = "InplaceReLU";
constexpr auto kNameInplaceScatterSrcReduce = "InplaceScatterSrcReduce";
constexpr auto kNameIRFFT2 = "IRFFT2";
constexpr auto kNameInplaceUniform = "InplaceUniform";
constexpr auto kNameInnerIndex = "InnerIndex";
constexpr auto kNameInplaceNormal = "InplaceNormal";
constexpr auto kNameIsNegInf = "IsNegInf";
constexpr auto kNameInplaceFillScalar = "InplaceFillScalar";
constexpr auto kNameIHFFTN = "IHFFTN";
constexpr auto kNameIsClose = "IsClose";
constexpr auto kNameInplaceExp = "InplaceExp";
constexpr auto kNameInnerMoeTokenUnpermute = "InnerMoeTokenUnpermute";
constexpr auto kNameInplaceBernoulliTensor = "InplaceBernoulliTensor";
constexpr auto kNameInplaceAddmm = "InplaceAddmm";
constexpr auto kNameImagView = "ImagView";
constexpr auto kNameIm2ColExt = "Im2ColExt";
constexpr auto kNameIRFFT = "IRFFT";
constexpr auto kNameIFFT2 = "IFFT2";
constexpr auto kNameInplaceScatterValue = "InplaceScatterValue";
constexpr auto kNameIsFinite = "IsFinite";
constexpr auto kNameInplaceScatterSrc = "InplaceScatterSrc";
constexpr auto kNameInplaceMul = "InplaceMul";
constexpr auto kNameIndex = "Index";
constexpr auto kNameIFFTShift = "IFFTShift";
constexpr auto kNameInplaceErfinv = "InplaceErfinv";
constexpr auto kNameInplaceMatmulAdd = "InplaceMatmulAdd";
constexpr auto kNameInplaceRandom = "InplaceRandom";
constexpr auto kNameInplaceHardtanh = "InplaceHardtanh";
constexpr auto kNameIHFFT2 = "IHFFT2";
constexpr auto kNameIndexSelect = "IndexSelect";
constexpr auto kNameInplaceCopy = "InplaceCopy";
constexpr auto kNameIsInf = "IsInf";
constexpr auto kNameInplaceSubScalar = "InplaceSubScalar";
constexpr auto kNameInplaceAddExt = "InplaceAddExt";
constexpr auto kNameIRFFTDouble = "IRFFTDouble";
constexpr auto kNameInplaceDiv = "InplaceDiv";
constexpr auto kNameIdentity = "Identity";
constexpr auto kNameInsertGemV2InBackward = "InsertGemV2InBackward";
constexpr auto kNameInplaceSubExt = "InplaceSubExt";
constexpr auto kNameIRFFTN = "IRFFTN";
constexpr auto kNameInplaceIndexAddExt = "InplaceIndexAddExt";
constexpr auto kNameInnerCommIsend = "InnerCommIsend";
constexpr auto kNameInnerCommReduceScatter = "InnerCommReduceScatter";
constexpr auto kNameInnerCommAllGather = "InnerCommAllGather";
constexpr auto kNameInnerCommIrecv = "InnerCommIrecv";
constexpr auto kNameInnerCommAllToAllV = "InnerCommAllToAllV";
constexpr auto kNameInnerCommAllReduce = "InnerCommAllReduce";
constexpr auto kNameInplaceExponential = "InplaceExponential";
}  // namespace mindspore::ops

#endif  // MINDSPORE_CORE_OP_NAME_I_H_
