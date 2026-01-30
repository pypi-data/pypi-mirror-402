/**
 * Copyright 2025 Huawei Technologies Co., Ltd
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
#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_INTERNAL_KERNEL_INFO_ADAPTER_H_
#define MINDSPORE_CCSRC_BACKEND_KERNEL_INTERNAL_KERNEL_INFO_ADAPTER_H_

#include <memory>
#include <string>
#include <vector>
#include "kernel/ascend/internal/pyboost/auto_gen/kernel_info_adapter.h"
#include "kernel/ascend/internal/pyboost/internal_pyboost_utils.h"
#include "kernel/ascend/internal/pyboost/internal_kernel_info.h"
#include "kernel/ascend/internal/pyboost/paged_attention.h"
#include "kernel/ascend/internal/pyboost/reshape_and_cache.h"
#include "kernel/ascend/internal/pyboost/mla.h"
#include "kernel/ascend/internal/pyboost/apply_rotary_pos_emb.h"
#include "kernel/ascend/internal/pyboost/flash_attention_score.h"

namespace mindspore {
namespace kernel {
class InternalPagedAttentionKernelInfoAdapter : public PagedAttentionKernelInfoAdapter {
 public:
  InternalPagedAttentionKernelInfoAdapter() = default;
  ~InternalPagedAttentionKernelInfoAdapter() override = default;

  void InternalKernelCall(const std::shared_ptr<pyboost::OpRunner> &op, const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_cache_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_cache_tensor, const std::optional<mindspore::tensor::TensorPtr> &block_tables_tensor, const std::optional<mindspore::tensor::TensorPtr> &context_lens_tensor, const std::optional<mindspore::tensor::TensorPtr> &antiquant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &antiquant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &attn_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &q_seq_lens_tensor, const std::optional<mindspore::tensor::TensorPtr> &alibi_mask_tensor, const int64_t &head_num_imm, const float &scale_value_imm, const int64_t &kv_head_num_imm, const int64_t &kv_cache_quant_mode_imm, const int64_t &mask_mode_imm, const int64_t &mla_v_dim_imm) override;
  void CreateKernelInfo(const std::string &kernel_name) override;

 private:
  std::shared_ptr<PagedAttention> kernel_info_{nullptr};
};

class InternalReshapeAndCacheKernelInfoAdapter : public ReshapeAndCacheKernelInfoAdapter {
 public:
  InternalReshapeAndCacheKernelInfoAdapter() = default;
  ~InternalReshapeAndCacheKernelInfoAdapter() override = default;

  void InternalKernelCall(const std::shared_ptr<pyboost::OpRunner> &op, const mindspore::tensor::TensorPtr &key_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_tensor, const std::optional<mindspore::tensor::TensorPtr> &key_cache_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_cache_tensor, const std::optional<mindspore::tensor::TensorPtr> &slot_mapping_tensor) override;
  void CreateKernelInfo(const std::string &kernel_name) override;

 private:
  std::shared_ptr<ReshapeAndCache> kernel_info_{nullptr};
};

class InternalMlaKernelInfoAdapter : public MlaKernelInfoAdapter {
 public:
  InternalMlaKernelInfoAdapter() = default;
  ~InternalMlaKernelInfoAdapter() override = default;

  void InternalKernelCall(const std::shared_ptr<pyboost::OpRunner> &op, const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &q_rope_tensor, const mindspore::tensor::TensorPtr &kv_cache_tensor, const mindspore::tensor::TensorPtr &k_rope_tensor, const mindspore::tensor::TensorPtr &block_tables_tensor, const std::optional<mindspore::tensor::TensorPtr> &attn_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &deq_scale_qk_tensor, const std::optional<mindspore::tensor::TensorPtr> &deq_scale_pv_tensor, const std::optional<mindspore::tensor::TensorPtr> &q_seq_lens_tensor, const std::optional<mindspore::tensor::TensorPtr> &context_lens_tensor, const int64_t &head_num_imm, const float &scale_value_imm, const int64_t &kv_head_num_imm, const int64_t &mask_mode_imm, const int64_t &is_ring_imm) override;
  void CreateKernelInfo(const std::string &kernel_name) override;

 private:
  std::shared_ptr<Mla> kernel_info_{nullptr};
};

class InternalApplyRotaryPosEmbKernelInfoAdapter : public ApplyRotaryPosEmbKernelInfoAdapter {
 public:
  InternalApplyRotaryPosEmbKernelInfoAdapter() = default;
  ~InternalApplyRotaryPosEmbKernelInfoAdapter() override = default;

  void InternalKernelCall(const std::shared_ptr<pyboost::OpRunner> &op, const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_tensor, const mindspore::tensor::TensorPtr &cos_tensor, const mindspore::tensor::TensorPtr &sin_tensor, const mindspore::tensor::TensorPtr &position_ids_tensor, const int64_t &cos_format_imm) override;
  void CreateKernelInfo(const std::string &kernel_name) override;

 private:
  std::shared_ptr<ApplyRotaryPosEmb> kernel_info_{nullptr};
};

class InternalFlashAttentionScoreKernelInfoAdapter : public FlashAttentionScoreKernelInfoAdapter {
 public:
  InternalFlashAttentionScoreKernelInfoAdapter() = default;
  ~InternalFlashAttentionScoreKernelInfoAdapter() override = default;

  void InternalKernelCall(const std::shared_ptr<pyboost::OpRunner> &op, const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_tensor, const mindspore::tensor::TensorPtr &value_tensor, const std::optional<mindspore::tensor::TensorPtr> &real_shift_tensor, const std::optional<mindspore::tensor::TensorPtr> &drop_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &padding_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &attn_mask_tensor, const std::vector<int64_t> &prefix_vector, const std::vector<int64_t> &actual_seq_qlen_vector, const std::vector<int64_t> &actual_seq_kvlen_vector, const int64_t &head_num_imm, const float &keep_prob_imm, const float &scale_value_imm, const int64_t &pre_tokens_imm, const int64_t &next_tokens_imm, const int64_t &inner_precise_imm, const int64_t &input_layout_imm, const int64_t &sparse_mode_imm) override;
  void CreateKernelInfo(const std::string &kernel_name) override;

 private:
  std::shared_ptr<FlashAttentionScore> kernel_info_{nullptr};
};
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_CCSRC_BACKEND_KERNEL_INTERNAL_KERNEL_INFO_ADAPTER_H_
