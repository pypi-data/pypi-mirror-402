/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_LOG_LOG_CORE_H
#define MKI_UTILS_LOG_LOG_CORE_H
#include <memory>
#include <vector>
#include "mki/utils/log/log_entity.h"
#include "mki/utils/log/log_sink.h"
#include "mki/utils/SVector/SVector.h"

namespace Mki_ms {
class LogCore {
public:
    LogCore();
    virtual ~LogCore() = default;
    static LogCore &Instance();
    LogLevel GetLogLevel() const;
    void SetLogLevel(LogLevel level);
    void Log(const char *log, uint64_t logLen);
    void DeleteLogFileSink();
    void AddSink(std::shared_ptr<LogSink> sink);
    const std::vector<std::shared_ptr<LogSink>> &GetAllSinks() const;

private:
    std::vector<std::shared_ptr<LogSink>> sinks_;
    LogLevel level_ = LogLevel::INFO;
};
} // namespace Mki_ms
#endif
