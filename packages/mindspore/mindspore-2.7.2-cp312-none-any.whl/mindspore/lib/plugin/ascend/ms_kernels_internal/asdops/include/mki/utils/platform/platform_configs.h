/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_PLATFORM_PLATFORM_CONFIGS_H
#define MKI_UTILS_PLATFORM_PLATFORM_CONFIGS_H

#include <map>
#include <string>
#include <vector>

namespace Mki_ms {
enum class LocalMemType {
    L0_A = 0,
    L0_B = 1,
    L0_C = 2,
    L1 = 3,
    L2 = 4,
    UB = 5,
    HBM = 6,
    RESERVED
};

class PlatformConfigs {
using PlatInfoMapType = std::map<std::string, std::vector<std::string>>;
using PlatSpecMapType = std::map<std::string, std::map<std::string, std::string>>;

public:
    void SetPlatformSpec(const std::string &label, std::map<std::string, std::string> &res);
    bool GetPlatformSpec(const std::string &label, const std::string &key, std::string &value);
    bool GetPlatformSpec(const std::string &label, std::map<std::string, std::string> &res);

    uint32_t GetCoreNumByType(const std::string &coreType);
    void GetLocalMemSize(const LocalMemType &memType, uint64_t &size);

    void SetFixPipeDtypeMap(const PlatInfoMapType &fixpipeDtypeMap);
    void SetAICoreIntrinsicDtype(PlatInfoMapType &intrinsicDtypes);
    void SetVectorCoreIntrinsicDtype(PlatInfoMapType &intrinsicDtypes);
    const PlatInfoMapType &GetFixPipeDtypeMap();
    PlatInfoMapType &GetAICoreIntrinsicDtype();
    PlatInfoMapType &GetVectorCoreIntrinsicDtype();
    const PlatSpecMapType &GetPlatformSpecMap();

private:
    PlatInfoMapType fixpipeDtypeMap_;
    PlatInfoMapType aiCoreIntrinsicDtypeMap_;
    PlatInfoMapType vectorCoreIntrinsicDtypeMap_;
    PlatSpecMapType platformSpecMap_;
};
} // namespace Mki_ms

#endif