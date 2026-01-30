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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_INTERNAL_FLASHATTENTIONSCORE_ASCEND_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_INTERNAL_FLASHATTENTIONSCORE_ASCEND_H_

#include "mindspore/ccsrc/pyboost/auto_generate/flash_attention_score.h"
#include "ir/tensor.h"
#include "ir/scalar.h"
#include "mindspore/ops/ops_utils/memory_overlap.h"
#include "kernel/ascend/visible.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class OPS_ASCEND_API InternalFlashAttentionScoreAscend : public pyboost::FlashAttentionScore {
 public:
  InternalFlashAttentionScoreAscend(PrimitivePtr primitive, const DeviceContext *device_context)
      : FlashAttentionScore(std::move(primitive), device_context) {}
  ~InternalFlashAttentionScoreAscend() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_tensor, const mindspore::tensor::TensorPtr &value_tensor, const std::optional<mindspore::tensor::TensorPtr> &real_shift_tensor, const std::optional<mindspore::tensor::TensorPtr> &drop_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &padding_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &attn_mask_tensor, const std::optional<mindspore::ValueTuplePtr> &prefix, const std::optional<mindspore::ValueTuplePtr> &actual_seq_qlen, const std::optional<mindspore::ValueTuplePtr> &actual_seq_kvlen, const mindspore::Int64ImmPtr &head_num, const mindspore::FP32ImmPtr &keep_prob, const mindspore::FP32ImmPtr &scale_value, const mindspore::Int64ImmPtr &pre_tokens, const mindspore::Int64ImmPtr &next_tokens, const mindspore::Int64ImmPtr &inner_precise, const mindspore::Int64ImmPtr &input_layout, const mindspore::Int64ImmPtr &sparse_mode) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_ASCEND_KERNEL_PYBOOST_INTERNAL_FLASHATTENTIONSCORE_ASCEND_H_
