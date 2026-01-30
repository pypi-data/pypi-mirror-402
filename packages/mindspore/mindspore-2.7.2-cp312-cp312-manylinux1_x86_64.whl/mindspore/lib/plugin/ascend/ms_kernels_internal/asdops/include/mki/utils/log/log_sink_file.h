/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_LOG_LOG_SINK_FILE_H
#define MKI_UTILS_LOG_LOG_SINK_FILE_H

#include <fstream>
#include <mutex>
#include "mki/utils/log/log_sink.h"

namespace Mki_ms {
class LogSinkFile : public LogSink {
public:
    LogSinkFile();
    ~LogSinkFile() override;
    void Log(const char *log, uint64_t logLen) override;

private:
    LogSinkFile(const LogSinkFile &) = delete;
    const LogSinkFile &operator=(const LogSinkFile &) = delete;
    void Init();
    void OpenFile();
    void DeleteOldestFile();
    std::string GetNewLogFilePath();
    bool IsDiskAvailable();
    void MakeLogDir();
    void CloseFile();
    std::string GetHomeDir();
    bool IsFileNameMatched(const std::string &fileName, std::string &createTime);

private:
    std::string boostType_;
    std::string logDir_;
    bool isFlush_ = false;
    int currentFd_ = -1;
    uint64_t currentFileSize_ = 0;
    std::mutex mutex_;
};
} // namespace Mki_ms
#endif
