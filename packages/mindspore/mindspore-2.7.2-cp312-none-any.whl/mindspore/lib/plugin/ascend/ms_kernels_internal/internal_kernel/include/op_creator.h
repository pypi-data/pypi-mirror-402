/**
 * Copyright 2024-2025 Huawei Technologies Co., Ltd
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

#ifndef MS_KERNELS_INTERNAL_KERNEL_OP_CREATOR_H_
#define MS_KERNELS_INTERNAL_KERNEL_OP_CREATOR_H_

#include <string>
#include "include/internal_op.h"
#include "include/op_param.h"

namespace mindspore {
namespace internal {
InternalOpPtr CreateMatmulOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                             const MatmulParam &param, const std::string &op_name);
InternalOpPtr CreateGroupedMatmulOp(const InputsImmutableInfoList &inputs_ii,
                                    const OutputsImmutableInfoList &outputs_ii, const MatmulParam &param,
                                    const std::string &op_name);
InternalOpPtr CreateAddOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                          const std::string &op_name);
InternalOpPtr CreateAddLayerNormOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const NormParam &param, const std::string &op_name);
InternalOpPtr CreateAddRmsNormDynamicQuantOp(const InputsImmutableInfoList &inputs_ii,
                                             const OutputsImmutableInfoList &outputs_ii, const NormParam &param,
                                             const std::string &op_name);
InternalOpPtr CreateAddRmsNormQuantOp(const InputsImmutableInfoList &inputs_ii,
                                      const OutputsImmutableInfoList &outputs_ii, const NormParam &param,
                                      const std::string &op_name);
InternalOpPtr CreateCastOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                           const std::string &op_name);
InternalOpPtr CreateTransposeOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                const TransposeParam &param, const std::string &op_name);
InternalOpPtr CreateQuantPerChannelOp(const InputsImmutableInfoList &inputs_ii,
                                      const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
InternalOpPtr CreateSwishOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                            const std::string &op_name);
InternalOpPtr CreateSwiGLUOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                             const SwiGLUParam &param, const std::string &op_name);
InternalOpPtr CreateSwiGLUDynamicQuantOp(const InputsImmutableInfoList &inputs_ii,
                                         const OutputsImmutableInfoList &outputs_ii, const SwiGLUParam &param,
                                         const std::string &op_name);
InternalOpPtr CreateLogicalNotOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                 const std::string &op_name);
InternalOpPtr CreateSoftmaxOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                              const SoftmaxParam &param, const std::string &op_name);
InternalOpPtr CreateReduceSumOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                const ReduceSumParam &param, const std::string &op_name);
InternalOpPtr CreateGatherOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                             const GatherParam &param, const std::string &op_name);
InternalOpPtr CreateApplyRotaryPosEmbOp(const InputsImmutableInfoList &inputs_ii,
                                        const OutputsImmutableInfoList &outputs_ii, const ApplyRotaryPosEmbParam &param,
                                        const std::string &op_name);
InternalOpPtr CreateApplyRotaryPosEmbNzOp(const InputsImmutableInfoList &inputs_ii,
                                          const OutputsImmutableInfoList &outputs_ii,
                                          const ApplyRotaryPosEmbParam &param, const std::string &op_name);
InternalOpPtr CreateRmsNormOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                              const NormParam &param, const std::string &op_name);
InternalOpPtr CreateMatmulAddRmsNormOp(const InputsImmutableInfoList &inputs_ii,
                                       const OutputsImmutableInfoList &outputs_ii, const MatmulAddRmsNormParam &param,
                                       const std::string &op_name);
InternalOpPtr CreateMultiWeightMatmulOp(const InputsImmutableInfoList &inputs_ii,
                                        const OutputsImmutableInfoList &outputs_ii, const MultiWeightMatmulParam &param,
                                        const std::string &op_name);
InternalOpPtr CreateTransposeBatchMatmulTransposeOp(const InputsImmutableInfoList &inputs_ii,
                                                    const OutputsImmutableInfoList &outputs_ii,
                                                    const TransBMMTransParam &param, const std::string &op_name);
// param section 0
InternalOpPtr CreateGeLUOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                           const std::string &op_name);
InternalOpPtr CreateMoeTokenUnpermuteOp(const InputsImmutableInfoList &inputs_ii,
                                        const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
InternalOpPtr CreateAddRmsNormOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                 const NormParam &param, const std::string &op_name);
InternalOpPtr CreateRmsNormQuantOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const NormParam &param, const std::string &op_name);
InternalOpPtr CreateGatherPreRmsNormOp(const InputsImmutableInfoList &inputs_ii,
                                       const OutputsImmutableInfoList &outputs_ii, const NormParam &param,
                                       const std::string &op_name);
InternalOpPtr CreateFlashAttentionScoreOp(const InputsImmutableInfoList &inputs_ii,
                                          const OutputsImmutableInfoList &outputs_ii,
                                          const FlashAttentionScoreParam &param, const std::string &op_name);
InternalOpPtr CreatePagedAttentionOp(const InputsImmutableInfoList &inputs_ii,
                                     const OutputsImmutableInfoList &outputs_ii, const PagedAttentionParam &param,
                                     const std::string &op_name);
// param section 1
InternalOpPtr CreateKvScaleCacheOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const KvScaleCacheParam &param, const std::string &op_name);
InternalOpPtr CreateReshapeAndCacheOp(const InputsImmutableInfoList &inputs_ii,
                                      const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
InternalOpPtr CreateReshapeAndCacheNzOp(const InputsImmutableInfoList &inputs_ii,
                                        const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
InternalOpPtr CreateAsdReshapeAndCacheOp(const InputsImmutableInfoList &inputs_ii,
                                         const OutputsImmutableInfoList &outputs_ii, const ReshapeAndCacheParam &param,
                                         const std::string &op_name);
InternalOpPtr CreateMulOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                          const std::string &op_name);
InternalOpPtr CreateSubOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                          const std::string &op_name);
InternalOpPtr CreateRealDivOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                              const std::string &op_name);

// param section 2
InternalOpPtr CreateFastGeLUOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                               const std::string &op_name);
InternalOpPtr CreateTransDataOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                const TransDataParam &param, const std::string &op_name);
InternalOpPtr CreateQuantLinearSparseOp(const InputsImmutableInfoList &inputs_ii,
                                        const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
InternalOpPtr CreateTssAddLayerNormOp(const InputsImmutableInfoList &inputs_ii,
                                      const OutputsImmutableInfoList &outputs_ii, const std::string &op_name);
// param section 3
InternalOpPtr CreateLessOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                           const std::string &op_name);
InternalOpPtr CreateEqualOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                            const std::string &op_name);
InternalOpPtr CreateNotEqualOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                               const std::string &op_name);
// param section 4
InternalOpPtr CreateGroupTopkOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                const GroupTopkParam &param, const std::string &op_name);
InternalOpPtr CreateFusedAddTopkDivOp(const InputsImmutableInfoList &inputs_ii,
                                      const OutputsImmutableInfoList &outputs_ii, const FusedAddTopkDivParam &param,
                                      const std::string &op_name);
InternalOpPtr CreateMlaPreprocessOp(const InputsImmutableInfoList &inputs_ii,
                                    const OutputsImmutableInfoList &outputs_ii, const MlaPreprocessParam &param,
                                    const std::string &op_name);
// param section 5
InternalOpPtr CreateSplitOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                            const SplitParam &param, const std::string &op_name);
InternalOpPtr CreatePagedCacheLoadOp(const InputsImmutableInfoList &inputs_ii,
                                     const OutputsImmutableInfoList &outputs_ii, const PagedCacheLoadParam &param,
                                     const std::string &op_name);

// param section 6
InternalOpPtr CreateDynamicNTKOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                 const DynamicNTKParam &param, const std::string &op_name);
InternalOpPtr CreateDynamicQuantOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const std::string &op_name);
// param section 7
InternalOpPtr CreateMLAOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                          const MLAParam &param, const std::string &op_name);
InternalOpPtr CreateRingMLAOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                              const RingMLAParam &param, const std::string &op_name);

InternalOpPtr CreateMoeGatingGroupTopKOp(const InputsImmutableInfoList &inputs_ii,
                                         const OutputsImmutableInfoList &outputs_ii,
                                         const MoeGatingGroupTopKParam &param, const std::string &op_name);
// param section 8

// param section 9

// param section 10

InternalOpPtr CreateMoeInitRoutingOp(const InputsImmutableInfoList &inputs_ii,
                                     const OutputsImmutableInfoList &outputs_ii, const MoeInitRoutingParam &param,
                                     const std::string &op_name);

bool IsInternalKernelDtypesSupported(const std::string op_name, InputDataTypes in_dtypes, InputDataTypes out_dtypes);
}  // namespace internal
}  // namespace mindspore

#endif  // MS_KERNELS_INTERNAL_KERNEL_OP_CREATOR_H_
