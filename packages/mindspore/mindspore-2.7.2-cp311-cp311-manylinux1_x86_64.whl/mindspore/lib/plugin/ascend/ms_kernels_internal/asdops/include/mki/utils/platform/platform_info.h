/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_PLATFORM_PLATFORM_INFO_H
#define MKI_UTILS_PLATFORM_PLATFORM_INFO_H

#include <string>
#include <unordered_map>
#include "mki/utils/platform/platform_manager.h"

namespace Mki_ms {
enum class PlatformType {
    ASCEND_310P = 0,
    ASCEND_910A,
    ASCEND_910B,
    ASCEND_310B,
    PLATFORM_INVALID,
};

enum class CoreType : int {
    CORE_TYPE_VECTOR = 0,
    CORE_TYPE_CUBE = 1,
};

class PlatformInfo {
public:
    static PlatformInfo &Instance();

    uint32_t GetCoreNum(CoreType type);

    uint64_t GetL2Size();
    uint64_t GetL1Size();
    uint64_t GetL0ASize();
    uint64_t GetL0BSize();
    uint64_t GetL0CSize();
    uint64_t GetUbSize();

    bool SupportL0c2out();

    PlatformType GetPlatformType() const;
    std::string GetPlatformName() const;

private:
    PlatformInfo();

    void Init();
    bool Inited() const;

    bool GetAicoreIntrinsic(const std::string &intrinsicName);

    bool inited_ = false;

    // platform
    PlatformType platformType_ = PlatformType::PLATFORM_INVALID;
    std::string platformName_;

    PlatformConfigs platformConfigs_;
};
} // namespace Mki_ms

#endif
