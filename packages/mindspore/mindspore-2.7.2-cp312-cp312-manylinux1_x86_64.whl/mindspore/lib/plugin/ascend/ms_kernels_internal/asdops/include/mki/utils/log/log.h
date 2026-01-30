/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_LOG_LOG_H
#define MKI_UTILS_LOG_LOG_H
#include "mki/utils/log/log_stream.h"
#include "mki/utils/log/log_core.h"
#include "mki/utils/log/log_sink.h"
#include "mki/utils/log/log_entity.h"

#define MKI_LOG(level) MKI_LOG_##level

#define MKI_FLOG(level, format, ...) MKI_FLOG_##level(format, ##__VA_ARGS__)

#define MKI_LOG_IF(condition, level)                                                                             \
    if (condition)                                                                                               \
    MKI_LOG(level)

#define MKI_LOG_TRACE                                                                                            \
    if (Mki_ms::LogLevel::TRACE >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::TRACE)
#define MKI_LOG_DEBUG                                                                                            \
    if (Mki_ms::LogLevel::DEBUG >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::DEBUG)
#define MKI_LOG_INFO                                                                                             \
    if (Mki_ms::LogLevel::INFO >= Mki_ms::LogCore::Instance().GetLogLevel())                                           \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::INFO)
#define MKI_LOG_WARN                                                                                             \
    if (Mki_ms::LogLevel::WARN >= Mki_ms::LogCore::Instance().GetLogLevel())                                           \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::WARN)
#define MKI_LOG_ERROR                                                                                            \
    if (Mki_ms::LogLevel::ERROR >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::ERROR)
#define MKI_LOG_FATAL                                                                                            \
    if (Mki_ms::LogLevel::FATAL >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::FATAL)

#define MKI_FLOG_TRACE(format, ...)                                                                              \
    if (Mki_ms::LogLevel::TRACE >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::TRACE).Format(format, ##__VA_ARGS__)
#define MKI_FLOG_DEBUG(format, ...)                                                                              \
    if (Mki_ms::LogLevel::DEBUG >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::DEBUG).Format(format, ##__VA_ARGS__)
#define MKI_FLOG_INFO(format, ...)                                                                               \
    if (Mki_ms::LogLevel::INFO >= Mki_ms::LogCore::Instance().GetLogLevel())                                           \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::INFO).Format(format, ##__VA_ARGS__)
#define MKI_FLOG_WARN(format, ...)                                                                               \
    if (Mki_ms::LogLevel::WARN >= Mki_ms::LogCore::Instance().GetLogLevel())                                           \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::WARN).Format(format, ##__VA_ARGS__)
#define MKI_FLOG_ERROR(format, ...)                                                                              \
    if (Mki_ms::LogLevel::ERROR >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::ERROR).Format(format, ##__VA_ARGS__)
#define MKI_FLOG_FATAL(format, ...)                                                                              \
    if (Mki_ms::LogLevel::FATAL >= Mki_ms::LogCore::Instance().GetLogLevel())                                          \
    Mki_ms::LogStream(__FILE__, __LINE__, __FUNCTION__, Mki_ms::LogLevel::FATAL).Format(format, ##__VA_ARGS__)

#endif
