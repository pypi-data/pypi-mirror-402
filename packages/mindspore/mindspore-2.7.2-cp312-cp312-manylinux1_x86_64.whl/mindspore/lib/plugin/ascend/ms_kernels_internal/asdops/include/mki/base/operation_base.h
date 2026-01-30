/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_BASE_OPERATION_BASE_H
#define MKI_BASE_OPERATION_BASE_H

#include <memory>
#include <set>
#include <string>
#include <vector>
#include <unordered_map>
#include "mki/launch_param.h"
#include "mki/operation.h"

namespace Mki_ms {
class OperationBase : public Operation {
public:
    explicit OperationBase(const std::string &opName) noexcept;
    ~OperationBase() override;
    std::string GetName() const override;
    Status InferShape(LaunchParam &launchParam) const override;

    int64_t GetInputNum(const Any &specificParam) const override;
    int64_t GetOutputNum(const Any &specificParam) const override;
    bool IsConsistent(const LaunchParam &launchParam) const override;

    const KernelList &GetKernelList() const override;
    Kernel *GetKernelByName(const std::string &kernelName) const override;
    bool DynamicRegisterKernelByName(
        const LaunchParam &launchParam, const std::string &kernelName = nullptr) override;
    void AddKernel(const std::string &kernelName, Kernel const *kernel);

protected:
    virtual Status InferShapeImpl(const LaunchParam &launchParam, SVector<Tensor> &outTensors) const = 0;

protected:
    std::string opName_;
    KernelList kernelList_;
    KernelMap kernelMap_;
};
} // namespace Mki_ms

#endif
