/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_BIN_HANDLE_H
#define MKI_BIN_HANDLE_H
#include <string>
#include <atomic>
#include "mki/tensor.h"

namespace Mki_ms {
using KernelHandle = void *const *;

struct BinaryBasicInfo {
    const uint8_t *binaryBuf = nullptr;
    uint32_t binaryLen = 0;
    std::string targetSoc;
};

struct KernelMetaInfo {
    std::vector<std::string> kernelList;
    std::string compileInfo;
    uint32_t version = 0;
    uint32_t tilingSize = 0;
    uint32_t coreType = 0;
    uint32_t magic = 0;
    uint32_t intercoreSync = 0;
    uint32_t cubeRatio = 0;
    uint32_t vectorRatio = 0;
    const void *codeBuf = nullptr;
    uint32_t codeBufLen = 0;
};

class BinHandle {
public:
    explicit BinHandle(const BinaryBasicInfo *binInfo);
    ~BinHandle();
    BinHandle(const BinHandle &) = delete;
    BinHandle &operator=(const BinHandle &other) = delete;
    KernelHandle GetHandle() const;
    bool Init(const std::string &kernelName);
    uint32_t GetKernelTilingSize() const;
    int32_t GetKernelCoreType() const;
    uint32_t GetIntercoreSync() const;
    uint32_t GetCubeRatio() const;
    uint32_t GetVectorRatio() const;
    const char *GetKernelCompileInfo() const;

private:
    bool CheckBinaryValid() const;
    bool CheckKernelInfo(const std::string &kernelName) const;
    bool RegisterBin(const std::string &kernelName);

private:
    KernelMetaInfo metaInfo_;
    void *handle_ = nullptr;
    void *moduleHandle_ = nullptr;
    BinaryBasicInfo const *const basicInfo_ = nullptr;
    std::atomic_bool codeLoadSuccess_ = false;
};
} // namespace Mki_ms

#endif
