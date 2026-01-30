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
  kUpsampleBicubic2D = 0,
  kInplaceErfinv = 1,
  kLinalgQr = 2,
  kHShrinkGrad = 3,
  kInplaceExp = 4,
  kSmoothL1Loss = 5,
  kAvgPool3DGradExt = 6,
  kAdaptiveMaxPool2D = 7,
  kConvolutionStrGrad = 8,
  kExpm1 = 9,
  kMin = 10,
  kLog1p = 11,
  kLess = 12,
  kAtanExt = 13,
  kReplicationPad3D = 14,
  kBatchNormElemt = 15,
  kGluGrad = 16,
  kZeros = 17,
  kConv1DExt = 18,
  kLinSpaceExt = 19,
  kCeil = 20,
  kMaskedFill = 21,
  kLogicalXor = 22,
  kXlogy = 23,
  kGatherDGradV2 = 24,
  kIndex = 25,
  kConstantPadND = 26,
  kCopy = 27,
  kMatMulExt = 28,
  kUpsampleTrilinear3D = 29,
  kContiguous = 30,
  kThresholdGrad = 31,
  kFrac = 32,
  kGeluGradExt = 33,
  kOnes = 34,
  kArgSort = 35,
  kAdaptiveAvgPool3DGradExt = 36,
  kSinh = 37,
  kDiagExt = 38,
  kBaddbmm = 39,
  kInplaceSigmoid = 40,
  kTraceExt = 41,
  kInplaceIndexFillTensor = 42,
  kReduceAny = 43,
  kMv = 44,
  kExpandAs = 45,
  kInplaceMaskedFillTensor = 45,
  kMultiScaleDeformableAttn = 46,
  kUpsampleTrilinear3DGrad = 47,
  kConv1DPadding = 48,
  kInplaceDivMod = 49,
  kInplaceZero = 50,
  kSwigluGrad = 51,
  kFFNExt = 52,
  kInnerInplaceIndexPut = 53,
  kArange = 54,
  kInplaceMaskedFillScalar = 55,
  kInplaceFillDiagonal = 56,
  kRemainderTensorScalar = 57,
  kToDevice = 58,
  kInplaceIndexPut = 59,
  kLogicalNot = 60,
  kLeakyReLUExt = 61,
  kMultiScaleDeformableAttnGrad = 62,
  kRepeatInterleaveInt = 63,
  kLogSumExp = 64,
  kTopkExt = 65,
  kUpsampleLinear1D = 66,
  kFlashAttentionScoreGrad = 67,
  kMaximum = 68,
  kConcat = 69,
  kEluGradExt = 70,
  kSigmoidGrad = 71,
  kAsinhExt = 72,
  kGeLU = 73,
  kMeshgrid = 74,
  kAcoshExt = 74,
  kNonZeroExt = 75,
  kAvgPool2DGrad = 76,
  kRmsNorm = 77,
  kArgMinExt = 78,
  kIndexAddExt = 79,
  kInplaceHardtanh = 80,
  kMaxUnpool2DExt = 81,
  kSeluGrad = 82,
  kInplaceIndexAddExt = 83,
  kPowTensorScalar = 84,
  kBatchNormGatherStatsWithCounts = 85,
  kIsClose = 86,
  kUniqueDim = 87,
  kAllFinite = 88,
  kAvgPool2D = 89,
  kLogAddExp2 = 90,
  kUpsampleNearest3D = 91,
  kMatrixInverseExt = 92,
  kIsInf = 93,
  kInplaceSiLU = 94,
  kErfc = 95,
  kSilentCheckV3 = 96,
  kMSELossGradExt = 97,
  kReluGrad = 98,
  kCumsumExt = 99,
  kRingAttentionUpdate = 100,
  kUniformExt = 101,
  kBinaryCrossEntropyWithLogitsBackward = 102,
  kCast = 103,
  kInplaceBernoulliScalar = 104,
  kInplaceFillScalar = 105,
  kFloorDiv = 106,
  kRandIntLike = 107,
  kInnerUnique = 108,
  kBitwiseAndTensor = 109,
  kErf = 110,
  kAddScalar = 111,
  kIncreFlashAttention = 112,
  kMaskedFillScalar = 113,
  kReflectionPad2DGrad = 114,
  kBatchMatMulExt = 115,
  kNLLLossGrad = 116,
  kLogicalOr = 117,
  kKthvalue = 118,
  kSwiglu = 119,
  kViewAs = 120,
  kInplaceFloorDivides = 120,
  kSliceExtView = 121,
  kInplaceScatterAdd = 122,
  kMuls = 123,
  kNLLLoss2dGrad = 124,
  kTanh = 125,
  kGeluExt = 126,
  kPow = 127,
  kArgMaxExt = 128,
  kMaxPoolGradWithMask = 129,
  kInplaceDiv = 130,
  kFmodScalar = 131,
  kLayerNormExt = 132,
  kSigmoid = 133,
  kRepeatInterleaveTensor = 134,
  kScatterAddExt = 135,
  kRealView = 136,
  kMla = 137,
  kReplicationPad2DGrad = 138,
  kNormalFloatTensor = 139,
  kEmptyLike = 140,
  kSelectV2 = 141,
  kMul = 142,
  kInplaceSubExt = 143,
  kDivMod = 144,
  kEye = 145,
  kScatterValue = 146,
  kInplaceCopy = 147,
  kConvolutionStr = 148,
  kMaskedSelectGrad = 149,
  kChunk = 150,
  kToOther = 151,
  kMax = 152,
  kReflectionPad1D = 153,
  kDropoutGenMaskExt = 154,
  kInplaceMaskedScatter = 155,
  kBroadcastToView = 156,
  kConv3DExt = 157,
  kAdd = 158,
  kNarrow = 159,
  kRandInt = 160,
  kSqueeze = 161,
  kBitwiseNot = 162,
  kTile = 163,
  kMSELossExt = 164,
  kGroupNormGrad = 165,
  kBroadcastTo = 166,
  kTrunc = 167,
  kSortExt = 168,
  kMinimum = 169,
  kSearchSorted = 170,
  kRoll = 171,
  kGreater = 172,
  kNanToNum = 173,
  kBernoulliExt = 174,
  kNewZeros = 175,
  kAtan2Ext = 176,
  kIndexFillTensor = 177,
  kTransposeExtView = 178,
  kDropoutDoMaskExt = 179,
  kHSwishGrad = 180,
  kFullLike = 181,
  kDropoutExt = 182,
  kReplicationPad2D = 183,
  kLogSigmoid = 184,
  kExp = 185,
  kBinaryCrossEntropyGrad = 186,
  kLogSigmoidGrad = 187,
  kLerpScalar = 188,
  kGenerator = 189,
  kGatherD = 190,
  kTensorScatterElements = 191,
  kInplaceScatterSrcReduce = 192,
  kNormalFloatFloat = 193,
  kInplaceClampTensor = 194,
  kSlice = 195,
  kInplaceStopGradient = 196,
  kGridSampler2D = 197,
  kFmodTensor = 198,
  kReduceAll = 199,
  kAcosExt = 200,
  kBitwiseAndScalar = 201,
  kOneHotExt = 202,
  kPReLUGrad = 203,
  kHSigmoid = 204,
  kMinDim = 205,
  kOuter = 206,
  kNewFull = 207,
  kProdExt = 208,
  kHSigmoidGrad = 209,
  kInplaceMul = 210,
  kRepeatInterleaveGrad = 211,
  kMaxPoolGradWithIndices = 212,
  kTan = 213,
  kUpsampleNearest1D = 214,
  kUpsampleBilinear2D = 215,
  kMishExt = 216,
  kVar = 217,
  kMoeDistributeCombine = 218,
  kStackExt = 219,
  kEmbedding = 220,
  kMaxPoolWithIndices = 221,
  kHShrink = 222,
  kLayerNormGradExt = 223,
  kNewOnes = 224,
  kEqual = 225,
  kConvolution = 226,
  kFloor = 227,
  kBitwiseOrScalar = 228,
  kBitwiseOrTensor = 229,
  kInplaceIndexCopy = 230,
  kSelect = 231,
  kSplit = 232,
  kUpsampleNearest1DGrad = 233,
  kSoftMarginLossGrad = 234,
  kAddmv = 235,
  kPowScalarTensor = 236,
  kInplaceTanh = 237,
  kBCEWithLogitsLoss = 238,
  kInplaceBernoulliTensor = 239,
  kCellBackwardHook = 240,
  kReduceMax = 241,
  kLogicalAnd = 242,
  kRmsNormGrad = 243,
  kBatchNormReduceGrad = 244,
  kReplicationPad1D = 245,
  kZerosLikeExt = 246,
  kCol2ImExt = 247,
  kSliceExt = 248,
  kNormalTensorFloat = 249,
  kBatchNormGradExt = 250,
  kAvgPool3DExt = 251,
  kSin = 252,
  kConvTranspose2D = 253,
  kStdMean = 254,
  kConv2DExt = 255,
  kAddLayerNormV2 = 256,
  kInnerIndex = 257,
  kTrilExt = 258,
  kSub = 259,
  kLogSoftmaxExt = 260,
  kAdaptiveAvgPool2DExt = 261,
  kExpandDims = 262,
  kIndexSelect = 263,
  kSiLU = 264,
  kTExt = 265,
  kReduceMin = 265,
  kDiv = 266,
  kCosh = 267,
  kGridSampler3DGrad = 268,
  kAbs = 269,
  kInplaceMatmulAdd = 270,
  kSpeedFusionAttentionGrad = 271,
  kScatter = 272,
  kPagedAttention = 273,
  kSiLUGrad = 274,
  kUpsampleBilinear2DGrad = 275,
  kInplaceLog = 276,
  kAddbmm = 277,
  kMaxPoolWithMask = 278,
  kInplaceRandom = 279,
  kInplaceThreshold = 280,
  kInplaceFloorDivide = 281,
  kErfinv = 282,
  kConv2DPadding = 283,
  kSplitTensorView = 284,
  kDivMods = 285,
  kUpsampleLinear1DGrad = 286,
  kAddcmulExt = 287,
  kSoftmax = 288,
  kGreaterEqualScalar = 289,
  kSplitTensor = 290,
  kNarrowView = 291,
  kInplaceDivMods = 292,
  kInplaceDivs = 293,
  kLogAddExp = 294,
  kRemainderTensorTensor = 295,
  kFloorDivScalar = 296,
  kInplaceRemainderTensorScalar = 297,
  kTranspose = 298,
  kLog = 299,
  kArgMinWithValue = 300,
  kGcd = 301,
  kAddRmsNorm = 302,
  kInplaceIndexFillScalar = 303,
  kCol2ImGrad = 304,
  kAddLayerNormGrad = 305,
  kRandn = 306,
  kCrossEntropyLoss = 307,
  kNorm = 308,
  kBatchNormExt = 309,
  kReLU = 310,
  kBatchNormStats = 311,
  kL1LossBackwardExt = 312,
  kSoftMarginLoss = 313,
  kAddmm = 314,
  kClone = 315,
  kMaskedSelect = 316,
  kIsNegInf = 317,
  kImagView = 318,
  kInplaceRemainderTensorTensor = 319,
  kNormalTensorTensor = 320,
  kAsStrided = 321,
  kKLDivGrad = 322,
  kSoftmaxBackward = 323,
  kPolar = 324,
  kSeLUExt = 325,
  kAllGatherMatmul = 326,
  kAvgPool1D = 327,
  kMishGradExt = 328,
  kExp2 = 329,
  kSilentCheckV2 = 330,
  kReflectionPad1DGrad = 331,
  kSoftplusExt = 332,
  kRotaryPositionEmbeddingGrad = 333,
  kInplaceAddsExt = 334,
  kInnerNonZero = 335,
  kMoeTokenPermuteGrad = 336,
  kSoftShrinkGrad = 337,
  kBitwiseXorScalar = 338,
  kInplaceUniform = 339,
  kMatmulReduceScatter = 340,
  kHistcExt = 341,
  kXLogYScalarSelf = 342,
  kUpsampleNearest2DGrad = 343,
  kRandExt = 344,
  kReflectionPad2D = 345,
  kReplicationPad3DGrad = 346,
  kOnesLikeExt = 347,
  kReshapeAndCache = 348,
  kTanhGrad = 349,
  kUniqueConsecutive = 350,
  kRandnLike = 351,
  kHSwish = 352,
  kCross = 353,
  kLog10 = 354,
  kInplaceFillTensor = 355,
  kSoftShrink = 356,
  kAtanh = 357,
  kSinc = 358,
  kMatMul = 359,
  kMoeDistributeDispatch = 360,
  kNLLLoss = 361,
  kNansum = 362,
  kFillTensor = 363,
  kBinaryCrossEntropy = 364,
  kInplaceClampScalar = 365,
  kApplyRotaryPosEmb = 366,
  kReplicationPad1DGrad = 367,
  kSplitWithSizeView = 368,
  kDivs = 369,
  kAddcdivExt = 370,
  kMaskedScatter = 371,
  kIsFinite = 372,
  kDequantSwigluQuant = 373,
  kIdentity = 374,
  kIm2ColExt = 375,
  kMultinomialExt = 376,
  kCountNonZero = 377,
  kReshape = 378,
  kDropoutGradExt = 379,
  kGeLUGrad = 380,
  kArgMaxWithValue = 381,
  kTake = 382,
  kUnique2 = 383,
  kElu = 384,
  kSplitWithSize = 385,
  kChunkView = 386,
  kInplaceElu = 387,
  kInplaceGroupedMatmulAdd = 388,
  kGreaterEqual = 389,
  kStd = 390,
  kCos = 391,
  kInplaceScatterValue = 392,
  kFillScalar = 393,
  kSumExt = 394,
  kTensorScatterAdd = 395,
  kCustomExt = 396,
  kSqrt = 397,
  kInplaceFloor = 398,
  kCummax = 399,
  kAddExt = 400,
  kUpsampleNearest2D = 401,
  kClampScalar = 402,
  kSquare = 403,
  kLog2 = 404,
  kKLDiv = 405,
  kEmbeddingDenseBackward = 406,
  kNLLLoss2d = 407,
  kInplaceReLU = 408,
  kSelectExtView = 409,
  kMaxDim = 410,
  kLogSoftmaxGrad = 411,
  kVarMean = 412,
  kReflectionPad3D = 413,
  kSpeedFusionAttention = 414,
  kRotaryPositionEmbedding = 415,
  kIndexFillScalar = 416,
  kNewEmpty = 417,
  kGridSampler2DGrad = 418,
  kDot = 419,
  kAdaptiveMaxPool1D = 420,
  kHardtanh = 421,
  kSubExt = 422,
  kNotEqual = 423,
  kAdaptiveAvgPool1D = 424,
  kUnstackExtView = 425,
  kTypeAs = 426,
  kInplaceScatterSrc = 427,
  kAdaptiveAvgPool3DExt = 428,
  kGroupNorm = 429,
  kAsinExt = 430,
  kSmoothL1LossGrad = 431,
  kView = 432,
  kEqualExt = 433,
  kRepeat = 434,
  kBatchMatMul = 435,
  kLerp = 436,
  kHardtanhGrad = 437,
  kAdamW = 438,
  kInnerMoeTokenUnpermute = 439,
  kUpsampleBicubic2DGrad = 440,
  kExpandDimsView = 441,
  kBatchNormElemtGrad = 442,
  kGLU = 443,
  kSoftplusGradExt = 444,
  kNeScalar = 445,
  kCumminExt = 446,
  kTransposeView = 447,
  kMeanExt = 448,
  kReciprocal = 449,
  kInplaceSubScalar = 450,
  kInplaceNormal = 451,
  kInplaceScatterValueReduce = 452,
  kThreshold = 453,
  kInplaceAddExt = 454,
  kFlashAttentionScore = 455,
  kInplaceMuls = 456,
  kDiagonalView = 457,
  kInplaceAddmm = 458,
  kMoeTokenPermute = 459,
  kLeakyReLUGradExt = 460,
  kRsqrt = 461,
  kTriu = 462,
  kLogSoftmax = 463,
  kRandLikeExt = 464,
  kConv3DPadding = 465,
  kRound = 466,
  kGatherNdExt = 467,
  kSubScalar = 468,
  kEmpty = 469,
  kL1LossExt = 470,
  kGridSampler3D = 471,
  kXLogYScalarOther = 472,
  kDense = 473,
  kBincountExt = 474,
  kTriangularSolve = 475,
  kPReLU = 476,
  kNonZero = 477,
  kUpsampleNearest3DGrad = 478,
  kNeg = 479,
  kFlattenExt = 480,
  kInplaceSign = 480,
  kRemainderScalarTensor = 481,
  kToDtype = 482,
  kReverseV2 = 483,
  kAdaptiveAvgPool2DGradExt = 484,
  kMm = 485,
  kBitwiseXorTensor = 486,
  kLessEqual = 487,
  kRandpermExt = 488,
  kSign = 489,
  kConvolutionGrad = 490,
  kClampTensor = 491,
  kMoeTokenUnpermuteGrad = 492,
  kReflectionPad3DGrad = 493,
  kLinalgVectorNorm = 494,
  kEluExt = 495,
  kMedianDim = 496,
  kMedianExt = 497,
  kInplacePut = 498,
  kCrossEntropyLossGrad = 499,
  kPromptFlashAttention = 500,
  kDynamicQuantExt = 501,
  kMoeInitRoutingV2 = 502,
  kKVCacheScatterUpdate = 503,
  kMoeInitRouting = 504,
  kGroupedMatmulV2 = 505,
  kWeightQuantBatchMatmul = 506,
  kMoeFinalizeRouting = 507,
  kAddRmsNormQuantV2 = 508,
  kGroupedMatmul = 509,
  kQuantMatmul = 510,
  kGroupedMatmulV4 = 511,
  kQuantV2 = 512,
  kMoeComputeExpertTokens = 513,
  kMoeInitRoutingQuantV2 = 514,
  kMoeGatingTopKSoftmax = 515,
  kMatmulAllReduceAddRmsNorm = 516,
  kQuantBatchMatmul = 517,
  kFusedInferAttentionScore = 518,
  kDistCommIrecv = 519,
  kDistCommBatchIsendIrecv = 520,
  kDistCommScatterTensor = 521,
  kDistCommAllToAllVC = 522,
  kInnerCommIrecv = 523,
  kInnerCommReduceScatter = 524,
  kDistCommAllGather = 525,
  kDistCommBarrier = 526,
  kInnerCommAllGather = 527,
  kInnerCommIsend = 528,
  kDistCommReduceScatterTensorUneven = 529,
  kDistCommGather = 530,
  kDistCommAllToAllVSingle = 531,
  kDistCommAllGatherIntoTensorUneven = 532,
  kDistCommReduceScatter = 533,
  kDistCommReduce = 534,
  kDistCommAllReduce = 535,
  kInnerCommAllReduce = 536,
  kDistCommAllToAllV = 537,
  kDistCommBroadcast = 538,
  kDistCommIsend = 539,
  kDistCommGatherIntoTensor = 540,
  kInnerCommAllToAllV = 541,
  kDistCommScatter = 542,
  kDistCommAllGatherIntoTensor = 543,
  kDistCommReduceScatterTensor = 544,
  kAnyExt = 545,
  kFuncMaxPool2D = 546,
  kGmm = 547,
  kGmmV2BackwardFusion = 548,
  kAny = 549,
  kDropout2dExt = 550,
  kFuncDropoutExt = 551,
  kGmmBackwardFusion = 552,
  kPixelShuffle = 553,
  kGmmV2 = 554,
  kGmmV2Backward = 555,
  kEinsumExt = 556,
  kInplaceExponential = 557,
  kGmmBackward = 558,
  kMoeTokenUnpermute = 559,
};

using UpsampleBicubic2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using InplaceErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LinalgQrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using HShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using InplaceExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SmoothL1LossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using AvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using AdaptiveMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ConvolutionStrGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using Expm1GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Log1pGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LessGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AtanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReplicationPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using BatchNormElemtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using GluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using Conv1DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using LinSpaceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using CeilGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedFillGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogicalXorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using XlogyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GatherDGradV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ConstantPadNDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &)>;
using CopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleTrilinear3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using ContiguousGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ThresholdGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FracGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GeluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using OnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ArgSortGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using AdaptiveAvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SinhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using DiagExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using BaddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TraceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReduceAnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using MvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMaskedFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MultiScaleDeformableAttnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleTrilinear3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using Conv1DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using InplaceDivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SwigluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using FFNExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InnerInplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using ArangeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceMaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceFillDiagonalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using RemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using ToDeviceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using LogicalNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using LeakyReLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MultiScaleDeformableAttnGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LogSumExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using TopkExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using UpsampleLinear1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using FlashAttentionScoreGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MaximumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ConcatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using EluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using SigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AsinhExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GeLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AcoshExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NonZeroExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AvgPool2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using ArgMinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using IndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceHardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MaxUnpool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using SeluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using PowTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BatchNormGatherStatsWithCountsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using IsCloseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using UniqueDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using AllFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using AvgPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LogAddExp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using MatrixInverseExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using IsInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SilentCheckV3GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MSELossGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ReluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CumsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RingAttentionUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using UniformExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyWithLogitsBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using CastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceBernoulliScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FloorDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RandIntLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InnerUniqueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using BitwiseAndTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using IncreFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using ReflectionPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using BatchMatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NLLLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using LogicalOrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using KthvalueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SwigluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceFloorDividesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SliceExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using InplaceScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using NLLLoss2dGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using TanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GeluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using PowGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ArgMaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using MaxPoolGradWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FmodScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using LayerNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using SigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ScatterAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RealViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MlaGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReplicationPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using NormalFloatTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EmptyLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using SelectV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using DivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using EyeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using ConvolutionStrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using MaskedSelectGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ChunkGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using ToOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReflectionPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using DropoutGenMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceMaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BroadcastToViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using Conv3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using AddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NarrowGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using RandIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using SqueezeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using BitwiseNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TileGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MSELossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GroupNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using BroadcastToGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using TruncGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SortExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MinimumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SearchSortedGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using RollGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using GreaterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NanToNumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &)>;
using BernoulliExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NewZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using Atan2ExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using TransposeExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using DropoutDoMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using HSwishGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FullLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using DropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReplicationPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using LogSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using LogSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LerpScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GeneratorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using GatherDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using TensorScatterElementsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceScatterSrcReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using NormalFloatFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using SliceGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &)>;
using InplaceStopGradientGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GridSampler2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using FmodTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReduceAllGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using AcosExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseAndScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using OneHotExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using PReLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using HSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MinDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using OuterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NewFullGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ProdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using HSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MaxPoolGradWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using TanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using UpsampleBilinear2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using MishExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using VarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeDistributeCombineGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using StackExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using EmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using MaxPoolWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using HShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using LayerNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using NewOnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using EqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ConvolutionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using FloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseOrScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BitwiseOrTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using UpsampleNearest1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using SoftMarginLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using AddmvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using PowScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceTanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BCEWithLogitsLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using InplaceBernoulliTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CellBackwardHookGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using ReduceMaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using LogicalAndGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RmsNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormReduceGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ZerosLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using Col2ImExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using SliceExtGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using NormalTensorFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::ValueTuplePtr &)>;
using AvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using SinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ConvTranspose2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using StdMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using Conv2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using AddLayerNormV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using InnerIndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using TrilExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SubGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogSoftmaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using AdaptiveAvgPool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ExpandDimsGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using IndexSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using SiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReduceMinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using DivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CoshGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GridSampler3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using AbsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SpeedFusionAttentionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using PagedAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using SiLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleBilinear2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using InplaceLogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MaxPoolWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceRandomGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceFloorDivideGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Conv2DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using SplitTensorViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using DivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UpsampleLinear1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using AddcmulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using GreaterEqualScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SplitTensorGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using NarrowViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using InplaceDivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceDivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using LogAddExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FloorDivScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceRemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using TransposeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using LogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ArgMinWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using GcdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using InplaceIndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using Col2ImGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using AddLayerNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RandnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using CrossEntropyLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using NormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using BatchNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using ReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormStatsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using L1LossBackwardExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SoftMarginLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using AddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using CloneGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IsNegInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ImagViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceRemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AsStridedGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &, const int64_t &)>;
using KLDivGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SoftmaxBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using PolarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SeLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AllGatherMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using AvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MishGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Exp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SilentCheckV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SoftplusExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using RotaryPositionEmbeddingGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using InplaceAddsExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InnerNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MoeTokenPermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SoftShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using BitwiseXorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceUniformGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MatmulReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using HistcExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using XLogYScalarSelfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using RandExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReflectionPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ReplicationPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using OnesLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReshapeAndCacheGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using TanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UniqueConsecutiveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RandnLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using HSwishGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using CrossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using Log10GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SoftShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using AtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SincGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeDistributeDispatchGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using NLLLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using NansumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using FillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using BinaryCrossEntropyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using InplaceClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using ApplyRotaryPosEmbGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ReplicationPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SplitWithSizeViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using DivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AddcdivExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IsFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using DequantSwigluQuantGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using IdentityGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Im2ColExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using MultinomialExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CountNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ReshapeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using DropoutGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GeLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ArgMaxWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using TakeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Unique2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using EluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using SplitWithSizeGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using ChunkViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using InplaceEluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using InplaceGroupedMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GreaterEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using StdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using CosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using SumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using TensorScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CustomExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using SqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using CummaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using AddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using UpsampleNearest2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using SquareGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Log2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using KLDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using EmbeddingDenseBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using NLLLoss2dGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SelectExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using MaxDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using LogSoftmaxGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using VarMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using ReflectionPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SpeedFusionAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using RotaryPositionEmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using IndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using NewEmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using GridSampler2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using DotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveMaxPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using HardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using SubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using NotEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveAvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using UnstackExtViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using TypeAsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterSrcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveAvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using GroupNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using AsinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SmoothL1LossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using EqualExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using BatchMatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using LerpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using HardtanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using AdamWGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InnerMoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using UpsampleBicubic2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using ExpandDimsViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using BatchNormElemtGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SoftplusGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using NeScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using CumminExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using TransposeViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using MeanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReciprocalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceNormalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterValueReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using ThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using FlashAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceMulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using DiagonalViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using InplaceAddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MoeTokenPermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using LeakyReLUGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using RsqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TriuGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using LogSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using RandLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using Conv3DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using RoundGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GatherNdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using EmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using L1LossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GridSampler3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using XLogYScalarOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using DenseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using BincountExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using TriangularSolveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using PReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleNearest3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using NegGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RemainderScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using ToDtypeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ReverseV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using AdaptiveAvgPool2DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseXorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LessEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RandpermExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ConvolutionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using ClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using MoeTokenUnpermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ReflectionPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using LinalgVectorNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using EluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using MedianDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using MedianExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplacePutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using CrossEntropyLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using PromptFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DynamicQuantExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using MoeInitRoutingV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using KVCacheScatterUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GroupedMatmulV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using WeightQuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeFinalizeRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using AddRmsNormQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using GroupedMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using QuantMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using GroupedMatmulV4GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using QuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeComputeExpertTokensGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using MoeGatingTopKSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using MatmulAllReduceAddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using QuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using FusedInferAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBatchIsendIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using DistCommScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVCGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InnerCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using InnerCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBarrierGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommReduceScatterTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVSingleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommAllGatherIntoTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using DistCommBroadcastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using AnyExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using FuncMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using GmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GmmV2BackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using AnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Dropout2dExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FuncDropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GmmBackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using PixelShuffleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GmmV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GmmV2BackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using EinsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceExponentialGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GmmBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using MoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;

struct OpsAutoGradRegisters {
  UpsampleBicubic2DGradFunc UpsampleBicubic2DGradFuncObj;
  InplaceErfinvGradFunc InplaceErfinvGradFuncObj;
  LinalgQrGradFunc LinalgQrGradFuncObj;
  HShrinkGradGradFunc HShrinkGradGradFuncObj;
  InplaceExpGradFunc InplaceExpGradFuncObj;
  SmoothL1LossGradFunc SmoothL1LossGradFuncObj;
  AvgPool3DGradExtGradFunc AvgPool3DGradExtGradFuncObj;
  AdaptiveMaxPool2DGradFunc AdaptiveMaxPool2DGradFuncObj;
  ConvolutionStrGradGradFunc ConvolutionStrGradGradFuncObj;
  Expm1GradFunc Expm1GradFuncObj;
  MinGradFunc MinGradFuncObj;
  Log1pGradFunc Log1pGradFuncObj;
  LessGradFunc LessGradFuncObj;
  AtanExtGradFunc AtanExtGradFuncObj;
  ReplicationPad3DGradFunc ReplicationPad3DGradFuncObj;
  BatchNormElemtGradFunc BatchNormElemtGradFuncObj;
  GluGradGradFunc GluGradGradFuncObj;
  ZerosGradFunc ZerosGradFuncObj;
  Conv1DExtGradFunc Conv1DExtGradFuncObj;
  LinSpaceExtGradFunc LinSpaceExtGradFuncObj;
  CeilGradFunc CeilGradFuncObj;
  MaskedFillGradFunc MaskedFillGradFuncObj;
  LogicalXorGradFunc LogicalXorGradFuncObj;
  XlogyGradFunc XlogyGradFuncObj;
  GatherDGradV2GradFunc GatherDGradV2GradFuncObj;
  IndexGradFunc IndexGradFuncObj;
  ConstantPadNDGradFunc ConstantPadNDGradFuncObj;
  CopyGradFunc CopyGradFuncObj;
  MatMulExtGradFunc MatMulExtGradFuncObj;
  UpsampleTrilinear3DGradFunc UpsampleTrilinear3DGradFuncObj;
  ContiguousGradFunc ContiguousGradFuncObj;
  ThresholdGradGradFunc ThresholdGradGradFuncObj;
  FracGradFunc FracGradFuncObj;
  GeluGradExtGradFunc GeluGradExtGradFuncObj;
  OnesGradFunc OnesGradFuncObj;
  ArgSortGradFunc ArgSortGradFuncObj;
  AdaptiveAvgPool3DGradExtGradFunc AdaptiveAvgPool3DGradExtGradFuncObj;
  SinhGradFunc SinhGradFuncObj;
  DiagExtGradFunc DiagExtGradFuncObj;
  BaddbmmGradFunc BaddbmmGradFuncObj;
  InplaceSigmoidGradFunc InplaceSigmoidGradFuncObj;
  TraceExtGradFunc TraceExtGradFuncObj;
  InplaceIndexFillTensorGradFunc InplaceIndexFillTensorGradFuncObj;
  ReduceAnyGradFunc ReduceAnyGradFuncObj;
  MvGradFunc MvGradFuncObj;
  InplaceMaskedFillTensorGradFunc InplaceMaskedFillTensorGradFuncObj;
  MultiScaleDeformableAttnGradFunc MultiScaleDeformableAttnGradFuncObj;
  UpsampleTrilinear3DGradGradFunc UpsampleTrilinear3DGradGradFuncObj;
  Conv1DPaddingGradFunc Conv1DPaddingGradFuncObj;
  InplaceDivModGradFunc InplaceDivModGradFuncObj;
  InplaceZeroGradFunc InplaceZeroGradFuncObj;
  SwigluGradGradFunc SwigluGradGradFuncObj;
  FFNExtGradFunc FFNExtGradFuncObj;
  InnerInplaceIndexPutGradFunc InnerInplaceIndexPutGradFuncObj;
  ArangeGradFunc ArangeGradFuncObj;
  InplaceMaskedFillScalarGradFunc InplaceMaskedFillScalarGradFuncObj;
  InplaceFillDiagonalGradFunc InplaceFillDiagonalGradFuncObj;
  RemainderTensorScalarGradFunc RemainderTensorScalarGradFuncObj;
  ToDeviceGradFunc ToDeviceGradFuncObj;
  InplaceIndexPutGradFunc InplaceIndexPutGradFuncObj;
  LogicalNotGradFunc LogicalNotGradFuncObj;
  LeakyReLUExtGradFunc LeakyReLUExtGradFuncObj;
  MultiScaleDeformableAttnGradGradFunc MultiScaleDeformableAttnGradGradFuncObj;
  RepeatInterleaveIntGradFunc RepeatInterleaveIntGradFuncObj;
  LogSumExpGradFunc LogSumExpGradFuncObj;
  TopkExtGradFunc TopkExtGradFuncObj;
  UpsampleLinear1DGradFunc UpsampleLinear1DGradFuncObj;
  FlashAttentionScoreGradGradFunc FlashAttentionScoreGradGradFuncObj;
  MaximumGradFunc MaximumGradFuncObj;
  ConcatGradFunc ConcatGradFuncObj;
  EluGradExtGradFunc EluGradExtGradFuncObj;
  SigmoidGradGradFunc SigmoidGradGradFuncObj;
  AsinhExtGradFunc AsinhExtGradFuncObj;
  GeLUGradFunc GeLUGradFuncObj;
  AcoshExtGradFunc AcoshExtGradFuncObj;
  NonZeroExtGradFunc NonZeroExtGradFuncObj;
  AvgPool2DGradGradFunc AvgPool2DGradGradFuncObj;
  RmsNormGradFunc RmsNormGradFuncObj;
  ArgMinExtGradFunc ArgMinExtGradFuncObj;
  IndexAddExtGradFunc IndexAddExtGradFuncObj;
  InplaceHardtanhGradFunc InplaceHardtanhGradFuncObj;
  MaxUnpool2DExtGradFunc MaxUnpool2DExtGradFuncObj;
  SeluGradGradFunc SeluGradGradFuncObj;
  InplaceIndexAddExtGradFunc InplaceIndexAddExtGradFuncObj;
  PowTensorScalarGradFunc PowTensorScalarGradFuncObj;
  BatchNormGatherStatsWithCountsGradFunc BatchNormGatherStatsWithCountsGradFuncObj;
  IsCloseGradFunc IsCloseGradFuncObj;
  UniqueDimGradFunc UniqueDimGradFuncObj;
  AllFiniteGradFunc AllFiniteGradFuncObj;
  AvgPool2DGradFunc AvgPool2DGradFuncObj;
  LogAddExp2GradFunc LogAddExp2GradFuncObj;
  UpsampleNearest3DGradFunc UpsampleNearest3DGradFuncObj;
  MatrixInverseExtGradFunc MatrixInverseExtGradFuncObj;
  IsInfGradFunc IsInfGradFuncObj;
  InplaceSiLUGradFunc InplaceSiLUGradFuncObj;
  ErfcGradFunc ErfcGradFuncObj;
  SilentCheckV3GradFunc SilentCheckV3GradFuncObj;
  MSELossGradExtGradFunc MSELossGradExtGradFuncObj;
  ReluGradGradFunc ReluGradGradFuncObj;
  CumsumExtGradFunc CumsumExtGradFuncObj;
  RingAttentionUpdateGradFunc RingAttentionUpdateGradFuncObj;
  UniformExtGradFunc UniformExtGradFuncObj;
  BinaryCrossEntropyWithLogitsBackwardGradFunc BinaryCrossEntropyWithLogitsBackwardGradFuncObj;
  CastGradFunc CastGradFuncObj;
  InplaceBernoulliScalarGradFunc InplaceBernoulliScalarGradFuncObj;
  InplaceFillScalarGradFunc InplaceFillScalarGradFuncObj;
  FloorDivGradFunc FloorDivGradFuncObj;
  RandIntLikeGradFunc RandIntLikeGradFuncObj;
  InnerUniqueGradFunc InnerUniqueGradFuncObj;
  BitwiseAndTensorGradFunc BitwiseAndTensorGradFuncObj;
  ErfGradFunc ErfGradFuncObj;
  AddScalarGradFunc AddScalarGradFuncObj;
  IncreFlashAttentionGradFunc IncreFlashAttentionGradFuncObj;
  MaskedFillScalarGradFunc MaskedFillScalarGradFuncObj;
  ReflectionPad2DGradGradFunc ReflectionPad2DGradGradFuncObj;
  BatchMatMulExtGradFunc BatchMatMulExtGradFuncObj;
  NLLLossGradGradFunc NLLLossGradGradFuncObj;
  LogicalOrGradFunc LogicalOrGradFuncObj;
  KthvalueGradFunc KthvalueGradFuncObj;
  SwigluGradFunc SwigluGradFuncObj;
  InplaceFloorDividesGradFunc InplaceFloorDividesGradFuncObj;
  SliceExtViewGradFunc SliceExtViewGradFuncObj;
  InplaceScatterAddGradFunc InplaceScatterAddGradFuncObj;
  MulsGradFunc MulsGradFuncObj;
  NLLLoss2dGradGradFunc NLLLoss2dGradGradFuncObj;
  TanhGradFunc TanhGradFuncObj;
  GeluExtGradFunc GeluExtGradFuncObj;
  PowGradFunc PowGradFuncObj;
  ArgMaxExtGradFunc ArgMaxExtGradFuncObj;
  MaxPoolGradWithMaskGradFunc MaxPoolGradWithMaskGradFuncObj;
  InplaceDivGradFunc InplaceDivGradFuncObj;
  FmodScalarGradFunc FmodScalarGradFuncObj;
  LayerNormExtGradFunc LayerNormExtGradFuncObj;
  SigmoidGradFunc SigmoidGradFuncObj;
  RepeatInterleaveTensorGradFunc RepeatInterleaveTensorGradFuncObj;
  ScatterAddExtGradFunc ScatterAddExtGradFuncObj;
  RealViewGradFunc RealViewGradFuncObj;
  MlaGradFunc MlaGradFuncObj;
  ReplicationPad2DGradGradFunc ReplicationPad2DGradGradFuncObj;
  NormalFloatTensorGradFunc NormalFloatTensorGradFuncObj;
  EmptyLikeGradFunc EmptyLikeGradFuncObj;
  SelectV2GradFunc SelectV2GradFuncObj;
  MulGradFunc MulGradFuncObj;
  InplaceSubExtGradFunc InplaceSubExtGradFuncObj;
  DivModGradFunc DivModGradFuncObj;
  EyeGradFunc EyeGradFuncObj;
  ScatterValueGradFunc ScatterValueGradFuncObj;
  InplaceCopyGradFunc InplaceCopyGradFuncObj;
  ConvolutionStrGradFunc ConvolutionStrGradFuncObj;
  MaskedSelectGradGradFunc MaskedSelectGradGradFuncObj;
  ChunkGradFunc ChunkGradFuncObj;
  ToOtherGradFunc ToOtherGradFuncObj;
  MaxGradFunc MaxGradFuncObj;
  ReflectionPad1DGradFunc ReflectionPad1DGradFuncObj;
  DropoutGenMaskExtGradFunc DropoutGenMaskExtGradFuncObj;
  InplaceMaskedScatterGradFunc InplaceMaskedScatterGradFuncObj;
  BroadcastToViewGradFunc BroadcastToViewGradFuncObj;
  Conv3DExtGradFunc Conv3DExtGradFuncObj;
  AddGradFunc AddGradFuncObj;
  NarrowGradFunc NarrowGradFuncObj;
  RandIntGradFunc RandIntGradFuncObj;
  SqueezeGradFunc SqueezeGradFuncObj;
  BitwiseNotGradFunc BitwiseNotGradFuncObj;
  TileGradFunc TileGradFuncObj;
  MSELossExtGradFunc MSELossExtGradFuncObj;
  GroupNormGradGradFunc GroupNormGradGradFuncObj;
  BroadcastToGradFunc BroadcastToGradFuncObj;
  TruncGradFunc TruncGradFuncObj;
  SortExtGradFunc SortExtGradFuncObj;
  MinimumGradFunc MinimumGradFuncObj;
  SearchSortedGradFunc SearchSortedGradFuncObj;
  RollGradFunc RollGradFuncObj;
  GreaterGradFunc GreaterGradFuncObj;
  NanToNumGradFunc NanToNumGradFuncObj;
  BernoulliExtGradFunc BernoulliExtGradFuncObj;
  NewZerosGradFunc NewZerosGradFuncObj;
  Atan2ExtGradFunc Atan2ExtGradFuncObj;
  IndexFillTensorGradFunc IndexFillTensorGradFuncObj;
  TransposeExtViewGradFunc TransposeExtViewGradFuncObj;
  DropoutDoMaskExtGradFunc DropoutDoMaskExtGradFuncObj;
  HSwishGradGradFunc HSwishGradGradFuncObj;
  FullLikeGradFunc FullLikeGradFuncObj;
  DropoutExtGradFunc DropoutExtGradFuncObj;
  ReplicationPad2DGradFunc ReplicationPad2DGradFuncObj;
  LogSigmoidGradFunc LogSigmoidGradFuncObj;
  ExpGradFunc ExpGradFuncObj;
  BinaryCrossEntropyGradGradFunc BinaryCrossEntropyGradGradFuncObj;
  LogSigmoidGradGradFunc LogSigmoidGradGradFuncObj;
  LerpScalarGradFunc LerpScalarGradFuncObj;
  GeneratorGradFunc GeneratorGradFuncObj;
  GatherDGradFunc GatherDGradFuncObj;
  TensorScatterElementsGradFunc TensorScatterElementsGradFuncObj;
  InplaceScatterSrcReduceGradFunc InplaceScatterSrcReduceGradFuncObj;
  NormalFloatFloatGradFunc NormalFloatFloatGradFuncObj;
  InplaceClampTensorGradFunc InplaceClampTensorGradFuncObj;
  SliceGradFunc SliceGradFuncObj;
  InplaceStopGradientGradFunc InplaceStopGradientGradFuncObj;
  GridSampler2DGradFunc GridSampler2DGradFuncObj;
  FmodTensorGradFunc FmodTensorGradFuncObj;
  ReduceAllGradFunc ReduceAllGradFuncObj;
  AcosExtGradFunc AcosExtGradFuncObj;
  BitwiseAndScalarGradFunc BitwiseAndScalarGradFuncObj;
  OneHotExtGradFunc OneHotExtGradFuncObj;
  PReLUGradGradFunc PReLUGradGradFuncObj;
  HSigmoidGradFunc HSigmoidGradFuncObj;
  MinDimGradFunc MinDimGradFuncObj;
  OuterGradFunc OuterGradFuncObj;
  NewFullGradFunc NewFullGradFuncObj;
  ProdExtGradFunc ProdExtGradFuncObj;
  HSigmoidGradGradFunc HSigmoidGradGradFuncObj;
  InplaceMulGradFunc InplaceMulGradFuncObj;
  RepeatInterleaveGradGradFunc RepeatInterleaveGradGradFuncObj;
  MaxPoolGradWithIndicesGradFunc MaxPoolGradWithIndicesGradFuncObj;
  TanGradFunc TanGradFuncObj;
  UpsampleNearest1DGradFunc UpsampleNearest1DGradFuncObj;
  UpsampleBilinear2DGradFunc UpsampleBilinear2DGradFuncObj;
  MishExtGradFunc MishExtGradFuncObj;
  VarGradFunc VarGradFuncObj;
  MoeDistributeCombineGradFunc MoeDistributeCombineGradFuncObj;
  StackExtGradFunc StackExtGradFuncObj;
  EmbeddingGradFunc EmbeddingGradFuncObj;
  MaxPoolWithIndicesGradFunc MaxPoolWithIndicesGradFuncObj;
  HShrinkGradFunc HShrinkGradFuncObj;
  LayerNormGradExtGradFunc LayerNormGradExtGradFuncObj;
  NewOnesGradFunc NewOnesGradFuncObj;
  EqualGradFunc EqualGradFuncObj;
  ConvolutionGradFunc ConvolutionGradFuncObj;
  FloorGradFunc FloorGradFuncObj;
  BitwiseOrScalarGradFunc BitwiseOrScalarGradFuncObj;
  BitwiseOrTensorGradFunc BitwiseOrTensorGradFuncObj;
  InplaceIndexCopyGradFunc InplaceIndexCopyGradFuncObj;
  SelectGradFunc SelectGradFuncObj;
  SplitGradFunc SplitGradFuncObj;
  UpsampleNearest1DGradGradFunc UpsampleNearest1DGradGradFuncObj;
  SoftMarginLossGradGradFunc SoftMarginLossGradGradFuncObj;
  AddmvGradFunc AddmvGradFuncObj;
  PowScalarTensorGradFunc PowScalarTensorGradFuncObj;
  InplaceTanhGradFunc InplaceTanhGradFuncObj;
  BCEWithLogitsLossGradFunc BCEWithLogitsLossGradFuncObj;
  InplaceBernoulliTensorGradFunc InplaceBernoulliTensorGradFuncObj;
  CellBackwardHookGradFunc CellBackwardHookGradFuncObj;
  ReduceMaxGradFunc ReduceMaxGradFuncObj;
  LogicalAndGradFunc LogicalAndGradFuncObj;
  RmsNormGradGradFunc RmsNormGradGradFuncObj;
  BatchNormReduceGradGradFunc BatchNormReduceGradGradFuncObj;
  ReplicationPad1DGradFunc ReplicationPad1DGradFuncObj;
  ZerosLikeExtGradFunc ZerosLikeExtGradFuncObj;
  Col2ImExtGradFunc Col2ImExtGradFuncObj;
  SliceExtGradFunc SliceExtGradFuncObj;
  NormalTensorFloatGradFunc NormalTensorFloatGradFuncObj;
  BatchNormGradExtGradFunc BatchNormGradExtGradFuncObj;
  AvgPool3DExtGradFunc AvgPool3DExtGradFuncObj;
  SinGradFunc SinGradFuncObj;
  ConvTranspose2DGradFunc ConvTranspose2DGradFuncObj;
  StdMeanGradFunc StdMeanGradFuncObj;
  Conv2DExtGradFunc Conv2DExtGradFuncObj;
  AddLayerNormV2GradFunc AddLayerNormV2GradFuncObj;
  InnerIndexGradFunc InnerIndexGradFuncObj;
  TrilExtGradFunc TrilExtGradFuncObj;
  SubGradFunc SubGradFuncObj;
  LogSoftmaxExtGradFunc LogSoftmaxExtGradFuncObj;
  AdaptiveAvgPool2DExtGradFunc AdaptiveAvgPool2DExtGradFuncObj;
  ExpandDimsGradFunc ExpandDimsGradFuncObj;
  IndexSelectGradFunc IndexSelectGradFuncObj;
  SiLUGradFunc SiLUGradFuncObj;
  ReduceMinGradFunc ReduceMinGradFuncObj;
  DivGradFunc DivGradFuncObj;
  CoshGradFunc CoshGradFuncObj;
  GridSampler3DGradGradFunc GridSampler3DGradGradFuncObj;
  AbsGradFunc AbsGradFuncObj;
  InplaceMatmulAddGradFunc InplaceMatmulAddGradFuncObj;
  SpeedFusionAttentionGradGradFunc SpeedFusionAttentionGradGradFuncObj;
  ScatterGradFunc ScatterGradFuncObj;
  PagedAttentionGradFunc PagedAttentionGradFuncObj;
  SiLUGradGradFunc SiLUGradGradFuncObj;
  UpsampleBilinear2DGradGradFunc UpsampleBilinear2DGradGradFuncObj;
  InplaceLogGradFunc InplaceLogGradFuncObj;
  AddbmmGradFunc AddbmmGradFuncObj;
  MaxPoolWithMaskGradFunc MaxPoolWithMaskGradFuncObj;
  InplaceRandomGradFunc InplaceRandomGradFuncObj;
  InplaceThresholdGradFunc InplaceThresholdGradFuncObj;
  InplaceFloorDivideGradFunc InplaceFloorDivideGradFuncObj;
  ErfinvGradFunc ErfinvGradFuncObj;
  Conv2DPaddingGradFunc Conv2DPaddingGradFuncObj;
  SplitTensorViewGradFunc SplitTensorViewGradFuncObj;
  DivModsGradFunc DivModsGradFuncObj;
  UpsampleLinear1DGradGradFunc UpsampleLinear1DGradGradFuncObj;
  AddcmulExtGradFunc AddcmulExtGradFuncObj;
  SoftmaxGradFunc SoftmaxGradFuncObj;
  GreaterEqualScalarGradFunc GreaterEqualScalarGradFuncObj;
  SplitTensorGradFunc SplitTensorGradFuncObj;
  NarrowViewGradFunc NarrowViewGradFuncObj;
  InplaceDivModsGradFunc InplaceDivModsGradFuncObj;
  InplaceDivsGradFunc InplaceDivsGradFuncObj;
  LogAddExpGradFunc LogAddExpGradFuncObj;
  RemainderTensorTensorGradFunc RemainderTensorTensorGradFuncObj;
  FloorDivScalarGradFunc FloorDivScalarGradFuncObj;
  InplaceRemainderTensorScalarGradFunc InplaceRemainderTensorScalarGradFuncObj;
  TransposeGradFunc TransposeGradFuncObj;
  LogGradFunc LogGradFuncObj;
  ArgMinWithValueGradFunc ArgMinWithValueGradFuncObj;
  GcdGradFunc GcdGradFuncObj;
  AddRmsNormGradFunc AddRmsNormGradFuncObj;
  InplaceIndexFillScalarGradFunc InplaceIndexFillScalarGradFuncObj;
  Col2ImGradGradFunc Col2ImGradGradFuncObj;
  AddLayerNormGradGradFunc AddLayerNormGradGradFuncObj;
  RandnGradFunc RandnGradFuncObj;
  CrossEntropyLossGradFunc CrossEntropyLossGradFuncObj;
  NormGradFunc NormGradFuncObj;
  BatchNormExtGradFunc BatchNormExtGradFuncObj;
  ReLUGradFunc ReLUGradFuncObj;
  BatchNormStatsGradFunc BatchNormStatsGradFuncObj;
  L1LossBackwardExtGradFunc L1LossBackwardExtGradFuncObj;
  SoftMarginLossGradFunc SoftMarginLossGradFuncObj;
  AddmmGradFunc AddmmGradFuncObj;
  CloneGradFunc CloneGradFuncObj;
  MaskedSelectGradFunc MaskedSelectGradFuncObj;
  IsNegInfGradFunc IsNegInfGradFuncObj;
  ImagViewGradFunc ImagViewGradFuncObj;
  InplaceRemainderTensorTensorGradFunc InplaceRemainderTensorTensorGradFuncObj;
  NormalTensorTensorGradFunc NormalTensorTensorGradFuncObj;
  AsStridedGradFunc AsStridedGradFuncObj;
  KLDivGradGradFunc KLDivGradGradFuncObj;
  SoftmaxBackwardGradFunc SoftmaxBackwardGradFuncObj;
  PolarGradFunc PolarGradFuncObj;
  SeLUExtGradFunc SeLUExtGradFuncObj;
  AllGatherMatmulGradFunc AllGatherMatmulGradFuncObj;
  AvgPool1DGradFunc AvgPool1DGradFuncObj;
  MishGradExtGradFunc MishGradExtGradFuncObj;
  Exp2GradFunc Exp2GradFuncObj;
  SilentCheckV2GradFunc SilentCheckV2GradFuncObj;
  ReflectionPad1DGradGradFunc ReflectionPad1DGradGradFuncObj;
  SoftplusExtGradFunc SoftplusExtGradFuncObj;
  RotaryPositionEmbeddingGradGradFunc RotaryPositionEmbeddingGradGradFuncObj;
  InplaceAddsExtGradFunc InplaceAddsExtGradFuncObj;
  InnerNonZeroGradFunc InnerNonZeroGradFuncObj;
  MoeTokenPermuteGradGradFunc MoeTokenPermuteGradGradFuncObj;
  SoftShrinkGradGradFunc SoftShrinkGradGradFuncObj;
  BitwiseXorScalarGradFunc BitwiseXorScalarGradFuncObj;
  InplaceUniformGradFunc InplaceUniformGradFuncObj;
  MatmulReduceScatterGradFunc MatmulReduceScatterGradFuncObj;
  HistcExtGradFunc HistcExtGradFuncObj;
  XLogYScalarSelfGradFunc XLogYScalarSelfGradFuncObj;
  UpsampleNearest2DGradGradFunc UpsampleNearest2DGradGradFuncObj;
  RandExtGradFunc RandExtGradFuncObj;
  ReflectionPad2DGradFunc ReflectionPad2DGradFuncObj;
  ReplicationPad3DGradGradFunc ReplicationPad3DGradGradFuncObj;
  OnesLikeExtGradFunc OnesLikeExtGradFuncObj;
  ReshapeAndCacheGradFunc ReshapeAndCacheGradFuncObj;
  TanhGradGradFunc TanhGradGradFuncObj;
  UniqueConsecutiveGradFunc UniqueConsecutiveGradFuncObj;
  RandnLikeGradFunc RandnLikeGradFuncObj;
  HSwishGradFunc HSwishGradFuncObj;
  CrossGradFunc CrossGradFuncObj;
  Log10GradFunc Log10GradFuncObj;
  InplaceFillTensorGradFunc InplaceFillTensorGradFuncObj;
  SoftShrinkGradFunc SoftShrinkGradFuncObj;
  AtanhGradFunc AtanhGradFuncObj;
  SincGradFunc SincGradFuncObj;
  MatMulGradFunc MatMulGradFuncObj;
  MoeDistributeDispatchGradFunc MoeDistributeDispatchGradFuncObj;
  NLLLossGradFunc NLLLossGradFuncObj;
  NansumGradFunc NansumGradFuncObj;
  FillTensorGradFunc FillTensorGradFuncObj;
  BinaryCrossEntropyGradFunc BinaryCrossEntropyGradFuncObj;
  InplaceClampScalarGradFunc InplaceClampScalarGradFuncObj;
  ApplyRotaryPosEmbGradFunc ApplyRotaryPosEmbGradFuncObj;
  ReplicationPad1DGradGradFunc ReplicationPad1DGradGradFuncObj;
  SplitWithSizeViewGradFunc SplitWithSizeViewGradFuncObj;
  DivsGradFunc DivsGradFuncObj;
  AddcdivExtGradFunc AddcdivExtGradFuncObj;
  MaskedScatterGradFunc MaskedScatterGradFuncObj;
  IsFiniteGradFunc IsFiniteGradFuncObj;
  DequantSwigluQuantGradFunc DequantSwigluQuantGradFuncObj;
  IdentityGradFunc IdentityGradFuncObj;
  Im2ColExtGradFunc Im2ColExtGradFuncObj;
  MultinomialExtGradFunc MultinomialExtGradFuncObj;
  CountNonZeroGradFunc CountNonZeroGradFuncObj;
  ReshapeGradFunc ReshapeGradFuncObj;
  DropoutGradExtGradFunc DropoutGradExtGradFuncObj;
  GeLUGradGradFunc GeLUGradGradFuncObj;
  ArgMaxWithValueGradFunc ArgMaxWithValueGradFuncObj;
  TakeGradFunc TakeGradFuncObj;
  Unique2GradFunc Unique2GradFuncObj;
  EluGradFunc EluGradFuncObj;
  SplitWithSizeGradFunc SplitWithSizeGradFuncObj;
  ChunkViewGradFunc ChunkViewGradFuncObj;
  InplaceEluGradFunc InplaceEluGradFuncObj;
  InplaceGroupedMatmulAddGradFunc InplaceGroupedMatmulAddGradFuncObj;
  GreaterEqualGradFunc GreaterEqualGradFuncObj;
  StdGradFunc StdGradFuncObj;
  CosGradFunc CosGradFuncObj;
  InplaceScatterValueGradFunc InplaceScatterValueGradFuncObj;
  FillScalarGradFunc FillScalarGradFuncObj;
  SumExtGradFunc SumExtGradFuncObj;
  TensorScatterAddGradFunc TensorScatterAddGradFuncObj;
  CustomExtGradFunc CustomExtGradFuncObj;
  SqrtGradFunc SqrtGradFuncObj;
  InplaceFloorGradFunc InplaceFloorGradFuncObj;
  CummaxGradFunc CummaxGradFuncObj;
  AddExtGradFunc AddExtGradFuncObj;
  UpsampleNearest2DGradFunc UpsampleNearest2DGradFuncObj;
  ClampScalarGradFunc ClampScalarGradFuncObj;
  SquareGradFunc SquareGradFuncObj;
  Log2GradFunc Log2GradFuncObj;
  KLDivGradFunc KLDivGradFuncObj;
  EmbeddingDenseBackwardGradFunc EmbeddingDenseBackwardGradFuncObj;
  NLLLoss2dGradFunc NLLLoss2dGradFuncObj;
  InplaceReLUGradFunc InplaceReLUGradFuncObj;
  SelectExtViewGradFunc SelectExtViewGradFuncObj;
  MaxDimGradFunc MaxDimGradFuncObj;
  LogSoftmaxGradGradFunc LogSoftmaxGradGradFuncObj;
  VarMeanGradFunc VarMeanGradFuncObj;
  ReflectionPad3DGradFunc ReflectionPad3DGradFuncObj;
  SpeedFusionAttentionGradFunc SpeedFusionAttentionGradFuncObj;
  RotaryPositionEmbeddingGradFunc RotaryPositionEmbeddingGradFuncObj;
  IndexFillScalarGradFunc IndexFillScalarGradFuncObj;
  NewEmptyGradFunc NewEmptyGradFuncObj;
  GridSampler2DGradGradFunc GridSampler2DGradGradFuncObj;
  DotGradFunc DotGradFuncObj;
  AdaptiveMaxPool1DGradFunc AdaptiveMaxPool1DGradFuncObj;
  HardtanhGradFunc HardtanhGradFuncObj;
  SubExtGradFunc SubExtGradFuncObj;
  NotEqualGradFunc NotEqualGradFuncObj;
  AdaptiveAvgPool1DGradFunc AdaptiveAvgPool1DGradFuncObj;
  UnstackExtViewGradFunc UnstackExtViewGradFuncObj;
  TypeAsGradFunc TypeAsGradFuncObj;
  InplaceScatterSrcGradFunc InplaceScatterSrcGradFuncObj;
  AdaptiveAvgPool3DExtGradFunc AdaptiveAvgPool3DExtGradFuncObj;
  GroupNormGradFunc GroupNormGradFuncObj;
  AsinExtGradFunc AsinExtGradFuncObj;
  SmoothL1LossGradGradFunc SmoothL1LossGradGradFuncObj;
  ViewGradFunc ViewGradFuncObj;
  EqualExtGradFunc EqualExtGradFuncObj;
  RepeatGradFunc RepeatGradFuncObj;
  BatchMatMulGradFunc BatchMatMulGradFuncObj;
  LerpGradFunc LerpGradFuncObj;
  HardtanhGradGradFunc HardtanhGradGradFuncObj;
  AdamWGradFunc AdamWGradFuncObj;
  InnerMoeTokenUnpermuteGradFunc InnerMoeTokenUnpermuteGradFuncObj;
  UpsampleBicubic2DGradGradFunc UpsampleBicubic2DGradGradFuncObj;
  ExpandDimsViewGradFunc ExpandDimsViewGradFuncObj;
  BatchNormElemtGradGradFunc BatchNormElemtGradGradFuncObj;
  GLUGradFunc GLUGradFuncObj;
  SoftplusGradExtGradFunc SoftplusGradExtGradFuncObj;
  NeScalarGradFunc NeScalarGradFuncObj;
  CumminExtGradFunc CumminExtGradFuncObj;
  TransposeViewGradFunc TransposeViewGradFuncObj;
  MeanExtGradFunc MeanExtGradFuncObj;
  ReciprocalGradFunc ReciprocalGradFuncObj;
  InplaceSubScalarGradFunc InplaceSubScalarGradFuncObj;
  InplaceNormalGradFunc InplaceNormalGradFuncObj;
  InplaceScatterValueReduceGradFunc InplaceScatterValueReduceGradFuncObj;
  ThresholdGradFunc ThresholdGradFuncObj;
  InplaceAddExtGradFunc InplaceAddExtGradFuncObj;
  FlashAttentionScoreGradFunc FlashAttentionScoreGradFuncObj;
  InplaceMulsGradFunc InplaceMulsGradFuncObj;
  DiagonalViewGradFunc DiagonalViewGradFuncObj;
  InplaceAddmmGradFunc InplaceAddmmGradFuncObj;
  MoeTokenPermuteGradFunc MoeTokenPermuteGradFuncObj;
  LeakyReLUGradExtGradFunc LeakyReLUGradExtGradFuncObj;
  RsqrtGradFunc RsqrtGradFuncObj;
  TriuGradFunc TriuGradFuncObj;
  LogSoftmaxGradFunc LogSoftmaxGradFuncObj;
  RandLikeExtGradFunc RandLikeExtGradFuncObj;
  Conv3DPaddingGradFunc Conv3DPaddingGradFuncObj;
  RoundGradFunc RoundGradFuncObj;
  GatherNdExtGradFunc GatherNdExtGradFuncObj;
  SubScalarGradFunc SubScalarGradFuncObj;
  EmptyGradFunc EmptyGradFuncObj;
  L1LossExtGradFunc L1LossExtGradFuncObj;
  GridSampler3DGradFunc GridSampler3DGradFuncObj;
  XLogYScalarOtherGradFunc XLogYScalarOtherGradFuncObj;
  DenseGradFunc DenseGradFuncObj;
  BincountExtGradFunc BincountExtGradFuncObj;
  TriangularSolveGradFunc TriangularSolveGradFuncObj;
  PReLUGradFunc PReLUGradFuncObj;
  NonZeroGradFunc NonZeroGradFuncObj;
  UpsampleNearest3DGradGradFunc UpsampleNearest3DGradGradFuncObj;
  NegGradFunc NegGradFuncObj;
  InplaceSignGradFunc InplaceSignGradFuncObj;
  RemainderScalarTensorGradFunc RemainderScalarTensorGradFuncObj;
  ToDtypeGradFunc ToDtypeGradFuncObj;
  ReverseV2GradFunc ReverseV2GradFuncObj;
  AdaptiveAvgPool2DGradExtGradFunc AdaptiveAvgPool2DGradExtGradFuncObj;
  MmGradFunc MmGradFuncObj;
  BitwiseXorTensorGradFunc BitwiseXorTensorGradFuncObj;
  LessEqualGradFunc LessEqualGradFuncObj;
  RandpermExtGradFunc RandpermExtGradFuncObj;
  SignGradFunc SignGradFuncObj;
  ConvolutionGradGradFunc ConvolutionGradGradFuncObj;
  ClampTensorGradFunc ClampTensorGradFuncObj;
  MoeTokenUnpermuteGradGradFunc MoeTokenUnpermuteGradGradFuncObj;
  ReflectionPad3DGradGradFunc ReflectionPad3DGradGradFuncObj;
  LinalgVectorNormGradFunc LinalgVectorNormGradFuncObj;
  EluExtGradFunc EluExtGradFuncObj;
  MedianDimGradFunc MedianDimGradFuncObj;
  MedianExtGradFunc MedianExtGradFuncObj;
  InplacePutGradFunc InplacePutGradFuncObj;
  CrossEntropyLossGradGradFunc CrossEntropyLossGradGradFuncObj;
  PromptFlashAttentionGradFunc PromptFlashAttentionGradFuncObj;
  DynamicQuantExtGradFunc DynamicQuantExtGradFuncObj;
  MoeInitRoutingV2GradFunc MoeInitRoutingV2GradFuncObj;
  KVCacheScatterUpdateGradFunc KVCacheScatterUpdateGradFuncObj;
  MoeInitRoutingGradFunc MoeInitRoutingGradFuncObj;
  GroupedMatmulV2GradFunc GroupedMatmulV2GradFuncObj;
  WeightQuantBatchMatmulGradFunc WeightQuantBatchMatmulGradFuncObj;
  MoeFinalizeRoutingGradFunc MoeFinalizeRoutingGradFuncObj;
  AddRmsNormQuantV2GradFunc AddRmsNormQuantV2GradFuncObj;
  GroupedMatmulGradFunc GroupedMatmulGradFuncObj;
  QuantMatmulGradFunc QuantMatmulGradFuncObj;
  GroupedMatmulV4GradFunc GroupedMatmulV4GradFuncObj;
  QuantV2GradFunc QuantV2GradFuncObj;
  MoeComputeExpertTokensGradFunc MoeComputeExpertTokensGradFuncObj;
  MoeInitRoutingQuantV2GradFunc MoeInitRoutingQuantV2GradFuncObj;
  MoeGatingTopKSoftmaxGradFunc MoeGatingTopKSoftmaxGradFuncObj;
  MatmulAllReduceAddRmsNormGradFunc MatmulAllReduceAddRmsNormGradFuncObj;
  QuantBatchMatmulGradFunc QuantBatchMatmulGradFuncObj;
  FusedInferAttentionScoreGradFunc FusedInferAttentionScoreGradFuncObj;
  DistCommIrecvGradFunc DistCommIrecvGradFuncObj;
  DistCommBatchIsendIrecvGradFunc DistCommBatchIsendIrecvGradFuncObj;
  DistCommScatterTensorGradFunc DistCommScatterTensorGradFuncObj;
  DistCommAllToAllVCGradFunc DistCommAllToAllVCGradFuncObj;
  InnerCommIrecvGradFunc InnerCommIrecvGradFuncObj;
  InnerCommReduceScatterGradFunc InnerCommReduceScatterGradFuncObj;
  DistCommAllGatherGradFunc DistCommAllGatherGradFuncObj;
  DistCommBarrierGradFunc DistCommBarrierGradFuncObj;
  InnerCommAllGatherGradFunc InnerCommAllGatherGradFuncObj;
  InnerCommIsendGradFunc InnerCommIsendGradFuncObj;
  DistCommReduceScatterTensorUnevenGradFunc DistCommReduceScatterTensorUnevenGradFuncObj;
  DistCommGatherGradFunc DistCommGatherGradFuncObj;
  DistCommAllToAllVSingleGradFunc DistCommAllToAllVSingleGradFuncObj;
  DistCommAllGatherIntoTensorUnevenGradFunc DistCommAllGatherIntoTensorUnevenGradFuncObj;
  DistCommReduceScatterGradFunc DistCommReduceScatterGradFuncObj;
  DistCommReduceGradFunc DistCommReduceGradFuncObj;
  DistCommAllReduceGradFunc DistCommAllReduceGradFuncObj;
  InnerCommAllReduceGradFunc InnerCommAllReduceGradFuncObj;
  DistCommAllToAllVGradFunc DistCommAllToAllVGradFuncObj;
  DistCommBroadcastGradFunc DistCommBroadcastGradFuncObj;
  DistCommIsendGradFunc DistCommIsendGradFuncObj;
  DistCommGatherIntoTensorGradFunc DistCommGatherIntoTensorGradFuncObj;
  InnerCommAllToAllVGradFunc InnerCommAllToAllVGradFuncObj;
  DistCommScatterGradFunc DistCommScatterGradFuncObj;
  DistCommAllGatherIntoTensorGradFunc DistCommAllGatherIntoTensorGradFuncObj;
  DistCommReduceScatterTensorGradFunc DistCommReduceScatterTensorGradFuncObj;
  AnyExtGradFunc AnyExtGradFuncObj;
  FuncMaxPool2DGradFunc FuncMaxPool2DGradFuncObj;
  GmmGradFunc GmmGradFuncObj;
  GmmV2BackwardFusionGradFunc GmmV2BackwardFusionGradFuncObj;
  AnyGradFunc AnyGradFuncObj;
  Dropout2dExtGradFunc Dropout2dExtGradFuncObj;
  FuncDropoutExtGradFunc FuncDropoutExtGradFuncObj;
  GmmBackwardFusionGradFunc GmmBackwardFusionGradFuncObj;
  PixelShuffleGradFunc PixelShuffleGradFuncObj;
  GmmV2GradFunc GmmV2GradFuncObj;
  GmmV2BackwardGradFunc GmmV2BackwardGradFuncObj;
  EinsumExtGradFunc EinsumExtGradFuncObj;
  InplaceExponentialGradFunc InplaceExponentialGradFuncObj;
  GmmBackwardGradFunc GmmBackwardGradFuncObj;
  MoeTokenUnpermuteGradFunc MoeTokenUnpermuteGradFuncObj;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_MINDSPORE_OPS_KERNEL_FUNCTIONS_AUTO_GENERATE_AUTO_GRAD_OP_REG_H_
