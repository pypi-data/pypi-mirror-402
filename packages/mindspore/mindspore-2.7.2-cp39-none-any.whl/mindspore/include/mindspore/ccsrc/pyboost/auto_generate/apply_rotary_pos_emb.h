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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_APPLYROTARYPOSEMB_H_
#define MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_APPLYROTARYPOSEMB_H_

#include "mindspore/ccsrc/pyboost/op_runner.h"
#include "mindspore/ccsrc/pyboost/op_register.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class PYBOOST_API ApplyRotaryPosEmb : public pyboost::OpRunner {
 public:
  ApplyRotaryPosEmb(PrimitivePtr primitive, const DeviceContext *device_context)
      : OpRunner(std::move(primitive), device_context) {}
  ~ApplyRotaryPosEmb() override = default;

  virtual std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_tensor, const mindspore::tensor::TensorPtr &cos_tensor, const mindspore::tensor::TensorPtr &sin_tensor, const mindspore::tensor::TensorPtr &position_ids_tensor, const mindspore::Int64ImmPtr &cos_format) = 0;
  bool output_is_tuple() const override { return true; }

 protected:
  static const std::string &op_name() {return op_name_;}

  inline static std::string op_name_ = "ApplyRotaryPosEmb";
};

}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_APPLYROTARYPOSEMB_H_
