/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_LOG_LOG_ENTITY_H
#define MKI_UTILS_LOG_LOG_ENTITY_H
#include <chrono>
#include <string>

namespace Mki_ms {
enum class LogLevel { TRACE = 0, DEBUG, INFO, WARN, ERROR, FATAL };

const char *LogLevelToString(LogLevel level);

struct LogEntity {
    std::chrono::system_clock::time_point time;
    long threadId = 0;
    LogLevel level = LogLevel::TRACE;
    const char *fileName = nullptr;
    int line = 0;
    const char *funcName = nullptr;
};
} // namespace Mki_ms
#endif
