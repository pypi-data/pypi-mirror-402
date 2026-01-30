/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_OPERATION_H
#define MKI_OPERATION_H

#include <string>
#include <vector>
#include <unordered_map>
#include "mki/launch_param.h"
#include "mki/kernel.h"
#include "mki/utils/any/any.h"
#include "mki/utils/status/status.h"

namespace Mki_ms {
using KernelList = std::vector<Kernel const *>;
using KernelMap = std::unordered_map<std::string, Kernel const *>;
class Operation {
public:
    Operation() = default;
    virtual ~Operation() = default;
    virtual std::string GetName() const = 0;
    virtual Status InferShape(LaunchParam &launchParam) const = 0;

    virtual int64_t GetInputNum(const Any &specificParam) const = 0;
    virtual int64_t GetOutputNum(const Any &specificParam) const = 0;
    virtual bool IsConsistent(const LaunchParam &launchParam) const = 0;

    virtual const KernelList &GetKernelList() const = 0;
    virtual Kernel *GetBestKernel(const LaunchParam &launchParam) const = 0;
    virtual Kernel *GetKernelByName(const std::string &kernelName) const = 0;
    virtual bool DynamicRegisterKernelByName(
        const LaunchParam &launchParam, const std::string &kernelName = nullptr) = 0;
};
} // namespace Mki_ms

#endif
