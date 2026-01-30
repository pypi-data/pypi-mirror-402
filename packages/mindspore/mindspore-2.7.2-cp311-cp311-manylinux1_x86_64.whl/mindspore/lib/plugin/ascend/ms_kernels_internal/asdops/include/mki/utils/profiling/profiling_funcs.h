/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef PROFILING_FUNCS_H
#define PROFILING_FUNCS_H

#include <mutex>
#include <unordered_map>
#include "prof_api.h"

namespace Mki_ms {
class ProfilingFuncs {
public:
    ProfilingFuncs() noexcept;
    ~ProfilingFuncs();
    int32_t ProfReportApi(uint32_t agingFlag, const MsProfApi *api) const;
    int32_t ProfReportCompactInfo(uint32_t agingFlag, const void *data, uint32_t length) const;
    int32_t ProfReportTypeInfo(uint16_t level, uint32_t typeId, std::string typeName) const;
    int32_t ProfReportAdditionalInfo(uint32_t agingFlag, const void *data, uint32_t length) const;
    uint64_t ProfSysCycleTime() const;
    uint64_t ProfGetHashId(const char *hashInfo, size_t length) const;
    uint64_t ProfGetHashId(const char *hashInfo, size_t length, void const *key);
    void SetProfilingLevel0Status(bool status) const;
    void SetProfilingLevel1Status(bool status) const;
    bool GetProfilingLevel0Status() const;
    bool GetProfilingLevel1Status() const;
    static int32_t MkiProfCommandHandle(uint32_t type, void *data, uint32_t len);

private:
    std::unordered_map<void const *, uint64_t> kernelNameHashCache_;
    static bool isProfilingLevel0Enable_;
    static bool isProfilingLevel1Enable_;
};
} // namespace Mki_ms
#endif
