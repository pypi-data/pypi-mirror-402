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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_e_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_e_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_e.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimExpm1;
OPS_API extern const PrimitivePtr kPrimExp;
OPS_API extern const PrimitivePtr kPrimExtractImagePatches;
OPS_API extern const PrimitivePtr kPrimEig;
OPS_API extern const PrimitivePtr kPrimEye;
OPS_API extern const PrimitivePtr kPrimErfinv;
OPS_API extern const PrimitivePtr kPrimEluGradExt;
OPS_API extern const PrimitivePtr kPrimExpandDims;
OPS_API extern const PrimitivePtr kPrimExpandAs;
OPS_API extern const PrimitivePtr kPrimErfc;
OPS_API extern const PrimitivePtr kPrimEqual;
OPS_API extern const PrimitivePtr kPrimErf;
OPS_API extern const PrimitivePtr kPrimExp2;
OPS_API extern const PrimitivePtr kPrimEmbeddingDenseBackward;
OPS_API extern const PrimitivePtr kPrimEluExt;
OPS_API extern const PrimitivePtr kPrimElu;
OPS_API extern const PrimitivePtr kPrimEluGrad;
OPS_API extern const PrimitivePtr kPrimEmptyLike;
OPS_API extern const PrimitivePtr kPrimEqualExt;
OPS_API extern const PrimitivePtr kPrimEmbedding;
OPS_API extern const PrimitivePtr kPrimExpandDimsView;
OPS_API extern const PrimitivePtr kPrimEmpty;
OPS_API extern const PrimitivePtr kPrimEinsumExt;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_e_H_
