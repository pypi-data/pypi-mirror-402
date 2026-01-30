/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_MEMSET_CLEAR_TENSORS_H
#define MKI_UTILS_MEMSET_CLEAR_TENSORS_H

#include <cstdint>
#include "mki/kernel_info.h"
#include "mki/utils/status/status.h"

namespace Mki_ms {
Status ClearTensors(void **args, uint64_t argsNum, const MiniVector<KernelInfo::MemsetInfo> &memsetInfo, void *stream);
} // namespace Mki_ms

#endif // MKI_UTILS_MEMSET_CLEAR_TENSORS_H
