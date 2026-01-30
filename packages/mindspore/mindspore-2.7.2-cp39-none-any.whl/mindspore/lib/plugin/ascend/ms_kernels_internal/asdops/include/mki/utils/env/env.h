/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

#ifndef MKI_ENV_ENV_H
#define MKI_ENV_ENV_H

#include <cstdlib>
#include <cstring>
#include "mki/utils/assert/assert.h"
#include "mki/utils/log/log.h"

namespace Mki_ms {
constexpr size_t MAX_ENV_STRING_LEN = 12800;

inline const char *GetEnv(const char *name)
{
    MKI_CHECK(name != nullptr, "env name is nullptr!", return nullptr);
    const char *env = std::getenv(name);
    if (env != nullptr && strlen(env) <= MAX_ENV_STRING_LEN) {
        return env;
    }
    MKI_LOG(WARN) << "env " << name << " is too long or not exist!";
    return nullptr;
}
} // namespace mki

#endif // MKI_ENV_ENV_H