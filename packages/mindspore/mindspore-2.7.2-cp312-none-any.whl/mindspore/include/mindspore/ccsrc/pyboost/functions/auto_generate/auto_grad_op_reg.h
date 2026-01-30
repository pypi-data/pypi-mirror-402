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
  kUpsampleNearest1D = 0,
  kPolar = 1,
  kAddcmulExt = 2,
  kMSELossExt = 3,
  kRepeat = 4,
  kSubScalar = 5,
  kUpsampleNearest3D = 6,
  kAdaptiveAvgPool2DGradExt = 7,
  kInplaceIndexPut = 8,
  kSoftmaxBackward = 9,
  kBatchNormStats = 10,
  kAdaptiveAvgPool3DExt = 11,
  kGeluExt = 12,
  kMishExt = 13,
  kRoll = 14,
  kAcoshExt = 15,
  kUpsampleTrilinear3D = 16,
  kMultinomialExt = 17,
  kRmsNormGrad = 18,
  kInplaceFillDiagonal = 19,
  kAvgPool3DGradExt = 20,
  kNonZeroExt = 21,
  kErf = 22,
  kIncreFlashAttention = 23,
  kSign = 24,
  kPReLU = 25,
  kMaskedSelect = 26,
  kRsqrt = 27,
  kBatchNormGradExt = 28,
  kInplaceZero = 29,
  kAddLayerNormV2 = 30,
  kBatchNormReduceGrad = 31,
  kInplaceScatterAdd = 32,
  kHSigmoid = 33,
  kAddmv = 34,
  kGatherD = 35,
  kMaximum = 36,
  kNormalTensorFloat = 37,
  kApplyRotaryPosEmb = 38,
  kBitwiseXorTensor = 39,
  kXLogYScalarOther = 40,
  kRepeatInterleaveGrad = 41,
  kNansum = 42,
  kBitwiseAndScalar = 43,
  kUpsampleNearest3DGrad = 44,
  kTransposeView = 45,
  kTransposeExtView = 46,
  kAtanh = 47,
  kInnerNonZero = 48,
  kChunk = 49,
  kArgMinWithValue = 50,
  kExpandAs = 51,
  kAvgPool2DGrad = 51,
  kMatmulReduceScatter = 52,
  kXLogYScalarSelf = 53,
  kDiagonalView = 54,
  kAbs = 55,
  kAddRmsNorm = 56,
  kCrossEntropyLoss = 57,
  kInplaceFillTensor = 58,
  kAvgPool3DExt = 59,
  kUniqueConsecutive = 60,
  kStd = 61,
  kIndexAddExt = 62,
  kInplaceGroupedMatmulAdd = 63,
  kAsinhExt = 64,
  kReflectionPad2D = 65,
  kMSELossGradExt = 66,
  kSin = 67,
  kTensorScatterAdd = 68,
  kInplaceFloor = 69,
  kInplaceRemainderTensorTensor = 70,
  kAdaptiveMaxPool1D = 71,
  kAdaptiveAvgPool3DGradExt = 72,
  kBatchNormExt = 73,
  kMatMulExt = 74,
  kGroupNormGrad = 75,
  kUpsampleBilinear2DGrad = 76,
  kFloor = 77,
  kAdamW = 78,
  kLog = 79,
  kAddcdivExt = 80,
  kRepeatInterleaveTensor = 81,
  kSubExt = 82,
  kBitwiseXorScalar = 83,
  kDropoutExt = 84,
  kRandInt = 85,
  kRingAttentionUpdate = 86,
  kMaskedFill = 87,
  kView = 88,
  kReduceAny = 89,
  kMax = 90,
  kViewAs = 91,
  kZeros = 91,
  kMoeDistributeDispatch = 92,
  kExpandDims = 93,
  kSqueeze = 94,
  kProdExt = 95,
  kNanToNum = 96,
  kInplaceBernoulliScalar = 97,
  kReciprocal = 98,
  kSearchSorted = 99,
  kReluGrad = 100,
  kMedianDim = 101,
  kAdaptiveMaxPool2D = 102,
  kSelectV2 = 103,
  kTile = 104,
  kSelectExtView = 105,
  kTraceExt = 106,
  kMaxUnpool2DExt = 107,
  kReLU = 108,
  kInplaceIndexFillScalar = 109,
  kLinalgVectorNorm = 110,
  kCumminExt = 111,
  kBernoulliExt = 112,
  kInplaceLog = 113,
  kNonZero = 114,
  kMm = 115,
  kInplaceStopGradient = 116,
  kAdd = 117,
  kSlice = 118,
  kGLU = 119,
  kTriangularSolve = 120,
  kReplicationPad3DGrad = 121,
  kMishGradExt = 122,
  kMaskedFillScalar = 123,
  kRemainderTensorScalar = 124,
  kFlattenExt = 125,
  kBatchNormElemt = 125,
  kInplaceAddsExt = 126,
  kInplaceIndexCopy = 127,
  kIndexFillScalar = 128,
  kInplaceMaskedFillScalar = 129,
  kBinaryCrossEntropyWithLogitsBackward = 130,
  kSelect = 131,
  kReflectionPad1DGrad = 132,
  kNLLLoss2dGrad = 133,
  kAvgPool2D = 134,
  kLogicalXor = 135,
  kReplicationPad3D = 136,
  kCol2ImExt = 137,
  kDivMod = 138,
  kInplaceMaskedScatter = 139,
  kSplitWithSizeView = 140,
  kContiguous = 141,
  kVarMean = 142,
  kBatchNormGatherStatsWithCounts = 143,
  kConv3DExt = 144,
  kDequantSwigluQuant = 145,
  kLerp = 146,
  kConcat = 147,
  kKthvalue = 148,
  kRandnLike = 149,
  kConvolutionStr = 150,
  kPReLUGrad = 151,
  kTranspose = 152,
  kAddmm = 153,
  kNewZeros = 154,
  kInplaceDivMods = 155,
  kSumExt = 156,
  kUnstackExtView = 157,
  kTrilExt = 158,
  kAllFinite = 159,
  kSeluGrad = 160,
  kLogicalOr = 161,
  kInplaceFloorDivides = 162,
  kExp = 163,
  kFillTensor = 164,
  kGridSampler3D = 165,
  kSplitTensorView = 166,
  kTake = 167,
  kNeScalar = 168,
  kInplaceFloorDivide = 169,
  kLeakyReLUExt = 170,
  kInplaceSign = 171,
  kTypeAs = 172,
  kSiLUGrad = 173,
  kInplacePut = 174,
  kOnes = 175,
  kRandExt = 176,
  kUpsampleLinear1DGrad = 177,
  kUpsampleNearest2D = 178,
  kInplaceMaskedFillTensor = 179,
  kToOther = 180,
  kUpsampleNearest2DGrad = 181,
  kInplaceRemainderTensorScalar = 182,
  kIndexFillTensor = 183,
  kInplaceClampScalar = 184,
  kGreaterEqualScalar = 185,
  kInplaceDivs = 186,
  kPagedAttention = 187,
  kInplaceTanh = 188,
  kInnerUnique = 189,
  kKLDiv = 190,
  kReplicationPad2DGrad = 191,
  kFullLike = 192,
  kReflectionPad1D = 193,
  kInplaceSigmoid = 194,
  kNormalFloatTensor = 195,
  kInplaceElu = 196,
  kReplicationPad2D = 197,
  kOuter = 198,
  kSplitTensor = 199,
  kInplaceDivMod = 200,
  kInnerInplaceIndexPut = 201,
  kInplaceIndexFillTensor = 202,
  kEqual = 203,
  kLog10 = 204,
  kSeLUExt = 205,
  kAddScalar = 206,
  kReduceMin = 207,
  kConvolutionStrGrad = 208,
  kNorm = 209,
  kUpsampleTrilinear3DGrad = 210,
  kInplaceThreshold = 211,
  kSliceExt = 212,
  kHardtanh = 213,
  kBinaryCrossEntropyGrad = 214,
  kPowTensorScalar = 215,
  kRandn = 216,
  kTensorScatterElements = 217,
  kCumsumExt = 218,
  kNewEmpty = 219,
  kGridSampler2DGrad = 220,
  kConstantPadND = 221,
  kChunkView = 222,
  kReplicationPad1D = 223,
  kRandLikeExt = 224,
  kInplaceSiLU = 225,
  kSinh = 226,
  kEmpty = 227,
  kInplaceMuls = 228,
  kAvgPool1D = 229,
  kScatterAddExt = 230,
  kClampTensor = 231,
  kEqualExt = 232,
  kInplaceClampTensor = 233,
  kMaxPoolWithIndices = 234,
  kInplaceScatterValueReduce = 235,
  kEmbeddingDenseBackward = 236,
  kMedianExt = 237,
  kBaddbmm = 238,
  kRandIntLike = 239,
  kConv1DExt = 240,
  kInplaceReLU = 241,
  kRandpermExt = 242,
  kConvolutionGrad = 243,
  kCosh = 244,
  kConv2DExt = 245,
  kNarrowView = 246,
  kLogSigmoidGrad = 247,
  kInplaceScatterSrcReduce = 248,
  kDropoutGradExt = 249,
  kConvTranspose2D = 250,
  kAsStrided = 251,
  kGreaterEqual = 252,
  kAtanExt = 253,
  kBinaryCrossEntropy = 254,
  kDot = 255,
  kCustomExt = 256,
  kHistcExt = 257,
  kRound = 258,
  kConv2DPadding = 259,
  kGcd = 260,
  kFlashAttentionScoreGrad = 261,
  kSwigluGrad = 262,
  kSoftMarginLossGrad = 263,
  kInplaceUniform = 264,
  kToDtype = 265,
  kArange = 266,
  kInnerIndex = 267,
  kMoeTokenPermute = 268,
  kCross = 269,
  kHSigmoidGrad = 270,
  kDivMods = 271,
  kLeakyReLUGradExt = 272,
  kMla = 273,
  kReflectionPad3DGrad = 274,
  kInplaceNormal = 275,
  kSigmoid = 276,
  kEluExt = 277,
  kIsNegInf = 278,
  kInplaceFillScalar = 279,
  kToDevice = 280,
  kSqrt = 281,
  kFmodScalar = 282,
  kHShrinkGrad = 283,
  kTanh = 284,
  kBitwiseOrTensor = 285,
  kFloorDivScalar = 286,
  kGenerator = 287,
  kArgMinExt = 288,
  kStackExt = 289,
  kNLLLoss2d = 290,
  kGroupNorm = 291,
  kLogSoftmaxGrad = 292,
  kLessEqual = 293,
  kCos = 294,
  kGatherNdExt = 295,
  kMinimum = 296,
  kIsClose = 297,
  kOneHotExt = 298,
  kMatrixInverseExt = 299,
  kArgSort = 300,
  kFrac = 301,
  kAllGatherMatmul = 302,
  kInplaceExp = 303,
  kRepeatInterleaveInt = 304,
  kPromptFlashAttention = 305,
  kLogSoftmax = 306,
  kGridSampler2D = 307,
  kConv3DPadding = 308,
  kUpsampleBicubic2DGrad = 309,
  kInnerMoeTokenUnpermute = 310,
  kClone = 311,
  kThresholdGrad = 312,
  kSplitWithSize = 313,
  kReduceAll = 314,
  kDiv = 315,
  kSwiglu = 316,
  kAtan2Ext = 317,
  kSigmoidGrad = 318,
  kInplaceBernoulliTensor = 319,
  kInplaceAddmm = 320,
  kRealView = 321,
  kSoftplusGradExt = 322,
  kArgMaxWithValue = 323,
  kSquare = 324,
  kAddExt = 325,
  kGluGrad = 326,
  kImagView = 327,
  kBCEWithLogitsLoss = 328,
  kSoftmax = 329,
  kScatterValue = 330,
  kCellBackwardHook = 331,
  kEye = 332,
  kIm2ColExt = 333,
  kHSwishGrad = 334,
  kHShrink = 335,
  kXlogy = 336,
  kSmoothL1Loss = 337,
  kSilentCheckV2 = 338,
  kLogicalAnd = 339,
  kNarrow = 340,
  kMaxPoolGradWithMask = 341,
  kStdMean = 342,
  kBitwiseNot = 343,
  kMeshgrid = 344,
  kCeil = 344,
  kFlashAttentionScore = 345,
  kLinalgQr = 346,
  kThreshold = 347,
  kLogAddExp2 = 348,
  kInplaceScatterValue = 349,
  kIsFinite = 350,
  kMoeDistributeCombine = 351,
  kReflectionPad2DGrad = 352,
  kLog2 = 353,
  kNewOnes = 354,
  kHardtanhGrad = 355,
  kInplaceScatterSrc = 356,
  kInplaceMul = 357,
  kLogSoftmaxExt = 358,
  kTrunc = 359,
  kGridSampler3DGrad = 360,
  kReshapeAndCache = 361,
  kReshape = 362,
  kIndex = 363,
  kCol2ImGrad = 364,
  kBroadcastToView = 365,
  kL1LossExt = 366,
  kEluGradExt = 367,
  kLess = 368,
  kLayerNormExt = 369,
  kOnesLikeExt = 370,
  kTriu = 371,
  kMaskedScatter = 372,
  kMinDim = 373,
  kUpsampleNearest1DGrad = 374,
  kInplaceErfinv = 375,
  kSiLU = 376,
  kBroadcastTo = 377,
  kMaxPoolGradWithIndices = 378,
  kLogAddExp = 379,
  kDense = 380,
  kAdaptiveAvgPool2DExt = 381,
  kAsinExt = 382,
  kBincountExt = 383,
  kSoftplusExt = 384,
  kMoeTokenPermuteGrad = 385,
  kReflectionPad3D = 386,
  kArgMaxExt = 387,
  kTan = 388,
  kConvolution = 389,
  kInplaceMatmulAdd = 390,
  kGeLUGrad = 391,
  kMuls = 392,
  kEmbedding = 393,
  kInplaceRandom = 394,
  kFloorDiv = 395,
  kMin = 396,
  kMaxDim = 397,
  kSliceExtView = 398,
  kSoftShrinkGrad = 399,
  kFFNExt = 400,
  kLogSigmoid = 401,
  kMaxPoolWithMask = 402,
  kPowScalarTensor = 403,
  kRemainderTensorTensor = 404,
  kBitwiseOrScalar = 405,
  kMultiScaleDeformableAttnGrad = 406,
  kRotaryPositionEmbeddingGrad = 407,
  kInplaceHardtanh = 408,
  kDivs = 409,
  kSmoothL1LossGrad = 410,
  kExpandDimsView = 411,
  kKLDivGrad = 412,
  kRemainderScalarTensor = 413,
  kNLLLossGrad = 414,
  kSplit = 415,
  kMaskedSelectGrad = 416,
  kExp2 = 417,
  kDropoutDoMaskExt = 418,
  kMatMul = 419,
  kScatter = 420,
  kUpsampleLinear1D = 421,
  kNeg = 422,
  kZerosLikeExt = 423,
  kLogicalNot = 424,
  kReduceMax = 425,
  kHSwish = 426,
  kSilentCheckV3 = 427,
  kGreater = 428,
  kReplicationPad1DGrad = 429,
  kIndexSelect = 430,
  kTopkExt = 431,
  kMoeTokenUnpermuteGrad = 432,
  kRmsNorm = 433,
  kDropoutGenMaskExt = 434,
  kPow = 435,
  kErfc = 436,
  kInplaceCopy = 437,
  kElu = 438,
  kCrossEntropyLossGrad = 439,
  kExpm1 = 440,
  kFillScalar = 441,
  kBatchNormElemtGrad = 442,
  kIsInf = 443,
  kInplaceSubScalar = 444,
  kDiagExt = 445,
  kGeLU = 446,
  kNotEqual = 447,
  kUniformExt = 448,
  kEmptyLike = 449,
  kAdaptiveAvgPool1D = 450,
  kAddbmm = 451,
  kSortExt = 452,
  kBatchMatMul = 453,
  kLerpScalar = 454,
  kNLLLoss = 455,
  kConv1DPadding = 456,
  kBitwiseAndTensor = 457,
  kLayerNormGradExt = 458,
  kCopy = 459,
  kRotaryPositionEmbedding = 460,
  kErfinv = 461,
  kTanhGrad = 462,
  kAcosExt = 463,
  kSpeedFusionAttention = 464,
  kSoftShrink = 465,
  kL1LossBackwardExt = 466,
  kMeanExt = 467,
  kNormalTensorTensor = 468,
  kBatchMatMulExt = 469,
  kGeluGradExt = 470,
  kTExt = 471,
  kInplaceAddExt = 471,
  kUnique2 = 472,
  kCountNonZero = 473,
  kSoftMarginLoss = 474,
  kVar = 475,
  kInplaceDiv = 476,
  kFmodTensor = 477,
  kAddLayerNormGrad = 478,
  kNewFull = 479,
  kUpsampleBilinear2D = 480,
  kCummax = 481,
  kSpeedFusionAttentionGrad = 482,
  kClampScalar = 483,
  kCast = 484,
  kUniqueDim = 485,
  kIdentity = 486,
  kSinc = 487,
  kReverseV2 = 488,
  kMultiScaleDeformableAttn = 489,
  kMv = 490,
  kUpsampleBicubic2D = 491,
  kLog1p = 492,
  kMul = 493,
  kNormalFloatFloat = 494,
  kInplaceSubExt = 495,
  kGatherDGradV2 = 496,
  kLinSpaceExt = 497,
  kInplaceIndexAddExt = 498,
  kSub = 499,
  kLogSumExp = 500,
  kQuantV2 = 501,
  kDynamicQuantExt = 502,
  kGroupedMatmulV2 = 503,
  kMoeInitRoutingQuantV2 = 504,
  kGroupedMatmul = 505,
  kGroupedMatmulV4 = 506,
  kWeightQuantBatchMatmul = 507,
  kQuantMatmul = 508,
  kMoeInitRoutingV2 = 509,
  kMoeGatingTopKSoftmax = 510,
  kAddRmsNormQuantV2 = 511,
  kKVCacheScatterUpdate = 512,
  kMoeComputeExpertTokens = 513,
  kMoeInitRouting = 514,
  kQuantBatchMatmul = 515,
  kFusedInferAttentionScore = 516,
  kMatmulAllReduceAddRmsNorm = 517,
  kMoeFinalizeRouting = 518,
  kInnerCommIsend = 519,
  kDistCommAllGatherIntoTensorUneven = 520,
  kDistCommReduce = 521,
  kDistCommBroadcast = 522,
  kInnerCommReduceScatter = 523,
  kDistCommReduceScatterTensor = 524,
  kDistCommAllToAllVSingle = 525,
  kDistCommIsend = 526,
  kInnerCommAllGather = 527,
  kDistCommBarrier = 528,
  kDistCommGather = 529,
  kInnerCommIrecv = 530,
  kDistCommReduceScatterTensorUneven = 531,
  kDistCommScatterTensor = 532,
  kDistCommAllToAllV = 533,
  kDistCommReduceScatter = 534,
  kDistCommAllToAllVC = 535,
  kDistCommBatchIsendIrecv = 536,
  kDistCommIrecv = 537,
  kInnerCommAllToAllV = 538,
  kDistCommGatherIntoTensor = 539,
  kDistCommAllGatherIntoTensor = 540,
  kDistCommScatter = 541,
  kInnerCommAllReduce = 542,
  kDistCommAllReduce = 543,
  kDistCommAllGather = 544,
  kGmm = 545,
  kGmmBackwardFusion = 546,
  kFuncDropoutExt = 547,
  kMoeTokenUnpermute = 548,
  kAnyExt = 549,
  kEinsumExt = 550,
  kGmmV2BackwardFusion = 551,
  kGmmV2 = 552,
  kGmmBackward = 553,
  kAny = 554,
  kGmmV2Backward = 555,
  kFuncMaxPool2D = 556,
  kPixelShuffle = 557,
  kDropout2dExt = 558,
  kInplaceExponential = 559,
};

using UpsampleNearest1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using PolarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AddcmulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MSELossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using RepeatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using UpsampleNearest3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using AdaptiveAvgPool2DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using SoftmaxBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using BatchNormStatsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using AdaptiveAvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using GeluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MishExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RollGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using AcoshExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleTrilinear3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using MultinomialExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RmsNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFillDiagonalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using AvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NonZeroExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using IncreFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using SignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using PReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RsqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddLayerNormV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchNormReduceGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using HSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddmvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using GatherDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using MaximumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalTensorFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ApplyRotaryPosEmbGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using BitwiseXorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using XLogYScalarOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RepeatInterleaveGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using NansumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using BitwiseAndScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using UpsampleNearest3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using TransposeViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using TransposeExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using AtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InnerNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ChunkGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using ArgMinWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using AvgPool2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using MatmulReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using XLogYScalarSelfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using DiagonalViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using AbsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using CrossEntropyLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AvgPool3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UniqueConsecutiveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using StdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using IndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceGroupedMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AsinhExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReflectionPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MSELossGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TensorScatterAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceRemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AdaptiveMaxPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using AdaptiveAvgPool3DGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using MatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GroupNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using UpsampleBilinear2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using FloorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AdamWGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using LogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddcdivExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RepeatInterleaveTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using SubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BitwiseXorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using DropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RandIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RingAttentionUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using MaskedFillGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using ReduceAnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using MaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using MoeDistributeDispatchGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ExpandDimsGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using SqueezeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using ProdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NanToNumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &)>;
using InplaceBernoulliScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReciprocalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SearchSortedGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using ReluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MedianDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using AdaptiveMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SelectV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using TileGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using SelectExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using TraceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaxUnpool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceIndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using LinalgVectorNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using CumminExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using BernoulliExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceLogGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceStopGradientGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SliceGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &)>;
using GLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using TriangularSolveGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MishGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BatchNormElemtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using InplaceAddsExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceIndexCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IndexFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceMaskedFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using BinaryCrossEntropyWithLogitsBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using SelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReflectionPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using NLLLoss2dGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using AvgPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LogicalXorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReplicationPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using Col2ImExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using DivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceMaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitWithSizeViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using ContiguousGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using VarMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchNormGatherStatsWithCountsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using Conv3DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using DequantSwigluQuantGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using LerpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ConcatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using KthvalueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using RandnLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ConvolutionStrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using PReLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using TransposeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using AddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using NewZerosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceDivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using SumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UnstackExtViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using TrilExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using AllFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using SeluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogicalOrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFloorDividesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using ExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using GridSampler3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SplitTensorViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using TakeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NeScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceFloorDivideGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LeakyReLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceSignGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TypeAsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SiLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplacePutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using OnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using RandExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UpsampleLinear1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using UpsampleNearest2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceMaskedFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ToOtherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using UpsampleNearest2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceRemainderTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using IndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using GreaterEqualScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using InplaceDivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using PagedAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceTanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InnerUniqueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using KLDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using ReplicationPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using FullLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using ReflectionPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalFloatTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceEluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using ReplicationPad2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using OuterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SplitTensorGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using InplaceDivModGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InnerInplaceIndexPutGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using InplaceIndexFillTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Log10GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SeLUExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using ReduceMinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using ConvolutionStrGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using NormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UpsampleTrilinear3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using InplaceThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using SliceExtGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using HardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using BinaryCrossEntropyGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using PowTensorScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using RandnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using TensorScatterElementsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using CumsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NewEmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using GridSampler2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using ConstantPadNDGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &)>;
using ChunkViewGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using ReplicationPad1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using RandLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceSiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SinhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using EmptyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using InplaceMulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using AvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ScatterAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using EqualExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceClampTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using MaxPoolWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceScatterValueReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using EmbeddingDenseBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using MedianExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BaddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using RandIntLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using Conv1DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using InplaceReLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RandpermExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ConvolutionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using CoshGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using Conv2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using NarrowViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using LogSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterSrcReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using DropoutGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using ConvTranspose2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using AsStridedGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const std::vector<int64_t> &, const int64_t &)>;
using GreaterEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AtanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BinaryCrossEntropyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using DotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CustomExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using HistcExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using RoundGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using Conv2DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using GcdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FlashAttentionScoreGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using SwigluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SoftMarginLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceUniformGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ToDtypeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ArangeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InnerIndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MoeTokenPermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using CrossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using HSigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using DivModsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LeakyReLUGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::BoolImmPtr &)>;
using MlaGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using InplaceNormalGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using EluExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using IsNegInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceFillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using ToDeviceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using SqrtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FmodScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using HShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using TanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseOrTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FloorDivScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using GeneratorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &)>;
using ArgMinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using StackExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using NLLLoss2dGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GroupNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using LogSoftmaxGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using LessEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using CosGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GatherNdExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MinimumGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IsCloseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using OneHotExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MatrixInverseExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ArgSortGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using FracGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AllGatherMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RepeatInterleaveIntGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using PromptFlashAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using LogSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GridSampler2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using Conv3DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using UpsampleBicubic2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using InnerMoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using CloneGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ThresholdGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SplitWithSizeGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &, const int64_t &)>;
using ReduceAllGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using DivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SwigluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using Atan2ExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SigmoidGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceBernoulliTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceAddmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using RealViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SoftplusGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using ArgMaxWithValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SquareGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using AddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using GluGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ImagViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BCEWithLogitsLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using SoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &)>;
using CellBackwardHookGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &)>;
using EyeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using Im2ColExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using HSwishGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using HShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using XlogyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using SmoothL1LossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using SilentCheckV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using LogicalAndGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NarrowGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &)>;
using MaxPoolGradWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using StdMeanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using BitwiseNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using CeilGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FlashAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using LinalgQrGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ThresholdGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using LogAddExp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceScatterValueGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using IsFiniteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MoeDistributeCombineGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::StringImmPtr> &, const std::optional<mindspore::StringImmPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ReflectionPad2DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using Log2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NewOnesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using HardtanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using InplaceScatterSrcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogSoftmaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &)>;
using TruncGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GridSampler3DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &)>;
using ReshapeAndCacheGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using ReshapeGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using IndexGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using Col2ImGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using BroadcastToViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using L1LossExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using EluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using LessGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LayerNormExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &)>;
using OnesLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using TriuGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MaskedScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MinDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using UpsampleNearest1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using InplaceErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SiLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BroadcastToGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::vector<int64_t> &)>;
using MaxPoolGradWithIndicesGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using LogAddExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using DenseGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using AdaptiveAvgPool2DExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using AsinExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using BincountExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using SoftplusExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using MoeTokenPermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using ReflectionPad3DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using ArgMaxExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using TanGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ConvolutionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using InplaceMatmulAddGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GeLUGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MulsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using EmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::FP32ImmPtr> &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceRandomGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FloorDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MinGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaxDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using SliceExtViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &, const int64_t &, const int64_t &)>;
using SoftShrinkGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using FFNExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using LogSigmoidGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MaxPoolWithMaskGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using PowScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using RemainderTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BitwiseOrScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using MultiScaleDeformableAttnGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using RotaryPositionEmbeddingGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using InplaceHardtanhGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using DivsGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SmoothL1LossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using ExpandDimsViewGradFunc = std::function<void(const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const int64_t &)>;
using KLDivGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using RemainderScalarTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &)>;
using NLLLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using SplitGradFunc = std::function<void(const std::vector<mindspore::tensor::TensorPtr> &, const mindspore::tensor::TensorPtr &, const int64_t &, const int64_t &)>;
using MaskedSelectGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using Exp2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using DropoutDoMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using MatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using ScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UpsampleLinear1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using NegGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ZerosLikeExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using LogicalNotGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReduceMaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using HSwishGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SilentCheckV3GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GreaterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ReplicationPad1DGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using IndexSelectGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &)>;
using TopkExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeTokenUnpermuteGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using RmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using DropoutGenMaskExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::FP32ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using PowGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using ErfcGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceCopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &)>;
using EluGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using CrossEntropyLossGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &)>;
using Expm1GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using FillScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using BatchNormElemtGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using IsInfGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSubScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using DiagExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using GeLUGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using NotEqualGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UniformExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using EmptyLikeGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const mindspore::BoolImmPtr &)>;
using AdaptiveAvgPool1DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using AddbmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &)>;
using SortExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using BatchMatMulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using LerpScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using NLLLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using Conv1DPaddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using BitwiseAndTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LayerNormGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using CopyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using RotaryPositionEmbeddingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using ErfinvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using TanhGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AcosExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SpeedFusionAttentionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using SoftShrinkGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using L1LossBackwardExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MeanExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using NormalTensorTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using BatchMatMulExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using GeluGradExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using InplaceAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using Unique2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using CountNonZeroGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using SoftMarginLossGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using VarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using InplaceDivGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using FmodTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using AddLayerNormGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NewFullGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ScalarPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using UpsampleBilinear2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using CummaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using SpeedFusionAttentionGradGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::FP32ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using ClampScalarGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ScalarPtr> &, const std::optional<mindspore::ScalarPtr> &)>;
using CastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using UniqueDimGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using IdentityGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using SincGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using ReverseV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &)>;
using MultiScaleDeformableAttnGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using UpsampleBicubic2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::BoolImmPtr &)>;
using Log1pGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using MulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using NormalFloatFloatGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceSubExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using GatherDGradV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LinSpaceExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ScalarPtr &, const mindspore::ScalarPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using InplaceIndexAddExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &)>;
using SubGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using LogSumExpGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &)>;
using QuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DynamicQuantExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using GroupedMatmulV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using GroupedMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using GroupedMatmulV4GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const std::optional<mindspore::Int64ImmPtr> &)>;
using WeightQuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using QuantMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::Int64ImmPtr> &, const std::optional<mindspore::ValueTuplePtr> &)>;
using MoeInitRoutingV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using MoeGatingTopKSoftmaxGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using AddRmsNormQuantV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &)>;
using KVCacheScatterUpdateGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeComputeExpertTokensGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using MoeInitRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using QuantBatchMatmulGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &)>;
using FusedInferAttentionScoreGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::FP32ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MatmulAllReduceAddRmsNormGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using MoeFinalizeRoutingGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const std::optional<mindspore::tensor::TensorPtr> &)>;
using InnerCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommAllGatherIntoTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBroadcastGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommReduceScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVSingleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommIsendGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using InnerCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommBarrierGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &)>;
using DistCommGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommReduceScatterTensorUnevenGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommScatterTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &)>;
using DistCommReduceScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllToAllVCGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using DistCommBatchIsendIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &)>;
using DistCommIrecvGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllToAllVGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using DistCommGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllGatherIntoTensorGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommScatterGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using InnerCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllReduceGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::StringImmPtr &, const mindspore::StringImmPtr &)>;
using DistCommAllGatherGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::StringImmPtr &)>;
using GmmGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GmmBackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using FuncDropoutExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using MoeTokenUnpermuteGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::BoolImmPtr &, const std::optional<mindspore::ValueTuplePtr> &)>;
using AnyExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &, const mindspore::BoolImmPtr &)>;
using EinsumExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::StringImmPtr &, const mindspore::ValueTuplePtr &)>;
using GmmV2BackwardFusionGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using GmmV2GradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &, const mindspore::Int64ImmPtr &)>;
using GmmBackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::Int64ImmPtr &)>;
using AnyGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &)>;
using GmmV2BackwardGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::tensor::TensorPtr> &, const mindspore::Int64ImmPtr &)>;
using FuncMaxPool2DGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ValueTuplePtr &, const std::optional<mindspore::ValueTuplePtr> &, const mindspore::ValueTuplePtr &, const mindspore::ValueTuplePtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &)>;
using PixelShuffleGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::Int64ImmPtr &)>;
using Dropout2dExtGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::FP32ImmPtr &, const mindspore::BoolImmPtr &, const mindspore::BoolImmPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;
using InplaceExponentialGradFunc = std::function<void(const kernel::pyboost::OpPtr &, const mindspore::tensor::TensorPtr &, const mindspore::ScalarPtr &, const mindspore::tensor::TensorPtr &, const mindspore::tensor::TensorPtr &)>;

struct OpsAutoGradRegisters {
  UpsampleNearest1DGradFunc UpsampleNearest1DGradFuncObj;
  PolarGradFunc PolarGradFuncObj;
  AddcmulExtGradFunc AddcmulExtGradFuncObj;
  MSELossExtGradFunc MSELossExtGradFuncObj;
  RepeatGradFunc RepeatGradFuncObj;
  SubScalarGradFunc SubScalarGradFuncObj;
  UpsampleNearest3DGradFunc UpsampleNearest3DGradFuncObj;
  AdaptiveAvgPool2DGradExtGradFunc AdaptiveAvgPool2DGradExtGradFuncObj;
  InplaceIndexPutGradFunc InplaceIndexPutGradFuncObj;
  SoftmaxBackwardGradFunc SoftmaxBackwardGradFuncObj;
  BatchNormStatsGradFunc BatchNormStatsGradFuncObj;
  AdaptiveAvgPool3DExtGradFunc AdaptiveAvgPool3DExtGradFuncObj;
  GeluExtGradFunc GeluExtGradFuncObj;
  MishExtGradFunc MishExtGradFuncObj;
  RollGradFunc RollGradFuncObj;
  AcoshExtGradFunc AcoshExtGradFuncObj;
  UpsampleTrilinear3DGradFunc UpsampleTrilinear3DGradFuncObj;
  MultinomialExtGradFunc MultinomialExtGradFuncObj;
  RmsNormGradGradFunc RmsNormGradGradFuncObj;
  InplaceFillDiagonalGradFunc InplaceFillDiagonalGradFuncObj;
  AvgPool3DGradExtGradFunc AvgPool3DGradExtGradFuncObj;
  NonZeroExtGradFunc NonZeroExtGradFuncObj;
  ErfGradFunc ErfGradFuncObj;
  IncreFlashAttentionGradFunc IncreFlashAttentionGradFuncObj;
  SignGradFunc SignGradFuncObj;
  PReLUGradFunc PReLUGradFuncObj;
  MaskedSelectGradFunc MaskedSelectGradFuncObj;
  RsqrtGradFunc RsqrtGradFuncObj;
  BatchNormGradExtGradFunc BatchNormGradExtGradFuncObj;
  InplaceZeroGradFunc InplaceZeroGradFuncObj;
  AddLayerNormV2GradFunc AddLayerNormV2GradFuncObj;
  BatchNormReduceGradGradFunc BatchNormReduceGradGradFuncObj;
  InplaceScatterAddGradFunc InplaceScatterAddGradFuncObj;
  HSigmoidGradFunc HSigmoidGradFuncObj;
  AddmvGradFunc AddmvGradFuncObj;
  GatherDGradFunc GatherDGradFuncObj;
  MaximumGradFunc MaximumGradFuncObj;
  NormalTensorFloatGradFunc NormalTensorFloatGradFuncObj;
  ApplyRotaryPosEmbGradFunc ApplyRotaryPosEmbGradFuncObj;
  BitwiseXorTensorGradFunc BitwiseXorTensorGradFuncObj;
  XLogYScalarOtherGradFunc XLogYScalarOtherGradFuncObj;
  RepeatInterleaveGradGradFunc RepeatInterleaveGradGradFuncObj;
  NansumGradFunc NansumGradFuncObj;
  BitwiseAndScalarGradFunc BitwiseAndScalarGradFuncObj;
  UpsampleNearest3DGradGradFunc UpsampleNearest3DGradGradFuncObj;
  TransposeViewGradFunc TransposeViewGradFuncObj;
  TransposeExtViewGradFunc TransposeExtViewGradFuncObj;
  AtanhGradFunc AtanhGradFuncObj;
  InnerNonZeroGradFunc InnerNonZeroGradFuncObj;
  ChunkGradFunc ChunkGradFuncObj;
  ArgMinWithValueGradFunc ArgMinWithValueGradFuncObj;
  AvgPool2DGradGradFunc AvgPool2DGradGradFuncObj;
  MatmulReduceScatterGradFunc MatmulReduceScatterGradFuncObj;
  XLogYScalarSelfGradFunc XLogYScalarSelfGradFuncObj;
  DiagonalViewGradFunc DiagonalViewGradFuncObj;
  AbsGradFunc AbsGradFuncObj;
  AddRmsNormGradFunc AddRmsNormGradFuncObj;
  CrossEntropyLossGradFunc CrossEntropyLossGradFuncObj;
  InplaceFillTensorGradFunc InplaceFillTensorGradFuncObj;
  AvgPool3DExtGradFunc AvgPool3DExtGradFuncObj;
  UniqueConsecutiveGradFunc UniqueConsecutiveGradFuncObj;
  StdGradFunc StdGradFuncObj;
  IndexAddExtGradFunc IndexAddExtGradFuncObj;
  InplaceGroupedMatmulAddGradFunc InplaceGroupedMatmulAddGradFuncObj;
  AsinhExtGradFunc AsinhExtGradFuncObj;
  ReflectionPad2DGradFunc ReflectionPad2DGradFuncObj;
  MSELossGradExtGradFunc MSELossGradExtGradFuncObj;
  SinGradFunc SinGradFuncObj;
  TensorScatterAddGradFunc TensorScatterAddGradFuncObj;
  InplaceFloorGradFunc InplaceFloorGradFuncObj;
  InplaceRemainderTensorTensorGradFunc InplaceRemainderTensorTensorGradFuncObj;
  AdaptiveMaxPool1DGradFunc AdaptiveMaxPool1DGradFuncObj;
  AdaptiveAvgPool3DGradExtGradFunc AdaptiveAvgPool3DGradExtGradFuncObj;
  BatchNormExtGradFunc BatchNormExtGradFuncObj;
  MatMulExtGradFunc MatMulExtGradFuncObj;
  GroupNormGradGradFunc GroupNormGradGradFuncObj;
  UpsampleBilinear2DGradGradFunc UpsampleBilinear2DGradGradFuncObj;
  FloorGradFunc FloorGradFuncObj;
  AdamWGradFunc AdamWGradFuncObj;
  LogGradFunc LogGradFuncObj;
  AddcdivExtGradFunc AddcdivExtGradFuncObj;
  RepeatInterleaveTensorGradFunc RepeatInterleaveTensorGradFuncObj;
  SubExtGradFunc SubExtGradFuncObj;
  BitwiseXorScalarGradFunc BitwiseXorScalarGradFuncObj;
  DropoutExtGradFunc DropoutExtGradFuncObj;
  RandIntGradFunc RandIntGradFuncObj;
  RingAttentionUpdateGradFunc RingAttentionUpdateGradFuncObj;
  MaskedFillGradFunc MaskedFillGradFuncObj;
  ViewGradFunc ViewGradFuncObj;
  ReduceAnyGradFunc ReduceAnyGradFuncObj;
  MaxGradFunc MaxGradFuncObj;
  ZerosGradFunc ZerosGradFuncObj;
  MoeDistributeDispatchGradFunc MoeDistributeDispatchGradFuncObj;
  ExpandDimsGradFunc ExpandDimsGradFuncObj;
  SqueezeGradFunc SqueezeGradFuncObj;
  ProdExtGradFunc ProdExtGradFuncObj;
  NanToNumGradFunc NanToNumGradFuncObj;
  InplaceBernoulliScalarGradFunc InplaceBernoulliScalarGradFuncObj;
  ReciprocalGradFunc ReciprocalGradFuncObj;
  SearchSortedGradFunc SearchSortedGradFuncObj;
  ReluGradGradFunc ReluGradGradFuncObj;
  MedianDimGradFunc MedianDimGradFuncObj;
  AdaptiveMaxPool2DGradFunc AdaptiveMaxPool2DGradFuncObj;
  SelectV2GradFunc SelectV2GradFuncObj;
  TileGradFunc TileGradFuncObj;
  SelectExtViewGradFunc SelectExtViewGradFuncObj;
  TraceExtGradFunc TraceExtGradFuncObj;
  MaxUnpool2DExtGradFunc MaxUnpool2DExtGradFuncObj;
  ReLUGradFunc ReLUGradFuncObj;
  InplaceIndexFillScalarGradFunc InplaceIndexFillScalarGradFuncObj;
  LinalgVectorNormGradFunc LinalgVectorNormGradFuncObj;
  CumminExtGradFunc CumminExtGradFuncObj;
  BernoulliExtGradFunc BernoulliExtGradFuncObj;
  InplaceLogGradFunc InplaceLogGradFuncObj;
  NonZeroGradFunc NonZeroGradFuncObj;
  MmGradFunc MmGradFuncObj;
  InplaceStopGradientGradFunc InplaceStopGradientGradFuncObj;
  AddGradFunc AddGradFuncObj;
  SliceGradFunc SliceGradFuncObj;
  GLUGradFunc GLUGradFuncObj;
  TriangularSolveGradFunc TriangularSolveGradFuncObj;
  ReplicationPad3DGradGradFunc ReplicationPad3DGradGradFuncObj;
  MishGradExtGradFunc MishGradExtGradFuncObj;
  MaskedFillScalarGradFunc MaskedFillScalarGradFuncObj;
  RemainderTensorScalarGradFunc RemainderTensorScalarGradFuncObj;
  BatchNormElemtGradFunc BatchNormElemtGradFuncObj;
  InplaceAddsExtGradFunc InplaceAddsExtGradFuncObj;
  InplaceIndexCopyGradFunc InplaceIndexCopyGradFuncObj;
  IndexFillScalarGradFunc IndexFillScalarGradFuncObj;
  InplaceMaskedFillScalarGradFunc InplaceMaskedFillScalarGradFuncObj;
  BinaryCrossEntropyWithLogitsBackwardGradFunc BinaryCrossEntropyWithLogitsBackwardGradFuncObj;
  SelectGradFunc SelectGradFuncObj;
  ReflectionPad1DGradGradFunc ReflectionPad1DGradGradFuncObj;
  NLLLoss2dGradGradFunc NLLLoss2dGradGradFuncObj;
  AvgPool2DGradFunc AvgPool2DGradFuncObj;
  LogicalXorGradFunc LogicalXorGradFuncObj;
  ReplicationPad3DGradFunc ReplicationPad3DGradFuncObj;
  Col2ImExtGradFunc Col2ImExtGradFuncObj;
  DivModGradFunc DivModGradFuncObj;
  InplaceMaskedScatterGradFunc InplaceMaskedScatterGradFuncObj;
  SplitWithSizeViewGradFunc SplitWithSizeViewGradFuncObj;
  ContiguousGradFunc ContiguousGradFuncObj;
  VarMeanGradFunc VarMeanGradFuncObj;
  BatchNormGatherStatsWithCountsGradFunc BatchNormGatherStatsWithCountsGradFuncObj;
  Conv3DExtGradFunc Conv3DExtGradFuncObj;
  DequantSwigluQuantGradFunc DequantSwigluQuantGradFuncObj;
  LerpGradFunc LerpGradFuncObj;
  ConcatGradFunc ConcatGradFuncObj;
  KthvalueGradFunc KthvalueGradFuncObj;
  RandnLikeGradFunc RandnLikeGradFuncObj;
  ConvolutionStrGradFunc ConvolutionStrGradFuncObj;
  PReLUGradGradFunc PReLUGradGradFuncObj;
  TransposeGradFunc TransposeGradFuncObj;
  AddmmGradFunc AddmmGradFuncObj;
  NewZerosGradFunc NewZerosGradFuncObj;
  InplaceDivModsGradFunc InplaceDivModsGradFuncObj;
  SumExtGradFunc SumExtGradFuncObj;
  UnstackExtViewGradFunc UnstackExtViewGradFuncObj;
  TrilExtGradFunc TrilExtGradFuncObj;
  AllFiniteGradFunc AllFiniteGradFuncObj;
  SeluGradGradFunc SeluGradGradFuncObj;
  LogicalOrGradFunc LogicalOrGradFuncObj;
  InplaceFloorDividesGradFunc InplaceFloorDividesGradFuncObj;
  ExpGradFunc ExpGradFuncObj;
  FillTensorGradFunc FillTensorGradFuncObj;
  GridSampler3DGradFunc GridSampler3DGradFuncObj;
  SplitTensorViewGradFunc SplitTensorViewGradFuncObj;
  TakeGradFunc TakeGradFuncObj;
  NeScalarGradFunc NeScalarGradFuncObj;
  InplaceFloorDivideGradFunc InplaceFloorDivideGradFuncObj;
  LeakyReLUExtGradFunc LeakyReLUExtGradFuncObj;
  InplaceSignGradFunc InplaceSignGradFuncObj;
  TypeAsGradFunc TypeAsGradFuncObj;
  SiLUGradGradFunc SiLUGradGradFuncObj;
  InplacePutGradFunc InplacePutGradFuncObj;
  OnesGradFunc OnesGradFuncObj;
  RandExtGradFunc RandExtGradFuncObj;
  UpsampleLinear1DGradGradFunc UpsampleLinear1DGradGradFuncObj;
  UpsampleNearest2DGradFunc UpsampleNearest2DGradFuncObj;
  InplaceMaskedFillTensorGradFunc InplaceMaskedFillTensorGradFuncObj;
  ToOtherGradFunc ToOtherGradFuncObj;
  UpsampleNearest2DGradGradFunc UpsampleNearest2DGradGradFuncObj;
  InplaceRemainderTensorScalarGradFunc InplaceRemainderTensorScalarGradFuncObj;
  IndexFillTensorGradFunc IndexFillTensorGradFuncObj;
  InplaceClampScalarGradFunc InplaceClampScalarGradFuncObj;
  GreaterEqualScalarGradFunc GreaterEqualScalarGradFuncObj;
  InplaceDivsGradFunc InplaceDivsGradFuncObj;
  PagedAttentionGradFunc PagedAttentionGradFuncObj;
  InplaceTanhGradFunc InplaceTanhGradFuncObj;
  InnerUniqueGradFunc InnerUniqueGradFuncObj;
  KLDivGradFunc KLDivGradFuncObj;
  ReplicationPad2DGradGradFunc ReplicationPad2DGradGradFuncObj;
  FullLikeGradFunc FullLikeGradFuncObj;
  ReflectionPad1DGradFunc ReflectionPad1DGradFuncObj;
  InplaceSigmoidGradFunc InplaceSigmoidGradFuncObj;
  NormalFloatTensorGradFunc NormalFloatTensorGradFuncObj;
  InplaceEluGradFunc InplaceEluGradFuncObj;
  ReplicationPad2DGradFunc ReplicationPad2DGradFuncObj;
  OuterGradFunc OuterGradFuncObj;
  SplitTensorGradFunc SplitTensorGradFuncObj;
  InplaceDivModGradFunc InplaceDivModGradFuncObj;
  InnerInplaceIndexPutGradFunc InnerInplaceIndexPutGradFuncObj;
  InplaceIndexFillTensorGradFunc InplaceIndexFillTensorGradFuncObj;
  EqualGradFunc EqualGradFuncObj;
  Log10GradFunc Log10GradFuncObj;
  SeLUExtGradFunc SeLUExtGradFuncObj;
  AddScalarGradFunc AddScalarGradFuncObj;
  ReduceMinGradFunc ReduceMinGradFuncObj;
  ConvolutionStrGradGradFunc ConvolutionStrGradGradFuncObj;
  NormGradFunc NormGradFuncObj;
  UpsampleTrilinear3DGradGradFunc UpsampleTrilinear3DGradGradFuncObj;
  InplaceThresholdGradFunc InplaceThresholdGradFuncObj;
  SliceExtGradFunc SliceExtGradFuncObj;
  HardtanhGradFunc HardtanhGradFuncObj;
  BinaryCrossEntropyGradGradFunc BinaryCrossEntropyGradGradFuncObj;
  PowTensorScalarGradFunc PowTensorScalarGradFuncObj;
  RandnGradFunc RandnGradFuncObj;
  TensorScatterElementsGradFunc TensorScatterElementsGradFuncObj;
  CumsumExtGradFunc CumsumExtGradFuncObj;
  NewEmptyGradFunc NewEmptyGradFuncObj;
  GridSampler2DGradGradFunc GridSampler2DGradGradFuncObj;
  ConstantPadNDGradFunc ConstantPadNDGradFuncObj;
  ChunkViewGradFunc ChunkViewGradFuncObj;
  ReplicationPad1DGradFunc ReplicationPad1DGradFuncObj;
  RandLikeExtGradFunc RandLikeExtGradFuncObj;
  InplaceSiLUGradFunc InplaceSiLUGradFuncObj;
  SinhGradFunc SinhGradFuncObj;
  EmptyGradFunc EmptyGradFuncObj;
  InplaceMulsGradFunc InplaceMulsGradFuncObj;
  AvgPool1DGradFunc AvgPool1DGradFuncObj;
  ScatterAddExtGradFunc ScatterAddExtGradFuncObj;
  ClampTensorGradFunc ClampTensorGradFuncObj;
  EqualExtGradFunc EqualExtGradFuncObj;
  InplaceClampTensorGradFunc InplaceClampTensorGradFuncObj;
  MaxPoolWithIndicesGradFunc MaxPoolWithIndicesGradFuncObj;
  InplaceScatterValueReduceGradFunc InplaceScatterValueReduceGradFuncObj;
  EmbeddingDenseBackwardGradFunc EmbeddingDenseBackwardGradFuncObj;
  MedianExtGradFunc MedianExtGradFuncObj;
  BaddbmmGradFunc BaddbmmGradFuncObj;
  RandIntLikeGradFunc RandIntLikeGradFuncObj;
  Conv1DExtGradFunc Conv1DExtGradFuncObj;
  InplaceReLUGradFunc InplaceReLUGradFuncObj;
  RandpermExtGradFunc RandpermExtGradFuncObj;
  ConvolutionGradGradFunc ConvolutionGradGradFuncObj;
  CoshGradFunc CoshGradFuncObj;
  Conv2DExtGradFunc Conv2DExtGradFuncObj;
  NarrowViewGradFunc NarrowViewGradFuncObj;
  LogSigmoidGradGradFunc LogSigmoidGradGradFuncObj;
  InplaceScatterSrcReduceGradFunc InplaceScatterSrcReduceGradFuncObj;
  DropoutGradExtGradFunc DropoutGradExtGradFuncObj;
  ConvTranspose2DGradFunc ConvTranspose2DGradFuncObj;
  AsStridedGradFunc AsStridedGradFuncObj;
  GreaterEqualGradFunc GreaterEqualGradFuncObj;
  AtanExtGradFunc AtanExtGradFuncObj;
  BinaryCrossEntropyGradFunc BinaryCrossEntropyGradFuncObj;
  DotGradFunc DotGradFuncObj;
  CustomExtGradFunc CustomExtGradFuncObj;
  HistcExtGradFunc HistcExtGradFuncObj;
  RoundGradFunc RoundGradFuncObj;
  Conv2DPaddingGradFunc Conv2DPaddingGradFuncObj;
  GcdGradFunc GcdGradFuncObj;
  FlashAttentionScoreGradGradFunc FlashAttentionScoreGradGradFuncObj;
  SwigluGradGradFunc SwigluGradGradFuncObj;
  SoftMarginLossGradGradFunc SoftMarginLossGradGradFuncObj;
  InplaceUniformGradFunc InplaceUniformGradFuncObj;
  ToDtypeGradFunc ToDtypeGradFuncObj;
  ArangeGradFunc ArangeGradFuncObj;
  InnerIndexGradFunc InnerIndexGradFuncObj;
  MoeTokenPermuteGradFunc MoeTokenPermuteGradFuncObj;
  CrossGradFunc CrossGradFuncObj;
  HSigmoidGradGradFunc HSigmoidGradGradFuncObj;
  DivModsGradFunc DivModsGradFuncObj;
  LeakyReLUGradExtGradFunc LeakyReLUGradExtGradFuncObj;
  MlaGradFunc MlaGradFuncObj;
  ReflectionPad3DGradGradFunc ReflectionPad3DGradGradFuncObj;
  InplaceNormalGradFunc InplaceNormalGradFuncObj;
  SigmoidGradFunc SigmoidGradFuncObj;
  EluExtGradFunc EluExtGradFuncObj;
  IsNegInfGradFunc IsNegInfGradFuncObj;
  InplaceFillScalarGradFunc InplaceFillScalarGradFuncObj;
  ToDeviceGradFunc ToDeviceGradFuncObj;
  SqrtGradFunc SqrtGradFuncObj;
  FmodScalarGradFunc FmodScalarGradFuncObj;
  HShrinkGradGradFunc HShrinkGradGradFuncObj;
  TanhGradFunc TanhGradFuncObj;
  BitwiseOrTensorGradFunc BitwiseOrTensorGradFuncObj;
  FloorDivScalarGradFunc FloorDivScalarGradFuncObj;
  GeneratorGradFunc GeneratorGradFuncObj;
  ArgMinExtGradFunc ArgMinExtGradFuncObj;
  StackExtGradFunc StackExtGradFuncObj;
  NLLLoss2dGradFunc NLLLoss2dGradFuncObj;
  GroupNormGradFunc GroupNormGradFuncObj;
  LogSoftmaxGradGradFunc LogSoftmaxGradGradFuncObj;
  LessEqualGradFunc LessEqualGradFuncObj;
  CosGradFunc CosGradFuncObj;
  GatherNdExtGradFunc GatherNdExtGradFuncObj;
  MinimumGradFunc MinimumGradFuncObj;
  IsCloseGradFunc IsCloseGradFuncObj;
  OneHotExtGradFunc OneHotExtGradFuncObj;
  MatrixInverseExtGradFunc MatrixInverseExtGradFuncObj;
  ArgSortGradFunc ArgSortGradFuncObj;
  FracGradFunc FracGradFuncObj;
  AllGatherMatmulGradFunc AllGatherMatmulGradFuncObj;
  InplaceExpGradFunc InplaceExpGradFuncObj;
  RepeatInterleaveIntGradFunc RepeatInterleaveIntGradFuncObj;
  PromptFlashAttentionGradFunc PromptFlashAttentionGradFuncObj;
  LogSoftmaxGradFunc LogSoftmaxGradFuncObj;
  GridSampler2DGradFunc GridSampler2DGradFuncObj;
  Conv3DPaddingGradFunc Conv3DPaddingGradFuncObj;
  UpsampleBicubic2DGradGradFunc UpsampleBicubic2DGradGradFuncObj;
  InnerMoeTokenUnpermuteGradFunc InnerMoeTokenUnpermuteGradFuncObj;
  CloneGradFunc CloneGradFuncObj;
  ThresholdGradGradFunc ThresholdGradGradFuncObj;
  SplitWithSizeGradFunc SplitWithSizeGradFuncObj;
  ReduceAllGradFunc ReduceAllGradFuncObj;
  DivGradFunc DivGradFuncObj;
  SwigluGradFunc SwigluGradFuncObj;
  Atan2ExtGradFunc Atan2ExtGradFuncObj;
  SigmoidGradGradFunc SigmoidGradGradFuncObj;
  InplaceBernoulliTensorGradFunc InplaceBernoulliTensorGradFuncObj;
  InplaceAddmmGradFunc InplaceAddmmGradFuncObj;
  RealViewGradFunc RealViewGradFuncObj;
  SoftplusGradExtGradFunc SoftplusGradExtGradFuncObj;
  ArgMaxWithValueGradFunc ArgMaxWithValueGradFuncObj;
  SquareGradFunc SquareGradFuncObj;
  AddExtGradFunc AddExtGradFuncObj;
  GluGradGradFunc GluGradGradFuncObj;
  ImagViewGradFunc ImagViewGradFuncObj;
  BCEWithLogitsLossGradFunc BCEWithLogitsLossGradFuncObj;
  SoftmaxGradFunc SoftmaxGradFuncObj;
  ScatterValueGradFunc ScatterValueGradFuncObj;
  CellBackwardHookGradFunc CellBackwardHookGradFuncObj;
  EyeGradFunc EyeGradFuncObj;
  Im2ColExtGradFunc Im2ColExtGradFuncObj;
  HSwishGradGradFunc HSwishGradGradFuncObj;
  HShrinkGradFunc HShrinkGradFuncObj;
  XlogyGradFunc XlogyGradFuncObj;
  SmoothL1LossGradFunc SmoothL1LossGradFuncObj;
  SilentCheckV2GradFunc SilentCheckV2GradFuncObj;
  LogicalAndGradFunc LogicalAndGradFuncObj;
  NarrowGradFunc NarrowGradFuncObj;
  MaxPoolGradWithMaskGradFunc MaxPoolGradWithMaskGradFuncObj;
  StdMeanGradFunc StdMeanGradFuncObj;
  BitwiseNotGradFunc BitwiseNotGradFuncObj;
  CeilGradFunc CeilGradFuncObj;
  FlashAttentionScoreGradFunc FlashAttentionScoreGradFuncObj;
  LinalgQrGradFunc LinalgQrGradFuncObj;
  ThresholdGradFunc ThresholdGradFuncObj;
  LogAddExp2GradFunc LogAddExp2GradFuncObj;
  InplaceScatterValueGradFunc InplaceScatterValueGradFuncObj;
  IsFiniteGradFunc IsFiniteGradFuncObj;
  MoeDistributeCombineGradFunc MoeDistributeCombineGradFuncObj;
  ReflectionPad2DGradGradFunc ReflectionPad2DGradGradFuncObj;
  Log2GradFunc Log2GradFuncObj;
  NewOnesGradFunc NewOnesGradFuncObj;
  HardtanhGradGradFunc HardtanhGradGradFuncObj;
  InplaceScatterSrcGradFunc InplaceScatterSrcGradFuncObj;
  InplaceMulGradFunc InplaceMulGradFuncObj;
  LogSoftmaxExtGradFunc LogSoftmaxExtGradFuncObj;
  TruncGradFunc TruncGradFuncObj;
  GridSampler3DGradGradFunc GridSampler3DGradGradFuncObj;
  ReshapeAndCacheGradFunc ReshapeAndCacheGradFuncObj;
  ReshapeGradFunc ReshapeGradFuncObj;
  IndexGradFunc IndexGradFuncObj;
  Col2ImGradGradFunc Col2ImGradGradFuncObj;
  BroadcastToViewGradFunc BroadcastToViewGradFuncObj;
  L1LossExtGradFunc L1LossExtGradFuncObj;
  EluGradExtGradFunc EluGradExtGradFuncObj;
  LessGradFunc LessGradFuncObj;
  LayerNormExtGradFunc LayerNormExtGradFuncObj;
  OnesLikeExtGradFunc OnesLikeExtGradFuncObj;
  TriuGradFunc TriuGradFuncObj;
  MaskedScatterGradFunc MaskedScatterGradFuncObj;
  MinDimGradFunc MinDimGradFuncObj;
  UpsampleNearest1DGradGradFunc UpsampleNearest1DGradGradFuncObj;
  InplaceErfinvGradFunc InplaceErfinvGradFuncObj;
  SiLUGradFunc SiLUGradFuncObj;
  BroadcastToGradFunc BroadcastToGradFuncObj;
  MaxPoolGradWithIndicesGradFunc MaxPoolGradWithIndicesGradFuncObj;
  LogAddExpGradFunc LogAddExpGradFuncObj;
  DenseGradFunc DenseGradFuncObj;
  AdaptiveAvgPool2DExtGradFunc AdaptiveAvgPool2DExtGradFuncObj;
  AsinExtGradFunc AsinExtGradFuncObj;
  BincountExtGradFunc BincountExtGradFuncObj;
  SoftplusExtGradFunc SoftplusExtGradFuncObj;
  MoeTokenPermuteGradGradFunc MoeTokenPermuteGradGradFuncObj;
  ReflectionPad3DGradFunc ReflectionPad3DGradFuncObj;
  ArgMaxExtGradFunc ArgMaxExtGradFuncObj;
  TanGradFunc TanGradFuncObj;
  ConvolutionGradFunc ConvolutionGradFuncObj;
  InplaceMatmulAddGradFunc InplaceMatmulAddGradFuncObj;
  GeLUGradGradFunc GeLUGradGradFuncObj;
  MulsGradFunc MulsGradFuncObj;
  EmbeddingGradFunc EmbeddingGradFuncObj;
  InplaceRandomGradFunc InplaceRandomGradFuncObj;
  FloorDivGradFunc FloorDivGradFuncObj;
  MinGradFunc MinGradFuncObj;
  MaxDimGradFunc MaxDimGradFuncObj;
  SliceExtViewGradFunc SliceExtViewGradFuncObj;
  SoftShrinkGradGradFunc SoftShrinkGradGradFuncObj;
  FFNExtGradFunc FFNExtGradFuncObj;
  LogSigmoidGradFunc LogSigmoidGradFuncObj;
  MaxPoolWithMaskGradFunc MaxPoolWithMaskGradFuncObj;
  PowScalarTensorGradFunc PowScalarTensorGradFuncObj;
  RemainderTensorTensorGradFunc RemainderTensorTensorGradFuncObj;
  BitwiseOrScalarGradFunc BitwiseOrScalarGradFuncObj;
  MultiScaleDeformableAttnGradGradFunc MultiScaleDeformableAttnGradGradFuncObj;
  RotaryPositionEmbeddingGradGradFunc RotaryPositionEmbeddingGradGradFuncObj;
  InplaceHardtanhGradFunc InplaceHardtanhGradFuncObj;
  DivsGradFunc DivsGradFuncObj;
  SmoothL1LossGradGradFunc SmoothL1LossGradGradFuncObj;
  ExpandDimsViewGradFunc ExpandDimsViewGradFuncObj;
  KLDivGradGradFunc KLDivGradGradFuncObj;
  RemainderScalarTensorGradFunc RemainderScalarTensorGradFuncObj;
  NLLLossGradGradFunc NLLLossGradGradFuncObj;
  SplitGradFunc SplitGradFuncObj;
  MaskedSelectGradGradFunc MaskedSelectGradGradFuncObj;
  Exp2GradFunc Exp2GradFuncObj;
  DropoutDoMaskExtGradFunc DropoutDoMaskExtGradFuncObj;
  MatMulGradFunc MatMulGradFuncObj;
  ScatterGradFunc ScatterGradFuncObj;
  UpsampleLinear1DGradFunc UpsampleLinear1DGradFuncObj;
  NegGradFunc NegGradFuncObj;
  ZerosLikeExtGradFunc ZerosLikeExtGradFuncObj;
  LogicalNotGradFunc LogicalNotGradFuncObj;
  ReduceMaxGradFunc ReduceMaxGradFuncObj;
  HSwishGradFunc HSwishGradFuncObj;
  SilentCheckV3GradFunc SilentCheckV3GradFuncObj;
  GreaterGradFunc GreaterGradFuncObj;
  ReplicationPad1DGradGradFunc ReplicationPad1DGradGradFuncObj;
  IndexSelectGradFunc IndexSelectGradFuncObj;
  TopkExtGradFunc TopkExtGradFuncObj;
  MoeTokenUnpermuteGradGradFunc MoeTokenUnpermuteGradGradFuncObj;
  RmsNormGradFunc RmsNormGradFuncObj;
  DropoutGenMaskExtGradFunc DropoutGenMaskExtGradFuncObj;
  PowGradFunc PowGradFuncObj;
  ErfcGradFunc ErfcGradFuncObj;
  InplaceCopyGradFunc InplaceCopyGradFuncObj;
  EluGradFunc EluGradFuncObj;
  CrossEntropyLossGradGradFunc CrossEntropyLossGradGradFuncObj;
  Expm1GradFunc Expm1GradFuncObj;
  FillScalarGradFunc FillScalarGradFuncObj;
  BatchNormElemtGradGradFunc BatchNormElemtGradGradFuncObj;
  IsInfGradFunc IsInfGradFuncObj;
  InplaceSubScalarGradFunc InplaceSubScalarGradFuncObj;
  DiagExtGradFunc DiagExtGradFuncObj;
  GeLUGradFunc GeLUGradFuncObj;
  NotEqualGradFunc NotEqualGradFuncObj;
  UniformExtGradFunc UniformExtGradFuncObj;
  EmptyLikeGradFunc EmptyLikeGradFuncObj;
  AdaptiveAvgPool1DGradFunc AdaptiveAvgPool1DGradFuncObj;
  AddbmmGradFunc AddbmmGradFuncObj;
  SortExtGradFunc SortExtGradFuncObj;
  BatchMatMulGradFunc BatchMatMulGradFuncObj;
  LerpScalarGradFunc LerpScalarGradFuncObj;
  NLLLossGradFunc NLLLossGradFuncObj;
  Conv1DPaddingGradFunc Conv1DPaddingGradFuncObj;
  BitwiseAndTensorGradFunc BitwiseAndTensorGradFuncObj;
  LayerNormGradExtGradFunc LayerNormGradExtGradFuncObj;
  CopyGradFunc CopyGradFuncObj;
  RotaryPositionEmbeddingGradFunc RotaryPositionEmbeddingGradFuncObj;
  ErfinvGradFunc ErfinvGradFuncObj;
  TanhGradGradFunc TanhGradGradFuncObj;
  AcosExtGradFunc AcosExtGradFuncObj;
  SpeedFusionAttentionGradFunc SpeedFusionAttentionGradFuncObj;
  SoftShrinkGradFunc SoftShrinkGradFuncObj;
  L1LossBackwardExtGradFunc L1LossBackwardExtGradFuncObj;
  MeanExtGradFunc MeanExtGradFuncObj;
  NormalTensorTensorGradFunc NormalTensorTensorGradFuncObj;
  BatchMatMulExtGradFunc BatchMatMulExtGradFuncObj;
  GeluGradExtGradFunc GeluGradExtGradFuncObj;
  InplaceAddExtGradFunc InplaceAddExtGradFuncObj;
  Unique2GradFunc Unique2GradFuncObj;
  CountNonZeroGradFunc CountNonZeroGradFuncObj;
  SoftMarginLossGradFunc SoftMarginLossGradFuncObj;
  VarGradFunc VarGradFuncObj;
  InplaceDivGradFunc InplaceDivGradFuncObj;
  FmodTensorGradFunc FmodTensorGradFuncObj;
  AddLayerNormGradGradFunc AddLayerNormGradGradFuncObj;
  NewFullGradFunc NewFullGradFuncObj;
  UpsampleBilinear2DGradFunc UpsampleBilinear2DGradFuncObj;
  CummaxGradFunc CummaxGradFuncObj;
  SpeedFusionAttentionGradGradFunc SpeedFusionAttentionGradGradFuncObj;
  ClampScalarGradFunc ClampScalarGradFuncObj;
  CastGradFunc CastGradFuncObj;
  UniqueDimGradFunc UniqueDimGradFuncObj;
  IdentityGradFunc IdentityGradFuncObj;
  SincGradFunc SincGradFuncObj;
  ReverseV2GradFunc ReverseV2GradFuncObj;
  MultiScaleDeformableAttnGradFunc MultiScaleDeformableAttnGradFuncObj;
  MvGradFunc MvGradFuncObj;
  UpsampleBicubic2DGradFunc UpsampleBicubic2DGradFuncObj;
  Log1pGradFunc Log1pGradFuncObj;
  MulGradFunc MulGradFuncObj;
  NormalFloatFloatGradFunc NormalFloatFloatGradFuncObj;
  InplaceSubExtGradFunc InplaceSubExtGradFuncObj;
  GatherDGradV2GradFunc GatherDGradV2GradFuncObj;
  LinSpaceExtGradFunc LinSpaceExtGradFuncObj;
  InplaceIndexAddExtGradFunc InplaceIndexAddExtGradFuncObj;
  SubGradFunc SubGradFuncObj;
  LogSumExpGradFunc LogSumExpGradFuncObj;
  QuantV2GradFunc QuantV2GradFuncObj;
  DynamicQuantExtGradFunc DynamicQuantExtGradFuncObj;
  GroupedMatmulV2GradFunc GroupedMatmulV2GradFuncObj;
  MoeInitRoutingQuantV2GradFunc MoeInitRoutingQuantV2GradFuncObj;
  GroupedMatmulGradFunc GroupedMatmulGradFuncObj;
  GroupedMatmulV4GradFunc GroupedMatmulV4GradFuncObj;
  WeightQuantBatchMatmulGradFunc WeightQuantBatchMatmulGradFuncObj;
  QuantMatmulGradFunc QuantMatmulGradFuncObj;
  MoeInitRoutingV2GradFunc MoeInitRoutingV2GradFuncObj;
  MoeGatingTopKSoftmaxGradFunc MoeGatingTopKSoftmaxGradFuncObj;
  AddRmsNormQuantV2GradFunc AddRmsNormQuantV2GradFuncObj;
  KVCacheScatterUpdateGradFunc KVCacheScatterUpdateGradFuncObj;
  MoeComputeExpertTokensGradFunc MoeComputeExpertTokensGradFuncObj;
  MoeInitRoutingGradFunc MoeInitRoutingGradFuncObj;
  QuantBatchMatmulGradFunc QuantBatchMatmulGradFuncObj;
  FusedInferAttentionScoreGradFunc FusedInferAttentionScoreGradFuncObj;
  MatmulAllReduceAddRmsNormGradFunc MatmulAllReduceAddRmsNormGradFuncObj;
  MoeFinalizeRoutingGradFunc MoeFinalizeRoutingGradFuncObj;
  InnerCommIsendGradFunc InnerCommIsendGradFuncObj;
  DistCommAllGatherIntoTensorUnevenGradFunc DistCommAllGatherIntoTensorUnevenGradFuncObj;
  DistCommReduceGradFunc DistCommReduceGradFuncObj;
  DistCommBroadcastGradFunc DistCommBroadcastGradFuncObj;
  InnerCommReduceScatterGradFunc InnerCommReduceScatterGradFuncObj;
  DistCommReduceScatterTensorGradFunc DistCommReduceScatterTensorGradFuncObj;
  DistCommAllToAllVSingleGradFunc DistCommAllToAllVSingleGradFuncObj;
  DistCommIsendGradFunc DistCommIsendGradFuncObj;
  InnerCommAllGatherGradFunc InnerCommAllGatherGradFuncObj;
  DistCommBarrierGradFunc DistCommBarrierGradFuncObj;
  DistCommGatherGradFunc DistCommGatherGradFuncObj;
  InnerCommIrecvGradFunc InnerCommIrecvGradFuncObj;
  DistCommReduceScatterTensorUnevenGradFunc DistCommReduceScatterTensorUnevenGradFuncObj;
  DistCommScatterTensorGradFunc DistCommScatterTensorGradFuncObj;
  DistCommAllToAllVGradFunc DistCommAllToAllVGradFuncObj;
  DistCommReduceScatterGradFunc DistCommReduceScatterGradFuncObj;
  DistCommAllToAllVCGradFunc DistCommAllToAllVCGradFuncObj;
  DistCommBatchIsendIrecvGradFunc DistCommBatchIsendIrecvGradFuncObj;
  DistCommIrecvGradFunc DistCommIrecvGradFuncObj;
  InnerCommAllToAllVGradFunc InnerCommAllToAllVGradFuncObj;
  DistCommGatherIntoTensorGradFunc DistCommGatherIntoTensorGradFuncObj;
  DistCommAllGatherIntoTensorGradFunc DistCommAllGatherIntoTensorGradFuncObj;
  DistCommScatterGradFunc DistCommScatterGradFuncObj;
  InnerCommAllReduceGradFunc InnerCommAllReduceGradFuncObj;
  DistCommAllReduceGradFunc DistCommAllReduceGradFuncObj;
  DistCommAllGatherGradFunc DistCommAllGatherGradFuncObj;
  GmmGradFunc GmmGradFuncObj;
  GmmBackwardFusionGradFunc GmmBackwardFusionGradFuncObj;
  FuncDropoutExtGradFunc FuncDropoutExtGradFuncObj;
  MoeTokenUnpermuteGradFunc MoeTokenUnpermuteGradFuncObj;
  AnyExtGradFunc AnyExtGradFuncObj;
  EinsumExtGradFunc EinsumExtGradFuncObj;
  GmmV2BackwardFusionGradFunc GmmV2BackwardFusionGradFuncObj;
  GmmV2GradFunc GmmV2GradFuncObj;
  GmmBackwardGradFunc GmmBackwardGradFuncObj;
  AnyGradFunc AnyGradFuncObj;
  GmmV2BackwardGradFunc GmmV2BackwardGradFuncObj;
  FuncMaxPool2DGradFunc FuncMaxPool2DGradFuncObj;
  PixelShuffleGradFunc PixelShuffleGradFuncObj;
  Dropout2dExtGradFunc Dropout2dExtGradFuncObj;
  InplaceExponentialGradFunc InplaceExponentialGradFuncObj;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_MINDSPORE_OPS_KERNEL_FUNCTIONS_AUTO_GENERATE_AUTO_GRAD_OP_REG_H_
