/**
 * Copyright 2023 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_FUSEDINFERATTENTIONSCORE_H_
#define MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_FUSEDINFERATTENTIONSCORE_H_

#include "mindspore/ccsrc/pyboost/op_runner.h"
#include "mindspore/ccsrc/pyboost/op_register.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class PYBOOST_API FusedInferAttentionScore : public pyboost::OpRunner {
 public:
  FusedInferAttentionScore(PrimitivePtr primitive, const DeviceContext *device_context)
      : OpRunner(std::move(primitive), device_context) {}
  ~FusedInferAttentionScore() override = default;

  virtual std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &query_tensor, const mindspore::ValueTuplePtr &key_tensor_list, const mindspore::ValueTuplePtr &value_tensor_list, const std::optional<mindspore::tensor::TensorPtr> &pse_shift_tensor, const std::optional<mindspore::tensor::TensorPtr> &attn_mask_tensor, const std::optional<mindspore::tensor::TensorPtr> &actual_seq_lengths_tensor, const std::optional<mindspore::tensor::TensorPtr> &actual_seq_lengths_kv_tensor, const std::optional<mindspore::tensor::TensorPtr> &dequant_scale1_tensor, const std::optional<mindspore::tensor::TensorPtr> &quant_scale1_tensor, const std::optional<mindspore::tensor::TensorPtr> &dequant_scale2_tensor, const std::optional<mindspore::tensor::TensorPtr> &quant_scale2_tensor, const std::optional<mindspore::tensor::TensorPtr> &quant_offset2_tensor, const std::optional<mindspore::tensor::TensorPtr> &antiquant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &antiquant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &block_table_tensor, const std::optional<mindspore::tensor::TensorPtr> &query_padding_size_tensor, const std::optional<mindspore::tensor::TensorPtr> &kv_padding_size_tensor, const std::optional<mindspore::tensor::TensorPtr> &key_antiquant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &key_antiquant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_antiquant_scale_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_antiquant_offset_tensor, const std::optional<mindspore::tensor::TensorPtr> &key_shared_prefix_tensor, const std::optional<mindspore::tensor::TensorPtr> &value_shared_prefix_tensor, const std::optional<mindspore::tensor::TensorPtr> &actual_shared_prefix_len_tensor, const mindspore::Int64ImmPtr &num_heads, const mindspore::FP32ImmPtr &scale_value, const mindspore::Int64ImmPtr &pre_tokens, const mindspore::Int64ImmPtr &next_tokens, const mindspore::Int64ImmPtr &input_layout, const mindspore::Int64ImmPtr &num_key_value_heads, const mindspore::Int64ImmPtr &sparse_mode, const mindspore::Int64ImmPtr &inner_precise, const mindspore::Int64ImmPtr &block_size, const mindspore::Int64ImmPtr &antiquant_mode, const mindspore::BoolImmPtr &softmax_lse_flag, const mindspore::Int64ImmPtr &key_antiquant_mode, const mindspore::Int64ImmPtr &value_antiquant_mode) = 0;
  bool output_is_tuple() const override { return true; }

 protected:
  static const std::string &op_name() {return op_name_;}

  inline static std::string op_name_ = "FusedInferAttentionScore";
};

}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_FUSEDINFERATTENTIONSCORE_H_
