/**
 * Copyright 2024 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_MINDSPORE_OPS_KERNEL_FUNCTIONS_AUTO_GENERATE_AUTO_GRAD_OP_REG_H_
#define MINDSPORE_MINDSPORE_OPS_KERNEL_FUNCTIONS_AUTO_GENERATE_AUTO_GRAD_OP_REG_H_

#include <functional>
#include <any>
#include <unordered_map>
#include "mindspore/ccsrc/pyboost/op_runner.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
enum class OpType {
  kCosh = 0,
  kRandLikeExt = 1,
  kMSELossExt = 2,
  kGeLU = 3,
  kMedianExt = 4,
  kProdExt = 5,
  kToOther = 6,
  kEqual = 7,
  kFrac = 8,
  kInplaceExp = 9,
  kInplaceClampTensor = 10,
  kBatchNormReduceGrad = 11,
  kRepeatInterleaveInt = 12,
  kUpsampleBicubic2DGrad = 13,
  kInplaceAddmm = 14,
  kInplaceSubScalar = 15,
  kInplaceLog = 16,
  kInnerIndex = 17,
  kKLDiv = 18,
  kRsqrt = 19,
  kLess = 20,
  kEluExt = 21,
  kSinh = 22,
  kLogAddExp = 23,
  kAsinExt = 24,
  kErf = 25,
  kAsinhExt = 26,
  kInplaceRandom = 27,
  kGreater = 28,
  kLog2 = 29,
  kErfinv = 30,
  kTransposeExtView = 31,
  kVarMean = 32,
  kLayerNormExt = 33,
  kBitwiseNot = 34,
  kAvgPool1D = 35,
  kAddbmm = 36,
  kAtan2Ext = 37,
  kLerp = 38,
  kFlashAttentionScore = 39,
  kBitwiseXorScalar = 40,
  kIsInf = 41,
  kMaxPoolWithMask = 42,
  kCustomExt = 43,
  kEye = 44,
  kTrilExt = 45,
  kSeluGrad = 46,
  kBatchNormExt = 47,
  kUpsampleNearest3DGrad = 48,
  kPolar = 49,
  kArgMinExt = 50,
  kNeScalar = 51,
  kTypeAs = 52,
  kSqrt = 53,
  kLogicalNot = 54,
  kIsFinite = 55,
  kBinaryCrossEntropyGrad = 56,
  kReflectionPad1D = 57,
  kMatrixInverseExt = 58,
  kNormalTensorTensor = 59,
  kSplitWithSizeView = 60,
  kInplaceDivs = 61,
  kSoftmax = 62,
  kMaskedFillScalar = 63,
  kConvolution = 64,
  kSplitWithSize = 65,
  kPagedAttention = 66,
  kStd = 67,
  kRemainderTensorScalar = 68,
  kBitwiseAndScalar = 69,
  kMultinomialExt = 70,
  kSoftMarginLossGrad = 71,
  kLogAddExp2 = 72,
  kCrossEntropyLossGrad = 73,
  kReshapeAndCache = 74,
  kInplaceDivMods = 75,
  kTrunc = 76,
  kChunkView = 77,
  kRingAttentionUpdate = 78,
  kSelectV2 = 79,
  kMaskedScatter = 80,
  kUniqueConsecutive = 81,
  kReduceMax = 82,
  kRound = 83,
  kMaskedSelectGrad = 84,
  kAdamW = 85,
  kUpsampleBilinear2D = 86,
  kGLU = 87,
  kDiagonalView = 88,
  kScatterAddExt = 89,
  kNonZero = 90,
  kAddScalar = 91,
  kMedianDim = 92,
  kInplaceSign = 93,
  kThreshold = 94,
  kNLLLoss2dGrad = 95,
  kNorm = 96,
  kNewZeros = 97,
  kNarrow = 98,
  kBatchMatMulExt = 99,
  kAvgPool3DExt = 100,
  kAvgPool3DGradExt = 101,
  kExpandDims = 102,
  kRotaryPositionEmbeddingGrad = 103,
  kCrossEntropyLoss = 104,
  kBatchNormElemt = 105,
  kGroupNorm = 106,
  kSlice = 107,
  kFloor = 108,
  kMatMul = 109,
  kInplaceElu = 110,
  kInplaceMatmulAdd = 111,
  kMatMulExt = 112,
  kSpeedFusionAttentionGrad = 113,
  kNonZeroExt = 114,
  kPReLUGrad = 115,
  kMaskedFill = 116,
  kSearchSorted = 117,
  kInplaceSigmoid = 118,
  kMaximum = 119,
  kReduceAny = 120,
  kArange = 121,
  kOnes = 122,
  kHSwish = 123,
  kClone = 124,
  kReciprocal = 125,
  kAddExt = 126,
  kSigmoid = 127,
  kInplaceMaskedScatter = 128,
  kSelectExtView = 129,
  kLog10 = 130,
  kInplaceThreshold = 131,
  kTransposeView = 132,
  kGridSampler2DGrad = 133,
  kStdMean = 134,
  kBatchMatMul = 135,
  kMoeTokenPermuteGrad = 136,
  kBatchNormGatherStatsWithCounts = 137,
  kL1LossExt = 138,
  kAsStrided = 139,
  kTanh = 140,
  kGenerator = 141,
  kLogSigmoid = 142,
  kAddmm = 143,
  kHardtanh = 144,
  kLayerNormGradExt = 145,
  kBitwiseOrScalar = 146,
  kLogSoftmaxExt = 147,
  kInplaceCopy = 148,
  kReplicationPad2DGrad = 149,
  kRepeat = 150,
  kMultiScaleDeformableAttn = 151,
  kGluGrad = 152,
  kEmbeddingDenseBackward = 153,
  kInplaceFloorDivides = 154,
  kCummax = 155,
  kMv = 156,
  kInnerMoeTokenUnpermute = 157,
  kRotaryPositionEmbedding = 158,
  kReflectionPad3DGrad = 159,
  kInplaceSubExt = 160,
  kGridSampler2D = 161,
  kReplicationPad1D = 162,
  kLogSumExp = 163,
  kFillScalar = 164,
  kInplaceZero = 165,
  kLog = 166,
  kInplaceUniform = 167,
  kSplitTensorView = 168,
  kRandn = 169,
  kIndexFillTensor = 170,
  kAdaptiveAvgPool2DGradExt = 171,
  kInplaceHardtanh = 172,
  kMaxPoolGradWithIndices = 173,
  kExp = 174,
  kInplaceIndexCopy = 175,
  kAdaptiveAvgPool3DGradExt = 176,
  kConv1DPadding = 177,
  kInplaceDivMod = 178,
  kDequantSwigluQuant = 179,
  kRandExt = 180,
  kLogSigmoidGrad = 181,
  kThresholdGrad = 182,
  kTExt = 183,
  kSinc = 183,
  kGeluGradExt = 184,
  kSqueeze = 185,
  kInnerNonZero = 186,
  kEmptyLike = 187,
  kPow = 188,
  kSigmoidGrad = 189,
  kUnique2 = 190,
  kBitwiseOrTensor = 191,
  kEluGradExt = 192,
  kUniformExt = 193,
  kReflectionPad1DGrad = 194,
  kHSigmoid = 195,
  kInplaceMul = 196,
  kToDevice = 197,
  kAtanExt = 198,
  kHistcExt = 199,
  kSilentCheckV2 = 200,
  kRemainderScalarTensor = 201,
  kSwigluGrad = 202,
  kExpandDimsView = 203,
  kIdentity = 204,
  kHShrinkGrad = 205,
  kRmsNormGrad = 206,
  kOnesLikeExt = 207,
  kConstantPadND = 208,
  kArgMaxExt = 209,
  kInplaceDiv = 210,
  kRoll = 211,
  kExpm1 = 212,
  kNormalFloatTensor = 213,
  kPowTensorScalar = 214,
  kFmodTensor = 215,
  kCumminExt = 216,
  kCountNonZero = 217,
  kSin = 218,
  kCol2ImExt = 219,
  kGridSampler3D = 220,
  kSoftMarginLoss = 221,
  kConv2DPadding = 222,
  kSliceExtView = 223,
  kKthvalue = 224,
  kInplaceFloorDivide = 225,
  kMishGradExt = 226,
  kGroupNormGrad = 227,
  kReplicationPad3DGrad = 228,
  kArgSort = 229,
  kInplacePut = 230,
  kNewEmpty = 231,
  kFmodScalar = 232,
  kDropoutExt = 233,
  kPReLU = 234,
  kZerosLikeExt = 235,
  kCopy = 236,
  kTranspose = 237,
  kConv2DExt = 238,
  kInplaceIndexFillScalar = 239,
  kKLDivGrad = 240,
  kSeLUExt = 241,
  kXLogYScalarSelf = 242,
  kSiLUGrad = 243,
  kGridSampler3DGrad = 244,
  kErfc = 245,
  kPowScalarTensor = 246,
  kUpsampleLinear1DGrad = 247,
  kLogicalAnd = 248,
  kCeil = 249,
  kSliceExt = 250,
  kReflectionPad3D = 251,
  kSign = 252,
  kRepeatInterleaveTensor = 253,
  kGeLUGrad = 254,
  kApplyRotaryPosEmb = 255,
  kUpsampleTrilinear3DGrad = 256,
  kUpsampleNearest2DGrad = 257,
  kInnerInplaceIndexPut = 258,
  kInplaceScatterAdd = 259,
  kAdaptiveAvgPool2DExt = 260,
  kNewFull = 261,
  kRealView = 262,
  kBinaryCrossEntropy = 263,
  kInplaceScatterSrcReduce = 264,
  kConcat = 265,
  kSoftplusGradExt = 266,
  kMatmulReduceScatter = 267,
  kDivMod = 268,
  kInplaceAddExt = 269,
  kConv1DExt = 270,
  kSoftShrinkGrad = 271,
  kGeluExt = 272,
  kNLLLossGrad = 273,
  kElu = 274,
  kAvgPool2DGrad = 275,
  kDiv = 276,
  kLinalgVectorNorm = 277,
  kBincountExt = 278,
  kChunk = 279,
  kBatchNormStats = 280,
  kNeg = 281,
  kInplaceFloor = 282,
  kInplaceScatterSrc = 283,
  kNotEqual = 284,
  kLinSpaceExt = 285,
  kViewAs = 286,
  kLeakyReLUExt = 286,
  kInplaceClampScalar = 287,
  kClampTensor = 288,
  kSmoothL1Loss = 289,
  kReduceMin = 290,
  kAddmv = 291,
  kSubScalar = 292,
  kInplaceBernoulliScalar = 293,
  kVar = 294,
  kInnerUnique = 295,
  kTanhGrad = 296,
  kAddcdivExt = 297,
  kAddcmulExt = 298,
  kAddRmsNorm = 299,
  kGreaterEqual = 300,
  kSiLU = 301,
  kFillTensor = 302,
  kEmpty = 303,
  kReplicationPad1DGrad = 304,
  kRmsNorm = 305,
  kGatherNdExt = 306,
  kIm2ColExt = 307,
  kMinDim = 308,
  kGatherDGradV2 = 309,
  kInplaceMaskedFillTensor = 310,
  kReLU = 311,
  kTensorScatterElements = 312,
  kLog1p = 313,
  kNormalTensorFloat = 314,
  kAllFinite = 315,
  kSilentCheckV3 = 316,
  kEqualExt = 317,
  kReluGrad = 318,
  kDivs = 319,
  kAdaptiveMaxPool1D = 320,
  kSwiglu = 321,
  kNanToNum = 322,
  kAllGatherMatmul = 323,
  kNLLLoss = 324,
  kReflectionPad2D = 325,
  kInplaceErfinv = 326,
  kToDtype = 327,
  kLinalgQr = 328,
  kMoeTokenPermute = 329,
  kDivMods = 330,
  kRandnLike = 331,
  kReshape = 332,
  kIndexFillScalar = 333,
  kFullLike = 334,
  kMla = 335,
  kInplaceTanh = 336,
  kRandIntLike = 337,
  kInplaceRemainderTensorScalar = 338,
  kFloorDivScalar = 339,
  kMaskedSelect = 340,
  kSpeedFusionAttention = 341,
  kInplaceMuls = 342,
  kInplaceReLU = 343,
  kConvolutionGrad = 344,
  kImagView = 345,
  kDropoutGradExt = 346,
  kHSwishGrad = 347,
  kL1LossBackwardExt = 348,
  kBroadcastToView = 349,
  kOuter = 350,
  kCumsumExt = 351,
  kClampScalar = 352,
  kNormalFloatFloat = 353,
  kIndex = 354,
  kTopkExt = 355,
  kArgMinWithValue = 356,
  kXlogy = 357,
  kSquare = 358,
  kBinaryCrossEntropyWithLogitsBackward = 359,
  kXLogYScalarOther = 360,
  kBroadcastTo = 361,
  kDropoutDoMaskExt = 362,
  kHardtanhGrad = 363,
  kBernoulliExt = 364,
  kBatchNormElemtGrad = 365,
  kMaxPoolWithIndices = 366,
  kLessEqual = 367,
  kInplaceRemainderTensorTensor = 368,
  kReplicationPad3D = 369,
  kInplaceFillScalar = 370,
  kSoftplusExt = 371,
  kAddLayerNormGrad = 372,
  kFlattenExt = 373,
  kSplit = 373,
  kExpandAs = 374,
  kNewOnes = 374,
  kLeakyReLUGradExt = 375,
  kScatterValue = 376,
  kSortExt = 377,
  kAdaptiveAvgPool3DExt = 378,
  kConv3DExt = 379,
  kIncreFlashAttention = 380,
  kMaxUnpool2DExt = 381,
  kInplaceIndexPut = 382,
  kHSigmoidGrad = 383,
  kFlashAttentionScoreGrad = 384,
  kAcoshExt = 385,
  kMoeDistributeCombine = 386,
  kMeanExt = 387,
  kZeros = 388,
  kInplaceAddsExt = 389,
  kConvolutionStr = 390,
  kAcosExt = 391,
  kHShrink = 392,
  kMinimum = 393,
  kSubExt = 394,
  kRandInt = 395,
  kInplaceBernoulliTensor = 396,
  kBitwiseAndTensor = 397,
  kInplaceIndexAddExt = 398,
  kAdd = 399,
  kNLLLoss2d = 400,
  kInplaceScatterValueReduce = 401,
  kLogicalOr = 402,
  kTake = 403,
  kSub = 404,
  kAtanh = 405,
  kDense = 406,
  kTraceExt = 407,
  kInplaceSiLU = 408,
  kPromptFlashAttention = 409,
  kCross = 410,
  kUnstackExtView = 411,
  kInplaceNormal = 412,
  kMm = 413,
  kIndexSelect = 414,
  kTriangularSolve = 415,
  kIsNegInf = 416,
  kCol2ImGrad = 417,
  kConvolutionStrGrad = 418,
  kFFNExt = 419,
  kAdaptiveAvgPool1D = 420,
  kCast = 421,
  kMishExt = 422,
  kDiagExt = 423,
  kInplaceScatterValue = 424,
  kRemainderTensorTensor = 425,
  kLerpScalar = 426,
  kCellBackwardHook = 427,
  kLogicalXor = 428,
  kMeshgrid = 429,
  kUpsampleNearest2D = 429,
  kConvTranspose2D = 430,
  kUniqueDim = 431,
  kInplaceStopGradient = 432,
  kReverseV2 = 433,
  kReduceAll = 434,
  kDropoutGenMaskExt = 435,
  kMin = 436,
  kCos = 437,
  kTan = 438,
  kMoeDistributeDispatch = 439,
  kReplicationPad2D = 440,
  kBaddbmm = 441,
  kMSELossGradExt = 442,
  kUpsampleNearest1D = 443,
  kUpsampleLinear1D = 444,
  kLogSoftmax = 445,
  kUpsampleBilinear2DGrad = 446,
  kSoftmaxBackward = 447,
  kInplaceFillDiagonal = 448,
  kStackExt = 449,
  kTensorScatterAdd = 450,
  kMuls = 451,
  kUpsampleNearest3D = 452,
  kTile = 453,
  kAdaptiveMaxPool2D = 454,
  kUpsampleBicubic2D = 455,
  kBitwiseXorTensor = 456,
  kNarrowView = 457,
  kMax = 458,
  kInplaceIndexFillTensor = 459,
  kEmbedding = 460,
  kIndexAddExt = 461,
  kMul = 462,
  kSelect = 463,
  kBCEWithLogitsLoss = 464,
  kConv3DPadding = 465,
  kMultiScaleDeformableAttnGrad = 466,
  kGatherD = 467,
  kNansum = 468,
  kGreaterEqualScalar = 469,
  kIsClose = 470,
  kInplaceMaskedFillScalar = 471,
  kBatchNormGradExt = 472,
  kInplaceFillTensor = 473,
  kExp2 = 474,
  kInplaceGroupedMatmulAdd = 475,
  kUpsampleTrilinear3D = 476,
  kOneHotExt = 477,
  kMaxDim = 478,
  kDot = 479,
  kSmoothL1LossGrad = 480,
  kReflectionPad2DGrad = 481,
  kScatter = 482,
  kMaxPoolGradWithMask = 483,
  kGcd = 484,
  kView = 485,
  kSoftShrink = 486,
  kSplitTensor = 487,
  kAbs = 488,
  kUpsampleNearest1DGrad = 489,
  kFloorDiv = 490,
  kLogSoftmaxGrad = 491,
  kSumExt = 492,
  kArgMaxWithValue = 493,
  kAvgPool2D = 494,
  kContiguous = 495,
  kRepeatInterleaveGrad = 496,
  kTriu = 497,
  kRandpermExt = 498,
  kMoeTokenUnpermuteGrad = 499,
  kAddLayerNormV2 = 500,
  kQuantV2 = 501,
  kMoeInitRouting = 502,
  kGroupedMatmulV4 = 503,
  kMatmulAllReduceAddRmsNorm = 504,
  kKVCacheScatterUpdate = 505,
  kMoeInitRoutingV2 = 506,
  kMoeComputeExpertTokens = 507,
  kQuantMatmul = 508,
  kMoeInitRoutingQuantV2 = 509,
  kAddRmsNormQuantV2 = 510,
  kQuantBatchMatmul = 511,
  kMoeFinalizeRouting = 512,
  kFusedInferAttentionScore = 513,
  kMoeGatingTopKSoftmax = 514,
  kGroupedMatmul = 515,
  kWeightQuantBatchMatmul = 516,
  kGroupedMatmulV2 = 517,
  kDynamicQuantExt = 518,
  kDistCommScatterTensor = 519,
  kDistCommAllToAllVC = 520,
  kDistCommAllGatherIntoTensorUneven = 521,
  kDistCommBarrier = 522,
  kInnerCommAllToAllV = 523,
  kDistCommGather = 524,
  kDistCommBroadcast = 525,
  kDistCommAllToAllV = 526,
  kDistCommReduceScatterTensorUneven = 527,
  kDistCommGatherIntoTensor = 528,
  kDistCommIrecv = 529,
  kDistCommAllReduce = 530,
  kInnerCommReduceScatter = 531,
  kDistCommReduce = 532,
  kInnerCommIsend = 533,
  kDistCommIsend = 534,
  kDistCommScatter = 535,
  kDistCommReduceScatter = 536,
  kDistCommBatchIsendIrecv = 537,
  kInnerCommAllGather = 538,
  kInnerCommAllReduce = 539,
  kDistCommReduceScatterTensor = 540,
  kDistCommAllToAllVSingle = 541,
  kDistCommAllGatherIntoTensor = 542,
  kDistCommAllGather = 543,
  kInnerCommIrecv = 544,
  kAnyExt = 545,
  kGmmV2 = 546,
  kEinsumExt = 547,
  kPixelShuffle = 548,
  kGmmBackward = 549,
  kGmmV2Backward = 550,
  kGmm = 551,
  kDropout2dExt = 552,
  kAny = 553,
  kFuncMaxPool2D = 554,
  kGmmBackwardFusion = 555,
  kGmmV2BackwardFusion = 556,
  kMoeTokenUnpermute = 557,
  kInplaceExponential = 558,
  kFuncDropoutExt = 559,
};

using CoshGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RandLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using MSELossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GeLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MedianExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ProdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ToOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using EqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FracGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using BatchNormReduceGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using RepeatInterleaveIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UpsampleBicubic2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using InplaceAddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceSubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceLogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InnerIndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using KLDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using RsqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LessGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using SinhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LogAddExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AsinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AsinhExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceRandomGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GreaterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Log2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TransposeExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using VarMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using LayerNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using BitwiseNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using AddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using Atan2ExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LerpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FlashAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using BitwiseXorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using IsInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaxPoolWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using CustomExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using EyeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using TrilExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SeluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using UpsampleNearest3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using PolarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ArgMinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using NeScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using TypeAsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LogicalNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using IsFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MatrixInverseExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitWithSizeViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using InplaceDivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using ConvolutionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using SplitWithSizeGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using PagedAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using StdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using RemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BitwiseAndScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MultinomialExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SoftMarginLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using LogAddExp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CrossEntropyLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using ReshapeAndCacheGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using InplaceDivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using TruncGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ChunkViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using RingAttentionUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using SelectV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UniqueConsecutiveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReduceMaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using RoundGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MaskedSelectGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdamWGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using UpsampleBilinear2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using GLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using DiagonalViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using ScatterAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MedianDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceSignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using NLLLoss2dGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using NormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NewZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NarrowGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using BatchMatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using AvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ExpandDimsGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using RotaryPositionEmbeddingGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using CrossEntropyLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchNormElemtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using GroupNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using SliceGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &)>;
using FloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceEluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using InplaceMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SpeedFusionAttentionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using NonZeroExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using PReLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedFillGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SearchSortedGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaximumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReduceAnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using ArangeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using OnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using HSwishGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using CloneGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReciprocalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SelectExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using Log10GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using TransposeViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using GridSampler2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using StdMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchMatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeTokenPermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchNormGatherStatsWithCountsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using L1LossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using AsStridedGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &, const int64_t &)>;
using TanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GeneratorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using LogSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using HardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using LayerNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using BitwiseOrScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using LogSoftmaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using RepeatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MultiScaleDeformableAttnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using EmbeddingDenseBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using InplaceFloorDividesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using CummaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InnerMoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using RotaryPositionEmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceSubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using GridSampler2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using LogSumExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using FillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceUniformGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitTensorViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using RandnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using IndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveAvgPool2DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceHardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MaxPoolGradWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using ExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveAvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Conv1DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using InplaceDivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using DequantSwigluQuantGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using RandExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LogSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ThresholdGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SincGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GeluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SqueezeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using InnerNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using EmptyLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using PowGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Unique2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using BitwiseOrTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using UniformExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReflectionPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using HSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ToDeviceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using AtanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using HistcExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using SilentCheckV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using RemainderScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using SwigluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ExpandDimsViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using IdentityGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using HShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using RmsNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using OnesLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ConstantPadNDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &)>;
using ArgMaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using InplaceDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RollGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using Expm1GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalFloatTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using PowTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FmodTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CumminExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using CountNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using SinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Col2ImExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using GridSampler3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SoftMarginLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using Conv2DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using SliceExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using KthvalueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceFloorDivideGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MishGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GroupNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ArgSortGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InplacePutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using NewEmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using FmodScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using DropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using PReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ZerosLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using CopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TransposeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using Conv2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using InplaceIndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using KLDivGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SeLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using XLogYScalarSelfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using SiLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GridSampler3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using ErfcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using PowScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleLinear1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using LogicalAndGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CeilGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SliceExtGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using ReflectionPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using GeLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ApplyRotaryPosEmbGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UpsampleTrilinear3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using UpsampleNearest2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InnerInplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using InplaceScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveAvgPool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using NewFullGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RealViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using InplaceScatterSrcReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ConcatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using SoftplusGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MatmulReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using DivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using Conv1DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using SoftShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GeluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using NLLLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using EluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using AvgPool2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using DivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LinalgVectorNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using BincountExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using ChunkGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using BatchNormStatsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using NegGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterSrcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NotEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LinSpaceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LeakyReLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using ClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using SmoothL1LossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReduceMinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using AddmvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using SubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceBernoulliScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using VarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using InnerUniqueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using TanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AddcdivExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AddcmulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GreaterEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using EmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using ReplicationPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using RmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GatherNdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Im2ColExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using MinDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using GatherDGradV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMaskedFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TensorScatterElementsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using Log1pGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalTensorFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AllFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using SilentCheckV3GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using EqualExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using DivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AdaptiveMaxPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SwigluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using NanToNumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &)>;
using AllGatherMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using NLLLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ToDtypeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using LinalgQrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MoeTokenPermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using DivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RandnLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReshapeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using IndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FullLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using MlaGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceTanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RandIntLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceRemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FloorDivScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MaskedSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SpeedFusionAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceMulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ConvolutionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using ImagViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using DropoutGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using HSwishGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using L1LossBackwardExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using BroadcastToViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using OuterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CumsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using NormalFloatFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using TopkExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ArgMinWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using XlogyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SquareGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyWithLogitsBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using XLogYScalarOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BroadcastToGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using DropoutDoMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using HardtanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using BernoulliExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormElemtGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MaxPoolWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using LessEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceRemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReplicationPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SoftplusExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using AddLayerNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using NewOnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LeakyReLUGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using ScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using SortExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using AdaptiveAvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using Conv3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using IncreFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MaxUnpool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using HSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FlashAttentionScoreGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using AcoshExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MoeDistributeCombineGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MeanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceAddsExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using ConvolutionStrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using AcosExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using HShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using MinimumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RandIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceBernoulliTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseAndTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NLLLoss2dGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceScatterValueReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using LogicalOrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using TakeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SubGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using DenseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using TraceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using PromptFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using CrossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UnstackExtViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using InplaceNormalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IndexSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using TriangularSolveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using IsNegInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Col2ImGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using ConvolutionStrGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using FFNExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using AdaptiveAvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using CastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MishExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using DiagExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LerpScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using CellBackwardHookGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using LogicalXorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ConvTranspose2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using UniqueDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceStopGradientGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReverseV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ReduceAllGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using DropoutGenMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using CosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MoeDistributeDispatchGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReplicationPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using BaddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MSELossGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UpsampleNearest1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using UpsampleLinear1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using LogSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UpsampleBilinear2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using SoftmaxBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceFillDiagonalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using StackExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using TensorScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using UpsampleNearest3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using TileGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using AdaptiveMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using UpsampleBicubic2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using BitwiseXorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NarrowViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using MaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using IndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BCEWithLogitsLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using Conv3DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using MultiScaleDeformableAttnGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GatherDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using NansumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using GreaterEqualScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using IsCloseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceMaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BatchNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Exp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceGroupedMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleTrilinear3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using OneHotExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MaxDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SmoothL1LossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MaxPoolGradWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using GcdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using SoftShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using SplitTensorGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using AbsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using FloorDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogSoftmaxGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ArgMaxWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using AvgPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ContiguousGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using TriuGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using RandpermExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MoeTokenUnpermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using AddLayerNormV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using QuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GroupedMatmulV4GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using MatmulAllReduceAddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using KVCacheScatterUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeComputeExpertTokensGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using QuantMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using MoeInitRoutingQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using AddRmsNormQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using QuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeFinalizeRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using FusedInferAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeGatingTopKSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using GroupedMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using WeightQuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using GroupedMatmulV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DynamicQuantExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using DistCommScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVCGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommAllGatherIntoTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBarrierGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBroadcastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using DistCommReduceScatterTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBatchIsendIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using InnerCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVSingleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommAllGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using AnyExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using GmmV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using EinsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &)>;
using PixelShuffleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GmmBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using GmmV2BackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using GmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using Dropout2dExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FuncMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using GmmBackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using GmmV2BackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using MoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceExponentialGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FuncDropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;

struct OpsAutoGradRegisters {
  CoshGradFunc CoshGradFuncObj;
  RandLikeExtGradFunc RandLikeExtGradFuncObj;
  MSELossExtGradFunc MSELossExtGradFuncObj;
  GeLUGradFunc GeLUGradFuncObj;
  MedianExtGradFunc MedianExtGradFuncObj;
  ProdExtGradFunc ProdExtGradFuncObj;
  ToOtherGradFunc ToOtherGradFuncObj;
  EqualGradFunc EqualGradFuncObj;
  FracGradFunc FracGradFuncObj;
  InplaceExpGradFunc InplaceExpGradFuncObj;
  InplaceClampTensorGradFunc InplaceClampTensorGradFuncObj;
  BatchNormReduceGradGradFunc BatchNormReduceGradGradFuncObj;
  RepeatInterleaveIntGradFunc RepeatInterleaveIntGradFuncObj;
  UpsampleBicubic2DGradGradFunc UpsampleBicubic2DGradGradFuncObj;
  InplaceAddmmGradFunc InplaceAddmmGradFuncObj;
  InplaceSubScalarGradFunc InplaceSubScalarGradFuncObj;
  InplaceLogGradFunc InplaceLogGradFuncObj;
  InnerIndexGradFunc InnerIndexGradFuncObj;
  KLDivGradFunc KLDivGradFuncObj;
  RsqrtGradFunc RsqrtGradFuncObj;
  LessGradFunc LessGradFuncObj;
  EluExtGradFunc EluExtGradFuncObj;
  SinhGradFunc SinhGradFuncObj;
  LogAddExpGradFunc LogAddExpGradFuncObj;
  AsinExtGradFunc AsinExtGradFuncObj;
  ErfGradFunc ErfGradFuncObj;
  AsinhExtGradFunc AsinhExtGradFuncObj;
  InplaceRandomGradFunc InplaceRandomGradFuncObj;
  GreaterGradFunc GreaterGradFuncObj;
  Log2GradFunc Log2GradFuncObj;
  ErfinvGradFunc ErfinvGradFuncObj;
  TransposeExtViewGradFunc TransposeExtViewGradFuncObj;
  VarMeanGradFunc VarMeanGradFuncObj;
  LayerNormExtGradFunc LayerNormExtGradFuncObj;
  BitwiseNotGradFunc BitwiseNotGradFuncObj;
  AvgPool1DGradFunc AvgPool1DGradFuncObj;
  AddbmmGradFunc AddbmmGradFuncObj;
  Atan2ExtGradFunc Atan2ExtGradFuncObj;
  LerpGradFunc LerpGradFuncObj;
  FlashAttentionScoreGradFunc FlashAttentionScoreGradFuncObj;
  BitwiseXorScalarGradFunc BitwiseXorScalarGradFuncObj;
  IsInfGradFunc IsInfGradFuncObj;
  MaxPoolWithMaskGradFunc MaxPoolWithMaskGradFuncObj;
  CustomExtGradFunc CustomExtGradFuncObj;
  EyeGradFunc EyeGradFuncObj;
  TrilExtGradFunc TrilExtGradFuncObj;
  SeluGradGradFunc SeluGradGradFuncObj;
  BatchNormExtGradFunc BatchNormExtGradFuncObj;
  UpsampleNearest3DGradGradFunc UpsampleNearest3DGradGradFuncObj;
  PolarGradFunc PolarGradFuncObj;
  ArgMinExtGradFunc ArgMinExtGradFuncObj;
  NeScalarGradFunc NeScalarGradFuncObj;
  TypeAsGradFunc TypeAsGradFuncObj;
  SqrtGradFunc SqrtGradFuncObj;
  LogicalNotGradFunc LogicalNotGradFuncObj;
  IsFiniteGradFunc IsFiniteGradFuncObj;
  BinaryCrossEntropyGradGradFunc BinaryCrossEntropyGradGradFuncObj;
  ReflectionPad1DGradFunc ReflectionPad1DGradFuncObj;
  MatrixInverseExtGradFunc MatrixInverseExtGradFuncObj;
  NormalTensorTensorGradFunc NormalTensorTensorGradFuncObj;
  SplitWithSizeViewGradFunc SplitWithSizeViewGradFuncObj;
  InplaceDivsGradFunc InplaceDivsGradFuncObj;
  SoftmaxGradFunc SoftmaxGradFuncObj;
  MaskedFillScalarGradFunc MaskedFillScalarGradFuncObj;
  ConvolutionGradFunc ConvolutionGradFuncObj;
  SplitWithSizeGradFunc SplitWithSizeGradFuncObj;
  PagedAttentionGradFunc PagedAttentionGradFuncObj;
  StdGradFunc StdGradFuncObj;
  RemainderTensorScalarGradFunc RemainderTensorScalarGradFuncObj;
  BitwiseAndScalarGradFunc BitwiseAndScalarGradFuncObj;
  MultinomialExtGradFunc MultinomialExtGradFuncObj;
  SoftMarginLossGradGradFunc SoftMarginLossGradGradFuncObj;
  LogAddExp2GradFunc LogAddExp2GradFuncObj;
  CrossEntropyLossGradGradFunc CrossEntropyLossGradGradFuncObj;
  ReshapeAndCacheGradFunc ReshapeAndCacheGradFuncObj;
  InplaceDivModsGradFunc InplaceDivModsGradFuncObj;
  TruncGradFunc TruncGradFuncObj;
  ChunkViewGradFunc ChunkViewGradFuncObj;
  RingAttentionUpdateGradFunc RingAttentionUpdateGradFuncObj;
  SelectV2GradFunc SelectV2GradFuncObj;
  MaskedScatterGradFunc MaskedScatterGradFuncObj;
  UniqueConsecutiveGradFunc UniqueConsecutiveGradFuncObj;
  ReduceMaxGradFunc ReduceMaxGradFuncObj;
  RoundGradFunc RoundGradFuncObj;
  MaskedSelectGradGradFunc MaskedSelectGradGradFuncObj;
  AdamWGradFunc AdamWGradFuncObj;
  UpsampleBilinear2DGradFunc UpsampleBilinear2DGradFuncObj;
  GLUGradFunc GLUGradFuncObj;
  DiagonalViewGradFunc DiagonalViewGradFuncObj;
  ScatterAddExtGradFunc ScatterAddExtGradFuncObj;
  NonZeroGradFunc NonZeroGradFuncObj;
  AddScalarGradFunc AddScalarGradFuncObj;
  MedianDimGradFunc MedianDimGradFuncObj;
  InplaceSignGradFunc InplaceSignGradFuncObj;
  ThresholdGradFunc ThresholdGradFuncObj;
  NLLLoss2dGradGradFunc NLLLoss2dGradGradFuncObj;
  NormGradFunc NormGradFuncObj;
  NewZerosGradFunc NewZerosGradFuncObj;
  NarrowGradFunc NarrowGradFuncObj;
  BatchMatMulExtGradFunc BatchMatMulExtGradFuncObj;
  AvgPool3DExtGradFunc AvgPool3DExtGradFuncObj;
  AvgPool3DGradExtGradFunc AvgPool3DGradExtGradFuncObj;
  ExpandDimsGradFunc ExpandDimsGradFuncObj;
  RotaryPositionEmbeddingGradGradFunc RotaryPositionEmbeddingGradGradFuncObj;
  CrossEntropyLossGradFunc CrossEntropyLossGradFuncObj;
  BatchNormElemtGradFunc BatchNormElemtGradFuncObj;
  GroupNormGradFunc GroupNormGradFuncObj;
  SliceGradFunc SliceGradFuncObj;
  FloorGradFunc FloorGradFuncObj;
  MatMulGradFunc MatMulGradFuncObj;
  InplaceEluGradFunc InplaceEluGradFuncObj;
  InplaceMatmulAddGradFunc InplaceMatmulAddGradFuncObj;
  MatMulExtGradFunc MatMulExtGradFuncObj;
  SpeedFusionAttentionGradGradFunc SpeedFusionAttentionGradGradFuncObj;
  NonZeroExtGradFunc NonZeroExtGradFuncObj;
  PReLUGradGradFunc PReLUGradGradFuncObj;
  MaskedFillGradFunc MaskedFillGradFuncObj;
  SearchSortedGradFunc SearchSortedGradFuncObj;
  InplaceSigmoidGradFunc InplaceSigmoidGradFuncObj;
  MaximumGradFunc MaximumGradFuncObj;
  ReduceAnyGradFunc ReduceAnyGradFuncObj;
  ArangeGradFunc ArangeGradFuncObj;
  OnesGradFunc OnesGradFuncObj;
  HSwishGradFunc HSwishGradFuncObj;
  CloneGradFunc CloneGradFuncObj;
  ReciprocalGradFunc ReciprocalGradFuncObj;
  AddExtGradFunc AddExtGradFuncObj;
  SigmoidGradFunc SigmoidGradFuncObj;
  InplaceMaskedScatterGradFunc InplaceMaskedScatterGradFuncObj;
  SelectExtViewGradFunc SelectExtViewGradFuncObj;
  Log10GradFunc Log10GradFuncObj;
  InplaceThresholdGradFunc InplaceThresholdGradFuncObj;
  TransposeViewGradFunc TransposeViewGradFuncObj;
  GridSampler2DGradGradFunc GridSampler2DGradGradFuncObj;
  StdMeanGradFunc StdMeanGradFuncObj;
  BatchMatMulGradFunc BatchMatMulGradFuncObj;
  MoeTokenPermuteGradGradFunc MoeTokenPermuteGradGradFuncObj;
  BatchNormGatherStatsWithCountsGradFunc BatchNormGatherStatsWithCountsGradFuncObj;
  L1LossExtGradFunc L1LossExtGradFuncObj;
  AsStridedGradFunc AsStridedGradFuncObj;
  TanhGradFunc TanhGradFuncObj;
  GeneratorGradFunc GeneratorGradFuncObj;
  LogSigmoidGradFunc LogSigmoidGradFuncObj;
  AddmmGradFunc AddmmGradFuncObj;
  HardtanhGradFunc HardtanhGradFuncObj;
  LayerNormGradExtGradFunc LayerNormGradExtGradFuncObj;
  BitwiseOrScalarGradFunc BitwiseOrScalarGradFuncObj;
  LogSoftmaxExtGradFunc LogSoftmaxExtGradFuncObj;
  InplaceCopyGradFunc InplaceCopyGradFuncObj;
  ReplicationPad2DGradGradFunc ReplicationPad2DGradGradFuncObj;
  RepeatGradFunc RepeatGradFuncObj;
  MultiScaleDeformableAttnGradFunc MultiScaleDeformableAttnGradFuncObj;
  GluGradGradFunc GluGradGradFuncObj;
  EmbeddingDenseBackwardGradFunc EmbeddingDenseBackwardGradFuncObj;
  InplaceFloorDividesGradFunc InplaceFloorDividesGradFuncObj;
  CummaxGradFunc CummaxGradFuncObj;
  MvGradFunc MvGradFuncObj;
  InnerMoeTokenUnpermuteGradFunc InnerMoeTokenUnpermuteGradFuncObj;
  RotaryPositionEmbeddingGradFunc RotaryPositionEmbeddingGradFuncObj;
  ReflectionPad3DGradGradFunc ReflectionPad3DGradGradFuncObj;
  InplaceSubExtGradFunc InplaceSubExtGradFuncObj;
  GridSampler2DGradFunc GridSampler2DGradFuncObj;
  ReplicationPad1DGradFunc ReplicationPad1DGradFuncObj;
  LogSumExpGradFunc LogSumExpGradFuncObj;
  FillScalarGradFunc FillScalarGradFuncObj;
  InplaceZeroGradFunc InplaceZeroGradFuncObj;
  LogGradFunc LogGradFuncObj;
  InplaceUniformGradFunc InplaceUniformGradFuncObj;
  SplitTensorViewGradFunc SplitTensorViewGradFuncObj;
  RandnGradFunc RandnGradFuncObj;
  IndexFillTensorGradFunc IndexFillTensorGradFuncObj;
  AdaptiveAvgPool2DGradExtGradFunc AdaptiveAvgPool2DGradExtGradFuncObj;
  InplaceHardtanhGradFunc InplaceHardtanhGradFuncObj;
  MaxPoolGradWithIndicesGradFunc MaxPoolGradWithIndicesGradFuncObj;
  ExpGradFunc ExpGradFuncObj;
  InplaceIndexCopyGradFunc InplaceIndexCopyGradFuncObj;
  AdaptiveAvgPool3DGradExtGradFunc AdaptiveAvgPool3DGradExtGradFuncObj;
  Conv1DPaddingGradFunc Conv1DPaddingGradFuncObj;
  InplaceDivModGradFunc InplaceDivModGradFuncObj;
  DequantSwigluQuantGradFunc DequantSwigluQuantGradFuncObj;
  RandExtGradFunc RandExtGradFuncObj;
  LogSigmoidGradGradFunc LogSigmoidGradGradFuncObj;
  ThresholdGradGradFunc ThresholdGradGradFuncObj;
  SincGradFunc SincGradFuncObj;
  GeluGradExtGradFunc GeluGradExtGradFuncObj;
  SqueezeGradFunc SqueezeGradFuncObj;
  InnerNonZeroGradFunc InnerNonZeroGradFuncObj;
  EmptyLikeGradFunc EmptyLikeGradFuncObj;
  PowGradFunc PowGradFuncObj;
  SigmoidGradGradFunc SigmoidGradGradFuncObj;
  Unique2GradFunc Unique2GradFuncObj;
  BitwiseOrTensorGradFunc BitwiseOrTensorGradFuncObj;
  EluGradExtGradFunc EluGradExtGradFuncObj;
  UniformExtGradFunc UniformExtGradFuncObj;
  ReflectionPad1DGradGradFunc ReflectionPad1DGradGradFuncObj;
  HSigmoidGradFunc HSigmoidGradFuncObj;
  InplaceMulGradFunc InplaceMulGradFuncObj;
  ToDeviceGradFunc ToDeviceGradFuncObj;
  AtanExtGradFunc AtanExtGradFuncObj;
  HistcExtGradFunc HistcExtGradFuncObj;
  SilentCheckV2GradFunc SilentCheckV2GradFuncObj;
  RemainderScalarTensorGradFunc RemainderScalarTensorGradFuncObj;
  SwigluGradGradFunc SwigluGradGradFuncObj;
  ExpandDimsViewGradFunc ExpandDimsViewGradFuncObj;
  IdentityGradFunc IdentityGradFuncObj;
  HShrinkGradGradFunc HShrinkGradGradFuncObj;
  RmsNormGradGradFunc RmsNormGradGradFuncObj;
  OnesLikeExtGradFunc OnesLikeExtGradFuncObj;
  ConstantPadNDGradFunc ConstantPadNDGradFuncObj;
  ArgMaxExtGradFunc ArgMaxExtGradFuncObj;
  InplaceDivGradFunc InplaceDivGradFuncObj;
  RollGradFunc RollGradFuncObj;
  Expm1GradFunc Expm1GradFuncObj;
  NormalFloatTensorGradFunc NormalFloatTensorGradFuncObj;
  PowTensorScalarGradFunc PowTensorScalarGradFuncObj;
  FmodTensorGradFunc FmodTensorGradFuncObj;
  CumminExtGradFunc CumminExtGradFuncObj;
  CountNonZeroGradFunc CountNonZeroGradFuncObj;
  SinGradFunc SinGradFuncObj;
  Col2ImExtGradFunc Col2ImExtGradFuncObj;
  GridSampler3DGradFunc GridSampler3DGradFuncObj;
  SoftMarginLossGradFunc SoftMarginLossGradFuncObj;
  Conv2DPaddingGradFunc Conv2DPaddingGradFuncObj;
  SliceExtViewGradFunc SliceExtViewGradFuncObj;
  KthvalueGradFunc KthvalueGradFuncObj;
  InplaceFloorDivideGradFunc InplaceFloorDivideGradFuncObj;
  MishGradExtGradFunc MishGradExtGradFuncObj;
  GroupNormGradGradFunc GroupNormGradGradFuncObj;
  ReplicationPad3DGradGradFunc ReplicationPad3DGradGradFuncObj;
  ArgSortGradFunc ArgSortGradFuncObj;
  InplacePutGradFunc InplacePutGradFuncObj;
  NewEmptyGradFunc NewEmptyGradFuncObj;
  FmodScalarGradFunc FmodScalarGradFuncObj;
  DropoutExtGradFunc DropoutExtGradFuncObj;
  PReLUGradFunc PReLUGradFuncObj;
  ZerosLikeExtGradFunc ZerosLikeExtGradFuncObj;
  CopyGradFunc CopyGradFuncObj;
  TransposeGradFunc TransposeGradFuncObj;
  Conv2DExtGradFunc Conv2DExtGradFuncObj;
  InplaceIndexFillScalarGradFunc InplaceIndexFillScalarGradFuncObj;
  KLDivGradGradFunc KLDivGradGradFuncObj;
  SeLUExtGradFunc SeLUExtGradFuncObj;
  XLogYScalarSelfGradFunc XLogYScalarSelfGradFuncObj;
  SiLUGradGradFunc SiLUGradGradFuncObj;
  GridSampler3DGradGradFunc GridSampler3DGradGradFuncObj;
  ErfcGradFunc ErfcGradFuncObj;
  PowScalarTensorGradFunc PowScalarTensorGradFuncObj;
  UpsampleLinear1DGradGradFunc UpsampleLinear1DGradGradFuncObj;
  LogicalAndGradFunc LogicalAndGradFuncObj;
  CeilGradFunc CeilGradFuncObj;
  SliceExtGradFunc SliceExtGradFuncObj;
  ReflectionPad3DGradFunc ReflectionPad3DGradFuncObj;
  SignGradFunc SignGradFuncObj;
  RepeatInterleaveTensorGradFunc RepeatInterleaveTensorGradFuncObj;
  GeLUGradGradFunc GeLUGradGradFuncObj;
  ApplyRotaryPosEmbGradFunc ApplyRotaryPosEmbGradFuncObj;
  UpsampleTrilinear3DGradGradFunc UpsampleTrilinear3DGradGradFuncObj;
  UpsampleNearest2DGradGradFunc UpsampleNearest2DGradGradFuncObj;
  InnerInplaceIndexPutGradFunc InnerInplaceIndexPutGradFuncObj;
  InplaceScatterAddGradFunc InplaceScatterAddGradFuncObj;
  AdaptiveAvgPool2DExtGradFunc AdaptiveAvgPool2DExtGradFuncObj;
  NewFullGradFunc NewFullGradFuncObj;
  RealViewGradFunc RealViewGradFuncObj;
  BinaryCrossEntropyGradFunc BinaryCrossEntropyGradFuncObj;
  InplaceScatterSrcReduceGradFunc InplaceScatterSrcReduceGradFuncObj;
  ConcatGradFunc ConcatGradFuncObj;
  SoftplusGradExtGradFunc SoftplusGradExtGradFuncObj;
  MatmulReduceScatterGradFunc MatmulReduceScatterGradFuncObj;
  DivModGradFunc DivModGradFuncObj;
  InplaceAddExtGradFunc InplaceAddExtGradFuncObj;
  Conv1DExtGradFunc Conv1DExtGradFuncObj;
  SoftShrinkGradGradFunc SoftShrinkGradGradFuncObj;
  GeluExtGradFunc GeluExtGradFuncObj;
  NLLLossGradGradFunc NLLLossGradGradFuncObj;
  EluGradFunc EluGradFuncObj;
  AvgPool2DGradGradFunc AvgPool2DGradGradFuncObj;
  DivGradFunc DivGradFuncObj;
  LinalgVectorNormGradFunc LinalgVectorNormGradFuncObj;
  BincountExtGradFunc BincountExtGradFuncObj;
  ChunkGradFunc ChunkGradFuncObj;
  BatchNormStatsGradFunc BatchNormStatsGradFuncObj;
  NegGradFunc NegGradFuncObj;
  InplaceFloorGradFunc InplaceFloorGradFuncObj;
  InplaceScatterSrcGradFunc InplaceScatterSrcGradFuncObj;
  NotEqualGradFunc NotEqualGradFuncObj;
  LinSpaceExtGradFunc LinSpaceExtGradFuncObj;
  LeakyReLUExtGradFunc LeakyReLUExtGradFuncObj;
  InplaceClampScalarGradFunc InplaceClampScalarGradFuncObj;
  ClampTensorGradFunc ClampTensorGradFuncObj;
  SmoothL1LossGradFunc SmoothL1LossGradFuncObj;
  ReduceMinGradFunc ReduceMinGradFuncObj;
  AddmvGradFunc AddmvGradFuncObj;
  SubScalarGradFunc SubScalarGradFuncObj;
  InplaceBernoulliScalarGradFunc InplaceBernoulliScalarGradFuncObj;
  VarGradFunc VarGradFuncObj;
  InnerUniqueGradFunc InnerUniqueGradFuncObj;
  TanhGradGradFunc TanhGradGradFuncObj;
  AddcdivExtGradFunc AddcdivExtGradFuncObj;
  AddcmulExtGradFunc AddcmulExtGradFuncObj;
  AddRmsNormGradFunc AddRmsNormGradFuncObj;
  GreaterEqualGradFunc GreaterEqualGradFuncObj;
  SiLUGradFunc SiLUGradFuncObj;
  FillTensorGradFunc FillTensorGradFuncObj;
  EmptyGradFunc EmptyGradFuncObj;
  ReplicationPad1DGradGradFunc ReplicationPad1DGradGradFuncObj;
  RmsNormGradFunc RmsNormGradFuncObj;
  GatherNdExtGradFunc GatherNdExtGradFuncObj;
  Im2ColExtGradFunc Im2ColExtGradFuncObj;
  MinDimGradFunc MinDimGradFuncObj;
  GatherDGradV2GradFunc GatherDGradV2GradFuncObj;
  InplaceMaskedFillTensorGradFunc InplaceMaskedFillTensorGradFuncObj;
  ReLUGradFunc ReLUGradFuncObj;
  TensorScatterElementsGradFunc TensorScatterElementsGradFuncObj;
  Log1pGradFunc Log1pGradFuncObj;
  NormalTensorFloatGradFunc NormalTensorFloatGradFuncObj;
  AllFiniteGradFunc AllFiniteGradFuncObj;
  SilentCheckV3GradFunc SilentCheckV3GradFuncObj;
  EqualExtGradFunc EqualExtGradFuncObj;
  ReluGradGradFunc ReluGradGradFuncObj;
  DivsGradFunc DivsGradFuncObj;
  AdaptiveMaxPool1DGradFunc AdaptiveMaxPool1DGradFuncObj;
  SwigluGradFunc SwigluGradFuncObj;
  NanToNumGradFunc NanToNumGradFuncObj;
  AllGatherMatmulGradFunc AllGatherMatmulGradFuncObj;
  NLLLossGradFunc NLLLossGradFuncObj;
  ReflectionPad2DGradFunc ReflectionPad2DGradFuncObj;
  InplaceErfinvGradFunc InplaceErfinvGradFuncObj;
  ToDtypeGradFunc ToDtypeGradFuncObj;
  LinalgQrGradFunc LinalgQrGradFuncObj;
  MoeTokenPermuteGradFunc MoeTokenPermuteGradFuncObj;
  DivModsGradFunc DivModsGradFuncObj;
  RandnLikeGradFunc RandnLikeGradFuncObj;
  ReshapeGradFunc ReshapeGradFuncObj;
  IndexFillScalarGradFunc IndexFillScalarGradFuncObj;
  FullLikeGradFunc FullLikeGradFuncObj;
  MlaGradFunc MlaGradFuncObj;
  InplaceTanhGradFunc InplaceTanhGradFuncObj;
  RandIntLikeGradFunc RandIntLikeGradFuncObj;
  InplaceRemainderTensorScalarGradFunc InplaceRemainderTensorScalarGradFuncObj;
  FloorDivScalarGradFunc FloorDivScalarGradFuncObj;
  MaskedSelectGradFunc MaskedSelectGradFuncObj;
  SpeedFusionAttentionGradFunc SpeedFusionAttentionGradFuncObj;
  InplaceMulsGradFunc InplaceMulsGradFuncObj;
  InplaceReLUGradFunc InplaceReLUGradFuncObj;
  ConvolutionGradGradFunc ConvolutionGradGradFuncObj;
  ImagViewGradFunc ImagViewGradFuncObj;
  DropoutGradExtGradFunc DropoutGradExtGradFuncObj;
  HSwishGradGradFunc HSwishGradGradFuncObj;
  L1LossBackwardExtGradFunc L1LossBackwardExtGradFuncObj;
  BroadcastToViewGradFunc BroadcastToViewGradFuncObj;
  OuterGradFunc OuterGradFuncObj;
  CumsumExtGradFunc CumsumExtGradFuncObj;
  ClampScalarGradFunc ClampScalarGradFuncObj;
  NormalFloatFloatGradFunc NormalFloatFloatGradFuncObj;
  IndexGradFunc IndexGradFuncObj;
  TopkExtGradFunc TopkExtGradFuncObj;
  ArgMinWithValueGradFunc ArgMinWithValueGradFuncObj;
  XlogyGradFunc XlogyGradFuncObj;
  SquareGradFunc SquareGradFuncObj;
  BinaryCrossEntropyWithLogitsBackwardGradFunc BinaryCrossEntropyWithLogitsBackwardGradFuncObj;
  XLogYScalarOtherGradFunc XLogYScalarOtherGradFuncObj;
  BroadcastToGradFunc BroadcastToGradFuncObj;
  DropoutDoMaskExtGradFunc DropoutDoMaskExtGradFuncObj;
  HardtanhGradGradFunc HardtanhGradGradFuncObj;
  BernoulliExtGradFunc BernoulliExtGradFuncObj;
  BatchNormElemtGradGradFunc BatchNormElemtGradGradFuncObj;
  MaxPoolWithIndicesGradFunc MaxPoolWithIndicesGradFuncObj;
  LessEqualGradFunc LessEqualGradFuncObj;
  InplaceRemainderTensorTensorGradFunc InplaceRemainderTensorTensorGradFuncObj;
  ReplicationPad3DGradFunc ReplicationPad3DGradFuncObj;
  InplaceFillScalarGradFunc InplaceFillScalarGradFuncObj;
  SoftplusExtGradFunc SoftplusExtGradFuncObj;
  AddLayerNormGradGradFunc AddLayerNormGradGradFuncObj;
  SplitGradFunc SplitGradFuncObj;
  NewOnesGradFunc NewOnesGradFuncObj;
  LeakyReLUGradExtGradFunc LeakyReLUGradExtGradFuncObj;
  ScatterValueGradFunc ScatterValueGradFuncObj;
  SortExtGradFunc SortExtGradFuncObj;
  AdaptiveAvgPool3DExtGradFunc AdaptiveAvgPool3DExtGradFuncObj;
  Conv3DExtGradFunc Conv3DExtGradFuncObj;
  IncreFlashAttentionGradFunc IncreFlashAttentionGradFuncObj;
  MaxUnpool2DExtGradFunc MaxUnpool2DExtGradFuncObj;
  InplaceIndexPutGradFunc InplaceIndexPutGradFuncObj;
  HSigmoidGradGradFunc HSigmoidGradGradFuncObj;
  FlashAttentionScoreGradGradFunc FlashAttentionScoreGradGradFuncObj;
  AcoshExtGradFunc AcoshExtGradFuncObj;
  MoeDistributeCombineGradFunc MoeDistributeCombineGradFuncObj;
  MeanExtGradFunc MeanExtGradFuncObj;
  ZerosGradFunc ZerosGradFuncObj;
  InplaceAddsExtGradFunc InplaceAddsExtGradFuncObj;
  ConvolutionStrGradFunc ConvolutionStrGradFuncObj;
  AcosExtGradFunc AcosExtGradFuncObj;
  HShrinkGradFunc HShrinkGradFuncObj;
  MinimumGradFunc MinimumGradFuncObj;
  SubExtGradFunc SubExtGradFuncObj;
  RandIntGradFunc RandIntGradFuncObj;
  InplaceBernoulliTensorGradFunc InplaceBernoulliTensorGradFuncObj;
  BitwiseAndTensorGradFunc BitwiseAndTensorGradFuncObj;
  InplaceIndexAddExtGradFunc InplaceIndexAddExtGradFuncObj;
  AddGradFunc AddGradFuncObj;
  NLLLoss2dGradFunc NLLLoss2dGradFuncObj;
  InplaceScatterValueReduceGradFunc InplaceScatterValueReduceGradFuncObj;
  LogicalOrGradFunc LogicalOrGradFuncObj;
  TakeGradFunc TakeGradFuncObj;
  SubGradFunc SubGradFuncObj;
  AtanhGradFunc AtanhGradFuncObj;
  DenseGradFunc DenseGradFuncObj;
  TraceExtGradFunc TraceExtGradFuncObj;
  InplaceSiLUGradFunc InplaceSiLUGradFuncObj;
  PromptFlashAttentionGradFunc PromptFlashAttentionGradFuncObj;
  CrossGradFunc CrossGradFuncObj;
  UnstackExtViewGradFunc UnstackExtViewGradFuncObj;
  InplaceNormalGradFunc InplaceNormalGradFuncObj;
  MmGradFunc MmGradFuncObj;
  IndexSelectGradFunc IndexSelectGradFuncObj;
  TriangularSolveGradFunc TriangularSolveGradFuncObj;
  IsNegInfGradFunc IsNegInfGradFuncObj;
  Col2ImGradGradFunc Col2ImGradGradFuncObj;
  ConvolutionStrGradGradFunc ConvolutionStrGradGradFuncObj;
  FFNExtGradFunc FFNExtGradFuncObj;
  AdaptiveAvgPool1DGradFunc AdaptiveAvgPool1DGradFuncObj;
  CastGradFunc CastGradFuncObj;
  MishExtGradFunc MishExtGradFuncObj;
  DiagExtGradFunc DiagExtGradFuncObj;
  InplaceScatterValueGradFunc InplaceScatterValueGradFuncObj;
  RemainderTensorTensorGradFunc RemainderTensorTensorGradFuncObj;
  LerpScalarGradFunc LerpScalarGradFuncObj;
  CellBackwardHookGradFunc CellBackwardHookGradFuncObj;
  LogicalXorGradFunc LogicalXorGradFuncObj;
  UpsampleNearest2DGradFunc UpsampleNearest2DGradFuncObj;
  ConvTranspose2DGradFunc ConvTranspose2DGradFuncObj;
  UniqueDimGradFunc UniqueDimGradFuncObj;
  InplaceStopGradientGradFunc InplaceStopGradientGradFuncObj;
  ReverseV2GradFunc ReverseV2GradFuncObj;
  ReduceAllGradFunc ReduceAllGradFuncObj;
  DropoutGenMaskExtGradFunc DropoutGenMaskExtGradFuncObj;
  MinGradFunc MinGradFuncObj;
  CosGradFunc CosGradFuncObj;
  TanGradFunc TanGradFuncObj;
  MoeDistributeDispatchGradFunc MoeDistributeDispatchGradFuncObj;
  ReplicationPad2DGradFunc ReplicationPad2DGradFuncObj;
  BaddbmmGradFunc BaddbmmGradFuncObj;
  MSELossGradExtGradFunc MSELossGradExtGradFuncObj;
  UpsampleNearest1DGradFunc UpsampleNearest1DGradFuncObj;
  UpsampleLinear1DGradFunc UpsampleLinear1DGradFuncObj;
  LogSoftmaxGradFunc LogSoftmaxGradFuncObj;
  UpsampleBilinear2DGradGradFunc UpsampleBilinear2DGradGradFuncObj;
  SoftmaxBackwardGradFunc SoftmaxBackwardGradFuncObj;
  InplaceFillDiagonalGradFunc InplaceFillDiagonalGradFuncObj;
  StackExtGradFunc StackExtGradFuncObj;
  TensorScatterAddGradFunc TensorScatterAddGradFuncObj;
  MulsGradFunc MulsGradFuncObj;
  UpsampleNearest3DGradFunc UpsampleNearest3DGradFuncObj;
  TileGradFunc TileGradFuncObj;
  AdaptiveMaxPool2DGradFunc AdaptiveMaxPool2DGradFuncObj;
  UpsampleBicubic2DGradFunc UpsampleBicubic2DGradFuncObj;
  BitwiseXorTensorGradFunc BitwiseXorTensorGradFuncObj;
  NarrowViewGradFunc NarrowViewGradFuncObj;
  MaxGradFunc MaxGradFuncObj;
  InplaceIndexFillTensorGradFunc InplaceIndexFillTensorGradFuncObj;
  EmbeddingGradFunc EmbeddingGradFuncObj;
  IndexAddExtGradFunc IndexAddExtGradFuncObj;
  MulGradFunc MulGradFuncObj;
  SelectGradFunc SelectGradFuncObj;
  BCEWithLogitsLossGradFunc BCEWithLogitsLossGradFuncObj;
  Conv3DPaddingGradFunc Conv3DPaddingGradFuncObj;
  MultiScaleDeformableAttnGradGradFunc MultiScaleDeformableAttnGradGradFuncObj;
  GatherDGradFunc GatherDGradFuncObj;
  NansumGradFunc NansumGradFuncObj;
  GreaterEqualScalarGradFunc GreaterEqualScalarGradFuncObj;
  IsCloseGradFunc IsCloseGradFuncObj;
  InplaceMaskedFillScalarGradFunc InplaceMaskedFillScalarGradFuncObj;
  BatchNormGradExtGradFunc BatchNormGradExtGradFuncObj;
  InplaceFillTensorGradFunc InplaceFillTensorGradFuncObj;
  Exp2GradFunc Exp2GradFuncObj;
  InplaceGroupedMatmulAddGradFunc InplaceGroupedMatmulAddGradFuncObj;
  UpsampleTrilinear3DGradFunc UpsampleTrilinear3DGradFuncObj;
  OneHotExtGradFunc OneHotExtGradFuncObj;
  MaxDimGradFunc MaxDimGradFuncObj;
  DotGradFunc DotGradFuncObj;
  SmoothL1LossGradGradFunc SmoothL1LossGradGradFuncObj;
  ReflectionPad2DGradGradFunc ReflectionPad2DGradGradFuncObj;
  ScatterGradFunc ScatterGradFuncObj;
  MaxPoolGradWithMaskGradFunc MaxPoolGradWithMaskGradFuncObj;
  GcdGradFunc GcdGradFuncObj;
  ViewGradFunc ViewGradFuncObj;
  SoftShrinkGradFunc SoftShrinkGradFuncObj;
  SplitTensorGradFunc SplitTensorGradFuncObj;
  AbsGradFunc AbsGradFuncObj;
  UpsampleNearest1DGradGradFunc UpsampleNearest1DGradGradFuncObj;
  FloorDivGradFunc FloorDivGradFuncObj;
  LogSoftmaxGradGradFunc LogSoftmaxGradGradFuncObj;
  SumExtGradFunc SumExtGradFuncObj;
  ArgMaxWithValueGradFunc ArgMaxWithValueGradFuncObj;
  AvgPool2DGradFunc AvgPool2DGradFuncObj;
  ContiguousGradFunc ContiguousGradFuncObj;
  RepeatInterleaveGradGradFunc RepeatInterleaveGradGradFuncObj;
  TriuGradFunc TriuGradFuncObj;
  RandpermExtGradFunc RandpermExtGradFuncObj;
  MoeTokenUnpermuteGradGradFunc MoeTokenUnpermuteGradGradFuncObj;
  AddLayerNormV2GradFunc AddLayerNormV2GradFuncObj;
  QuantV2GradFunc QuantV2GradFuncObj;
  MoeInitRoutingGradFunc MoeInitRoutingGradFuncObj;
  GroupedMatmulV4GradFunc GroupedMatmulV4GradFuncObj;
  MatmulAllReduceAddRmsNormGradFunc MatmulAllReduceAddRmsNormGradFuncObj;
  KVCacheScatterUpdateGradFunc KVCacheScatterUpdateGradFuncObj;
  MoeInitRoutingV2GradFunc MoeInitRoutingV2GradFuncObj;
  MoeComputeExpertTokensGradFunc MoeComputeExpertTokensGradFuncObj;
  QuantMatmulGradFunc QuantMatmulGradFuncObj;
  MoeInitRoutingQuantV2GradFunc MoeInitRoutingQuantV2GradFuncObj;
  AddRmsNormQuantV2GradFunc AddRmsNormQuantV2GradFuncObj;
  QuantBatchMatmulGradFunc QuantBatchMatmulGradFuncObj;
  MoeFinalizeRoutingGradFunc MoeFinalizeRoutingGradFuncObj;
  FusedInferAttentionScoreGradFunc FusedInferAttentionScoreGradFuncObj;
  MoeGatingTopKSoftmaxGradFunc MoeGatingTopKSoftmaxGradFuncObj;
  GroupedMatmulGradFunc GroupedMatmulGradFuncObj;
  WeightQuantBatchMatmulGradFunc WeightQuantBatchMatmulGradFuncObj;
  GroupedMatmulV2GradFunc GroupedMatmulV2GradFuncObj;
  DynamicQuantExtGradFunc DynamicQuantExtGradFuncObj;
  DistCommScatterTensorGradFunc DistCommScatterTensorGradFuncObj;
  DistCommAllToAllVCGradFunc DistCommAllToAllVCGradFuncObj;
  DistCommAllGatherIntoTensorUnevenGradFunc DistCommAllGatherIntoTensorUnevenGradFuncObj;
  DistCommBarrierGradFunc DistCommBarrierGradFuncObj;
  InnerCommAllToAllVGradFunc InnerCommAllToAllVGradFuncObj;
  DistCommGatherGradFunc DistCommGatherGradFuncObj;
  DistCommBroadcastGradFunc DistCommBroadcastGradFuncObj;
  DistCommAllToAllVGradFunc DistCommAllToAllVGradFuncObj;
  DistCommReduceScatterTensorUnevenGradFunc DistCommReduceScatterTensorUnevenGradFuncObj;
  DistCommGatherIntoTensorGradFunc DistCommGatherIntoTensorGradFuncObj;
  DistCommIrecvGradFunc DistCommIrecvGradFuncObj;
  DistCommAllReduceGradFunc DistCommAllReduceGradFuncObj;
  InnerCommReduceScatterGradFunc InnerCommReduceScatterGradFuncObj;
  DistCommReduceGradFunc DistCommReduceGradFuncObj;
  InnerCommIsendGradFunc InnerCommIsendGradFuncObj;
  DistCommIsendGradFunc DistCommIsendGradFuncObj;
  DistCommScatterGradFunc DistCommScatterGradFuncObj;
  DistCommReduceScatterGradFunc DistCommReduceScatterGradFuncObj;
  DistCommBatchIsendIrecvGradFunc DistCommBatchIsendIrecvGradFuncObj;
  InnerCommAllGatherGradFunc InnerCommAllGatherGradFuncObj;
  InnerCommAllReduceGradFunc InnerCommAllReduceGradFuncObj;
  DistCommReduceScatterTensorGradFunc DistCommReduceScatterTensorGradFuncObj;
  DistCommAllToAllVSingleGradFunc DistCommAllToAllVSingleGradFuncObj;
  DistCommAllGatherIntoTensorGradFunc DistCommAllGatherIntoTensorGradFuncObj;
  DistCommAllGatherGradFunc DistCommAllGatherGradFuncObj;
  InnerCommIrecvGradFunc InnerCommIrecvGradFuncObj;
  AnyExtGradFunc AnyExtGradFuncObj;
  GmmV2GradFunc GmmV2GradFuncObj;
  EinsumExtGradFunc EinsumExtGradFuncObj;
  PixelShuffleGradFunc PixelShuffleGradFuncObj;
  GmmBackwardGradFunc GmmBackwardGradFuncObj;
  GmmV2BackwardGradFunc GmmV2BackwardGradFuncObj;
  GmmGradFunc GmmGradFuncObj;
  Dropout2dExtGradFunc Dropout2dExtGradFuncObj;
  AnyGradFunc AnyGradFuncObj;
  FuncMaxPool2DGradFunc FuncMaxPool2DGradFuncObj;
  GmmBackwardFusionGradFunc GmmBackwardFusionGradFuncObj;
  GmmV2BackwardFusionGradFunc GmmV2BackwardFusionGradFuncObj;
  MoeTokenUnpermuteGradFunc MoeTokenUnpermuteGradFuncObj;
  InplaceExponentialGradFunc InplaceExponentialGradFuncObj;
  FuncDropoutExtGradFunc FuncDropoutExtGradFuncObj;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_MINDSPORE_OPS_KERNEL_FUNCTIONS_AUTO_GENERATE_AUTO_GRAD_OP_REG_H_
