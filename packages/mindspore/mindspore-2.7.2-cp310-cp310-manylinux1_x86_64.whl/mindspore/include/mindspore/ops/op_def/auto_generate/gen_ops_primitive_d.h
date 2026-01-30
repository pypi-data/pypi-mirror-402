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
#ifndef MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_d_H_
#define MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_d_H_

#include "ir/primitive.h"
#include "mindapi/base/macros.h"
#include "mindspore/ops/op_def/auto_generate/gen_ops_name_d.h"

namespace mindspore::prim {
OPS_API extern const PrimitivePtr kPrimDumpGradient;
OPS_API extern const PrimitivePtr kPrimDCTN;
OPS_API extern const PrimitivePtr kPrimDense;
OPS_API extern const PrimitivePtr kPrimDCT;
OPS_API extern const PrimitivePtr kPrimDivMod;
OPS_API extern const PrimitivePtr kPrimDiagonalView;
OPS_API extern const PrimitivePtr kPrimDropoutDoMaskExt;
OPS_API extern const PrimitivePtr kPrimDropoutGradExt;
OPS_API extern const PrimitivePtr kPrimDivs;
OPS_API extern const PrimitivePtr kPrimDiv;
OPS_API extern const PrimitivePtr kPrimDiagonal;
OPS_API extern const PrimitivePtr kPrimDiagExt;
OPS_API extern const PrimitivePtr kPrimDivMods;
OPS_API extern const PrimitivePtr kPrimDiag;
OPS_API extern const PrimitivePtr kPrimDot;
OPS_API extern const PrimitivePtr kPrimDropout;
OPS_API extern const PrimitivePtr kPrimDequantSwigluQuant;
OPS_API extern const PrimitivePtr kPrimDropoutGenMaskExt;
OPS_API extern const PrimitivePtr kPrimDropoutExt;
OPS_API extern const PrimitivePtr kPrimDynamicQuantExt;
OPS_API extern const PrimitivePtr kPrimDynamicNTK;
OPS_API extern const PrimitivePtr kPrimDistCommReduce;
OPS_API extern const PrimitivePtr kPrimDistCommScatter;
OPS_API extern const PrimitivePtr kPrimDistCommReduceScatter;
OPS_API extern const PrimitivePtr kPrimDistCommGather;
OPS_API extern const PrimitivePtr kPrimDistCommAllToAllVSingle;
OPS_API extern const PrimitivePtr kPrimDistCommAllGather;
OPS_API extern const PrimitivePtr kPrimDistCommIrecv;
OPS_API extern const PrimitivePtr kPrimDistCommReduceScatterTensorUneven;
OPS_API extern const PrimitivePtr kPrimDistCommIsend;
OPS_API extern const PrimitivePtr kPrimDistCommScatterTensor;
OPS_API extern const PrimitivePtr kPrimDistCommBatchIsendIrecv;
OPS_API extern const PrimitivePtr kPrimDistCommAllGatherIntoTensor;
OPS_API extern const PrimitivePtr kPrimDistCommAllToAllV;
OPS_API extern const PrimitivePtr kPrimDistCommAllReduce;
OPS_API extern const PrimitivePtr kPrimDistCommAllGatherIntoTensorUneven;
OPS_API extern const PrimitivePtr kPrimDistCommReduceScatterTensor;
OPS_API extern const PrimitivePtr kPrimDistCommAllToAllVC;
OPS_API extern const PrimitivePtr kPrimDistCommBarrier;
OPS_API extern const PrimitivePtr kPrimDistCommGatherIntoTensor;
OPS_API extern const PrimitivePtr kPrimDistCommBroadcast;
OPS_API extern const PrimitivePtr kPrimDropout2dExt;
}  // namespace mindspore::prim
#endif  // MINDSPORE_CORE_OPS_GEN_OPS_PRIMITIVE_d_H_
