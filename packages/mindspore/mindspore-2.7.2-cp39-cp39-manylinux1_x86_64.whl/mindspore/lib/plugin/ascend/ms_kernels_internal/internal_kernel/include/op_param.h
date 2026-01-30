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

#ifndef MS_KERNELS_INTERNAL_KERNEL_OP_PARAM_H_
#define MS_KERNELS_INTERNAL_KERNEL_OP_PARAM_H_

#include <stdint.h>
#include <vector>

namespace mindspore {
namespace internal {
// matmul fused op
constexpr auto kInternalMatMulOpName = "MatMul";
constexpr auto kInternalGroupedMatmulOpName = "GroupedMatmul";
constexpr auto kInternalMultiWeightMatmulOpName = "MultiWeightMatmul";
constexpr auto kInternalMatMulAddRmsNormOpName = "MatMulAddRmsNorm";
constexpr auto kInternalTransBMMTransOpName = "TransposeBatchMatmulTranspose";
// attention fused op
constexpr auto kInternalFlashAttentionScoreOpName = "FlashAttentionScore";
constexpr auto kInternalPagedAttentionOpName = "PagedAttention";
constexpr auto kInternalReshapeAndCacheOpName = "ReshapeAndCache";
constexpr auto kInternalAsdReshapeAndCacheOpName = "AsdReshapeAndCache";
constexpr auto kInternalKvScaleCacheOpName = "KvScaleCache";
constexpr auto kInternalReshapeAndCacheNzOpName = "ReshapeAndCacheNz";
constexpr auto kInternalApplyRotaryPosEmbOpName = "ApplyRotaryPosEmb";
constexpr auto kInternalApplyRotaryPosEmbNzOpName = "ApplyRotaryPosEmbNz";
constexpr auto kInternalMLAOpName = "MultiLatentAttention";
constexpr auto kInternalRingMLAOpName = "RingMLA";
// norm fused op
constexpr auto kInternalAddLayerNormOpName = "AddLayerNorm";
constexpr auto kInternalRmsNormOpName = "RmsNorm";
constexpr auto kInternalAddRmsNormOpName = "AddRmsNorm";
constexpr auto kInternalRmsNormQuantOpName = "RmsNormQuant";
constexpr auto kInternalAddRmsNormQuantOpName = "AddRmsNormQuantV2";
constexpr auto kInternalAddRmsNormDynamicQuantOpName = "AddRmsNormDynamicQuant";
constexpr auto kInternalGatherPreRmsNormOpName = "GatherPreRmsNorm";
// activation
constexpr auto kInternalReluOpName = "Relu";
constexpr auto kInternalGeLUOpName = "GeLU";
constexpr auto kInternalFastGeLUOpName = "FastGeLU";
constexpr auto kInternalMoeTokenUnpermuteOpName = "MoeTokenUnpermute";
constexpr auto kInternalSwishOpName = "Swish";
constexpr auto kInternalSwiGLUOpName = "SwiGLU";
constexpr auto kInternalSwiGLUDynamicQuantOpName = "SwiGLUDynamicQuant";
// elewise unary
constexpr auto kInternalCastOpName = "Cast";
constexpr auto kInternalExpOpName = "Exp";
constexpr auto kInternalLnOpName = "Ln";
constexpr auto kInternalRsqrtOpName = "Rsqrt";
constexpr auto kInternalSqrtOpName = "Sqrt";
constexpr auto kInternalAbsOpName = "Abs";
constexpr auto kInternalReciprocalOpName = "Reciprocal";
// elewise binary
constexpr auto kInternalAddOpName = "Add";
constexpr auto kInternalSubOpName = "Sub";
constexpr auto kInternalMulOpName = "Mul";
constexpr auto kInternalDivOpName = "Div";
constexpr auto kInternalRealDivOpName = "RealDiv";
constexpr auto kInternalMaxOpName = "Max";
constexpr auto kInternalMinOpName = "Min";
constexpr auto kInternalNotOpName = "Not";
constexpr auto kInternalOrOpName = "Or";
constexpr auto kInternalAndOpName = "And";
constexpr auto kInternalEqualOpName = "Equal";
constexpr auto kInternalNotEqualOpName = "NotEqual";
constexpr auto kInternalLessOpName = "Less";
constexpr auto kInternalLessEqualOpName = "LessEqual";
constexpr auto kInternalGreaterOpName = "Greater";
constexpr auto kInternalGreaterEqualOpName = "GreaterEqual";
constexpr auto kInternalLogicalNotOpName = "LogicalNot";
// others
constexpr auto kInternalSplitOpName = "Split";
constexpr auto kInternalGatherOpName = "Gather";
constexpr auto kInternalTransposeOpName = "Transpose";
constexpr auto kInternalTransDataOpName = "TransData";
constexpr auto kInternalQuantPerChannelOpName = "QuantPerChannel";
constexpr auto kInternalDynamicNTKOpName = "DynamicNTK";
constexpr auto kInternalSoftmaxOpName = "Softmax";
constexpr auto kInternalReduceSumOpName = "ReduceSum";
constexpr auto kInternalQuantLinearSparseOpName = "QuantLinearSparse";
constexpr auto kInternalGroupTopkOpName = "GroupTopk";
constexpr auto kInternalMoeGatingGroupTopKOpName = "MoeGatingGroupTopK";
constexpr auto kInternalFusedAddTopkDivOpName = "FusedAddTopkDiv";
constexpr auto kInternalMlaPreprocessOpName = "MlaPreprocess";
constexpr auto kInternalMoeInitRoutingOpName = "MoeInitRouting";
constexpr auto kInternalDynamicQuantOpName = "DynamicQuant";
constexpr auto kInternalPagedCacheLoadOpName = "PagedCacheLoad";

struct AxesParam {
  std::vector<int64_t> axes;
};

using TransposeParam = AxesParam;
using SoftmaxParam = AxesParam;
using ReduceSumParam = AxesParam;

struct GatherParam {
  int64_t batch_dims;
  std::vector<int64_t> axes;
};

struct SwiGLUParam {
  int64_t axis;
  bool is_fusion_v2{false};
  bool with_dyn_quant{false};
};

struct MatmulParam {
  bool transpose_a{false};
  bool transpose_b{false};
  bool enable_dequant{false};
  bool with_relu{false};
  bool with_gelu{false};
  bool with_fastgelu{false};
  bool with_bias{false};
  bool with_bias_fastgelu{false};
  bool with_sigmoid_add{false};
  bool enable_shuffle{false};
  bool with_pertoken_scale{false};
  uint32_t tilingN = 0;  // 压缩算法透传参数, 单压缩块 n 方向的基块数
  uint32_t tilingK = 0;  // 压缩算法透传参数, 单压缩块 k 方向的基块数
};

struct MatmulAddRmsNormParam {
  bool transpose_a{false};
  bool transpose_b{false};
  float eps{1e-6};
};

struct MultiWeightMatmulParam {
  uint32_t n0_len{0};
  uint32_t n1_len{0};
  uint32_t n2_len{0};
  bool transpose_a;
  bool transpose_b;
  int32_t silu_position{-1};
  bool with_bias{false};
  bool fused{false};
  bool split_two{true};
};

struct TransBMMTransParam {
  std::vector<int64_t> perm_in;
  std::vector<int64_t> perm_out;
  bool transpose_a{false};
  bool transpose_b{false};
  bool with_bias{false};
};

struct NormParam {
  float eps;
  bool need_rms_norm_out{false};  // only for fused kernels such as AddRmsNormQuant
};

struct ApplyRotaryPosEmbParam {
  // cos_format=0  shape是[maxSeqLen, headDim]，    cos/sin不交替
  // cos_format=1  shape是[maxSeqLen, headDim]，    cos/sin交替
  // cos_format=2  shape是[batch*seqLen, headDim]， cos/sin不交替
  // cos_format=3  shape是[batch*seqLen, headDim]， cos/sin交替
  int32_t cos_format{0};
  int32_t rotary_coeff{-1};
  std::vector<int32_t> batch_valid_length;
};

struct TransDataParam {
  enum TransdataType { UNDEFINED = 0, FRACTAL_NZ_TO_ND, ND_TO_FRACTAL_NZ };
  TransdataType transdataType = UNDEFINED;
  enum SpecialType { NORMAL = 0, ATTENTION_INPUT_QKV, ATTENTION_INPUT_MASK };
  int64_t specialTransdata = NORMAL;
};

struct DynamicNTKParam {
  int64_t out_type;
};

struct FlashAttentionScoreParam {
  int32_t head_num = 0;
  int32_t inner_precise = 0;
  int32_t pre_tokens = 2147483647;
  int32_t next_tokens = 0;
  int32_t sparse_mode = 0;
  int32_t mask_dtype = 0;
  int32_t input_layout = 0;
  std::vector<int64_t> mask_dims;
  std::vector<int32_t> kv_seq_len;
  std::vector<int32_t> q_seq_len;
  float tor = 0;

  enum InputLayoutMode : int64_t { BSH = 0, BNSD = 1, SBH = 2, BSND = 3, TND = 4, TH = 5, NSD = 6, SH = 7 };
  enum InnerPrecise : int64_t { BMM1_FP16_EXP_FP32 = 0, BMM1_FP32_EXP_FP32 = 1, BMM2_ONLINE_SOFTMAX_FP16 = 2 };
};

struct PagedAttentionParam {
  int32_t inner_precise = 0;
  int32_t head_num = 0;
  int32_t kv_head_num = 0;
  std::vector<int32_t> kv_seq_len;
  std::vector<int32_t> q_seq_len;
  float tor = 0;

  enum MaskType : uint32_t { kMaskTypeNone = 0, kMaskTypeAlibi = 1, kMaskTypeLookAhead = 2 };
  MaskType mask_type = kMaskTypeNone;
  int32_t kv_cache_quant_mode = 0;
  enum MaskMode : uint32_t { kDefaultMask = 0, kTrapezoidalMask = 1 };
  MaskMode mask_mode = kDefaultMask;
  int32_t mla_v_dim = 0;
  bool has_q_seq_lens{false};
};

struct GroupTopkParam {
  int32_t group_num{0};
  int32_t k{0};
  int32_t k_inner{0};
};

struct SplitParam {
  int32_t split_dim;
  std::vector<uint32_t> split_sizes;
};

struct FusedAddTopkDivParam {
  int32_t group_num = 1;
  int32_t group_topk = 1;
  int32_t n = 1;
  int32_t k = 1;
  int32_t activate_type = 0;
  bool is_norm = true;
  float scale = 1.0;
  bool enableExpertMapping = false;
};
struct MoeGatingGroupTopKParam {
  int32_t k{1};
  int32_t k_group{1};
  int32_t group_count{1};
  int32_t group_select_mode{0};
  int32_t renorm{0};
  int32_t norm_type{0};
  bool out_flag{false};
  float routed_scaling_factor{1.0};
  float eps{1e-20};
};

struct MLAParam {
  enum Type {
    kSplitCache = 0,
  };
  Type type = kSplitCache;
  int32_t head_size = 0;
  float tor = 0;
  int32_t kv_head = 0;

  enum MaskType {
    kMaskTypeNone = 0,
    kMaskTypeNorm = 1,
    kMaskTypeAlibi = 2,
    kMaskTypeLookAhead = 3,
    kMaskTypeMaskFree = 4
  };

  MaskType mask_type = kMaskTypeNone;

  std::vector<int32_t> q_seq_len;
  std::vector<int32_t> kv_seq_len;

  int32_t is_ring = 0;
};

//!
//! \struct RingMLAParam
//!
//! \warning 仅Atlas 800I/T A2/A3推理产品支持该算子
//!
struct RingMLAParam {
  //!
  //! \enum CalcType
  //!
  //! \brief 计算类型
  //!
  enum CalcType : int {
      CALC_TYPE_DEFAULT = 0,  // 默认，非首末卡场景，有prev_lse, prev_o传入，生成softmaxLse输出
      CALC_TYPE_FISRT_RING,   // 首卡场景，无prev_lse, prev_o传入，生成softmaxLse输出
      CALC_TYPE_MAX
  };
  //!
  //! \enum KernelType
  //!
  //! \brief 算子内核精度类型
  //!
  enum KernelType : int {
      KERNELTYPE_DEFAULT = 0,    //!< i:float16, bmm:float16, o:float16
      KERNELTYPE_HIGH_PRECISION  //!< i:float16, bmm:float, o:float16
  };

  //!
  //! \enum MaskType
  //!
  //! \brief mask类型
  //!
  enum MaskType : int {
      NO_MASK = 0,     //!< 全0mask
      MASK_TYPE_TRIU,  //!< 默认值，上三角mask
  };

  //! 计算类型
  CalcType calcType = CalcType::CALC_TYPE_DEFAULT;

  //! query头大小, 需大于0
  int32_t headNum = 0;
  //! kv头数量, 该值需要用户根据使用的模型实际情况传入
  //! kvHeadNum = 0时，keyCache的k_head_num，valueCache的v_head_num与query的num_heads一致，均为num_heads的数值
  //! kvHeadNum != 0时，keyCache的k_head_num， valueCache的v_head_num与kvHeadNum值相同
  int32_t kvHeadNum = 0;

  //! 算子tor值, 在Q*K^T后乘
  float qkScale = 1;

  //! 内核精度类型
  KernelType kernelType = KERNELTYPE_HIGH_PRECISION;  // 预留

  //! mask类型
  MaskType maskType = MASK_TYPE_TRIU;

  //!
  //! \enum InputLayout
  //!
  //! \brief 数据排布类型
  //!
  enum InputLayout : int {
    TYPE_BSND = 0,  //!< 默认值，表示数据排布为BSND
    TYPE_BNSD       //!< 表示数据排布为BNSD
  };

  //! 数据排布格式默认为BSND
  InputLayout inputLayout = TYPE_BSND;

  std::vector<int32_t> qSeqLen;
  std::vector<int32_t> kvSeqLen;

  //!
  //! \brief 预留参数
  //!
  uint8_t rsv[64] = {0};
};

struct KvScaleCacheParam {
  int32_t cache_mode = -1;
};

struct MlaPreprocessParam {
  int32_t n = 1;
  int32_t head_num = 1;
  int32_t cache_mode = 1;
};

struct MoeInitRoutingParam {
  int32_t active_num = 1;
  int32_t expert_capacity = 1;
  int32_t expert_num = 1;
  int32_t drop_pad_mode = 0;
  int32_t expert_tokens_count_or_cumsum_flag = 0;
  bool expert_tokens_before_capacity_flag = false;
};

struct ReshapeAndCacheParam {
  int32_t head_num = 0;
};

struct PagedCacheLoadParam {
  int32_t kv_cache_cfg_type = 0;
  bool is_seq_lens_cumsum_type = false;
  bool has_seq_starts = false;
  int64_t sum_context_lens = 0;
};
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_OP_PARAM_H_
