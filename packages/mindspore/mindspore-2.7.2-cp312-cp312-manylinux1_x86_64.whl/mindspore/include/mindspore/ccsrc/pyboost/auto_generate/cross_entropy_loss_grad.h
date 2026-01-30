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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_CROSSENTROPYLOSSGRAD_H_
#define MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_CROSSENTROPYLOSSGRAD_H_

#include "mindspore/ccsrc/pyboost/op_runner.h"
#include "mindspore/ccsrc/pyboost/op_register.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class PYBOOST_API CrossEntropyLossGrad : public pyboost::OpRunner {
 public:
  CrossEntropyLossGrad(PrimitivePtr primitive, const DeviceContext *device_context)
      : OpRunner(std::move(primitive), device_context) {}
  ~CrossEntropyLossGrad() override = default;

  virtual mindspore::tensor::TensorPtr Call(const mindspore::tensor::TensorPtr &grad_loss_tensor, const mindspore::tensor::TensorPtr &log_prob_tensor, const mindspore::tensor::TensorPtr &target_tensor, const std::optional<mindspore::tensor::TensorPtr> &weight_tensor, const std::optional<mindspore::tensor::TensorPtr> &grad_zloss_tensor, const std::optional<mindspore::tensor::TensorPtr> &lse_for_zloss_tensor, const mindspore::Int64ImmPtr &reduction, const mindspore::Int64ImmPtr &ignore_index, const mindspore::FP32ImmPtr &label_smoothing, const mindspore::FP32ImmPtr &lse_square_scale_for_zloss) = 0;


 protected:
  static const std::string &op_name() {return op_name_;}

  inline static std::string op_name_ = "CrossEntropyLossGrad";
};

}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_CROSSENTROPYLOSSGRAD_H_
