/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_KERNEL_INFO_H
#define MKI_KERNEL_INFO_H

#include <cstdint>
#include "mki/utils/status/status.h"
#include "mki/utils/SVector/SVector.h"

namespace Mki_ms {
class KernelInfo {
public:
struct ConstTensorInfo {
    uint64_t argIdx = 0;
    uint64_t size = 0;
};

struct TilingExtInfo {
    uint32_t blockDim = 0;
    uint64_t tilingId = 0;
    uint64_t constTensorOffset = 0; // const tensor offset in host tiling
    uint64_t usedSize = 0; // actual tiling size used
    uint8_t *hostTilingAddr = nullptr;
    uint64_t hostTilingSize = 0;
};

struct MemsetInfo {
    uint64_t argIdx = 0;
    uint64_t size = 0;
};

public:
    KernelInfo() = default;
    ~KernelInfo();
    KernelInfo(const KernelInfo &) = delete;
    KernelInfo &operator=(const KernelInfo &other) = delete;
    void Copy(const KernelInfo &other);
    std::string ToString() const;

public:
    void Reset();
    // Args
    Status InitArgs(uint64_t len);
    uint8_t *GetArgs() const;
    uint64_t GetArgsSize() const;

    // Hwsync
    void SetHwsyncIdx(int64_t idx);
    int64_t GetHwsyncIdx() const;

    // TilingExtInfo - BlockDim / TilingId
    void SetBlockDim(uint32_t blockDim);
    uint32_t GetBlockDim() const;
    void SetTilingId(uint64_t tilingId);
    uint64_t GetTilingId() const;

    // TilingExtInfo - TilingHost
    Status AllocTilingHost(uint64_t len);
    void SetTilingHostAddr(uint8_t *addr, uint64_t len);
    uint8_t *GetTilingHostAddr() const;
    uint64_t GetTilingSize() const;

    void SetTilingUsedSize(uint64_t usedSize);
    uint64_t GetTilingUsedSize() const;

    // TilingExtInfo - ConstTensorOffset
    void SetConstTensorOffset(uint64_t offset);
    uint64_t GetConstTensorOffset() const;

    // ConstTensor
    template <typename T_SRC, typename T_DST = T_SRC, typename T_CONT = SVector<T_SRC>>
    bool AddConstTensorData(uint64_t argIdx, const T_CONT &tensorData);

    size_t GetConstTensorCount() const;
    const ConstTensorInfo &GetConstTensorInfo(size_t id) const;
    const MiniVector<ConstTensorInfo> &GetConstTensorInfos() const;

    // LaunchWithTiling
    void SetLaunchWithTiling(bool flag);
    bool GetLaunchWithTiling() const;

    // Scratch
    MiniVector<uint64_t> &GetScratchSizes();
    const MiniVector<uint64_t> &GetScratchSizes() const;
    uint64_t GetTotalScratchSize() const;

    // Memset
    void SetMemsetInfo(uint64_t argIdx, uint64_t size);
    const MiniVector<KernelInfo::MemsetInfo> &GetMemsetInfo() const;

    // BishengIR kernel args index
    void SetKernelArgsIndex(const MiniVector<uint64_t>& index);
    const MiniVector<uint64_t>& GetKernelArgsIndex() const;
    MiniVector<uint64_t>& GetKernelArgsIndex();

private:
    void ResetArgs();
    void ResetTilingInfo();
    void ResetConstTensorInfo();
    void ResetScratchSizes();
    void ResetMemsetInfo();

private:
    uint8_t *args_ = nullptr;
    uint64_t argsSize_ = 0;
    bool initFlag_{false};  // kernel info 线程间不共享
    bool launchWithTiling_{true};
    int64_t hwsyncIdx_ = -1; // < 0: no hwsync, >= 0: hwsync arg idx
    TilingExtInfo tilingExtInfo_;
    MiniVector<ConstTensorInfo> constTensorInfo_;
    MiniVector<uint64_t> scratchSizes_;
    MiniVector<MemsetInfo> memsetInfo_;
    MiniVector<uint64_t> kernelArgsIndex_;
};
} // namespace Mki_ms

#endif
