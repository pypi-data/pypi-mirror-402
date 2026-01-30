/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_PLATFORM_PLATFORM_MANAGER_H
#define MKI_UTILS_PLATFORM_PLATFORM_MANAGER_H

#include <map>
#include <string>
#include "platform_configs.h"

namespace Mki_ms {

const uint32_t PLATFORM_FAILED = 0XFFFFFFFF;
const uint32_t PLATFORM_SUCCESS = 0;

class PlatformManager {
using PlatMapType = std::map<std::string, std::string>;

public:
    PlatformManager(const PlatformManager &) = delete;
    PlatformManager &operator=(const PlatformManager &) = delete;

    static PlatformManager &Instance();
    uint32_t InitializePlatformManager();
    uint32_t Finalize();

    uint32_t GetPlatformConfigs(const std::string socVersion, PlatformConfigs &platformConfigs);

private:
    PlatformManager();
    ~PlatformManager();

    uint32_t LoadConfigFile(std::string filePath);
    uint32_t LoadIniFile(std::string iniFileRealPath);

    void ParseVersion(PlatMapType &versionMap, std::string &socVersion) const;
    void ParsePlatformSpec(const std::string &label, PlatMapType &platformSpecMap,
                          PlatformConfigs &platformConfigsTemp) const;
    uint32_t ParsePlatformInfo(std::map<std::string, PlatMapType> &contentMap,
                               std::string &socVersion, PlatformConfigs &platformConfigsTemp) const;
    bool ParseAICoreintrinsicDtypeMap(PlatMapType &aiCoreintrinsicDtypeMap,
                                      PlatformConfigs &platformConfigsTemp) const;
    bool ParseVectorCoreintrinsicDtypeMap(PlatMapType &vectorCoreintrinsicDtypeMap,
                                          PlatformConfigs &platformConfigsTemp) const;

    uint32_t AssemblePlatformInfoVector(std::map<std::string, PlatMapType> &contentMap);
    void FillupFixPipeInfo(PlatformConfigs &platformConfigs) const;

private:
    bool initFlag_;
    std::map<std::string, PlatformConfigs> platformConfigsMap_;
};
} // namespace Mki_ms

#endif
