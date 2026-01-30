/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

#ifndef MKI_UTILS_MATH_MATH_H
#define MKI_UTILS_MATH_MATH_H

#include <cstdint>
#include "mki/utils/log/log.h"

namespace Mki_ms {
namespace Utils {
template <typename T>
T CeilDiv(T dividend, T divisor)
{
    return (divisor == 0) ? 0 : ((dividend + divisor - 1) / divisor);
}
size_t RoundUp(size_t size, size_t divisor = 32);
size_t RoundDown(size_t size, size_t divisor = 32);
void SetRandseeds(uint32_t &randseed);
}
}

#endif // MKI_UTILS_MATH_MATH_H
