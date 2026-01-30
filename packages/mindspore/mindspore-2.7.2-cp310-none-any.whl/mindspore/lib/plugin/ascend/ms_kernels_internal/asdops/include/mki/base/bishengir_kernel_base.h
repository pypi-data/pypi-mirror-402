/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_BISHENGIR_BASE_KERNEL_BASE_H
#define MKI_BISHENGIR_BASE_KERNEL_BASE_H
#include <string>
#include <functional>
#include <map>
#include "mki/kernel.h"
#include "mki/kernel_info.h"
#include "mki/run_info.h"
#include "mki/bin_handle.h"

namespace Mki_ms {
class BishengIRKernelBase : public Kernel {
    using KernelSelfCreator = std::function<BishengIRKernelBase *(void)>;

public:
    BishengIRKernelBase() = delete;
    BishengIRKernelBase(const BishengIRKernelBase &) = delete;
    BishengIRKernelBase &operator=(const BishengIRKernelBase &) = delete;
    BishengIRKernelBase(const std::string &opName, const BinHandle *handle);
    ~BishengIRKernelBase() override;
    Kernel *Clone() const override;
    void Reset() override;

    bool CanSupport(const LaunchParam &launchParam) const override;
    uint64_t GetTilingSize(const LaunchParam &launchParam) const override;
    Status Init(const LaunchParam &launchParam) override;
    Status Run(const LaunchParam &launchParam, RunInfo &runInfo) override;

    void SetLaunchWithTiling(bool flag) override;
    void SetTilingHostAddr(uint8_t *addr, uint64_t len) override;
    std::string GetName() const override;
    const KernelInfo &GetKernelInfo() const override;
    KernelType GetType() const override;
    const uint64_t getNumPtr() const;
    void setStrideInOutput(const uint64_t numPtr);
    const uint64_t getStrideInOutput() const;
    void setStrideTilingWs(const uint64_t numPtr);
    const uint64_t getStrideTilingWs() const;
    Status BuildArgs(const LaunchParam &launchParam, RunInfo &runinfo, void *hostBuffer) override;
    Status RunWithArgs(void *args, void *stream, bool isDeviceAddr) override;

protected:
    virtual Status InitImpl(const LaunchParam &launchParam);
    const BinHandle *GetBinHandle() const;
    void Copy(const BishengIRKernelBase &other);

protected:
    uint32_t launchBufferSize_ = 0;
    KernelInfo kernelInfo_;

private:
    uint64_t GetKernelArgsTotalSize(const LaunchParam &launchParam);
    void UpdateKernelArgsIndex(const LaunchParam &launchParam);

private:
    std::string kernelName_;
    KernelType kernelType_{KernelType::KERNEL_TYPE_INVALID};
    const BinHandle *handle_{nullptr};
    KernelSelfCreator creator_{nullptr};
    friend void SetKernelSelfCreator(BishengIRKernelBase &kernel, KernelSelfCreator func);
    uint64_t numPtr_ = 2;
    uint64_t strideInOutput_ = 5;
    uint64_t strideTilingWs_ = 3;
};

void SetKernelSelfCreator(BishengIRKernelBase &kernel, BishengIRKernelBase::KernelSelfCreator func);
}  // namespace Mki_ms

#endif
