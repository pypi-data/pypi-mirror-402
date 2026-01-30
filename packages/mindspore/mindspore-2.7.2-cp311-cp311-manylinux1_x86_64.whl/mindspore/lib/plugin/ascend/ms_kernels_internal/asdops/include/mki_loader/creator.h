/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_LOADER_CREATOR_H
#define MKI_LOADER_CREATOR_H

#include <string>
#include <vector>
#include <map>
#include "mki/bin_handle.h"
#include "mki/operation.h"

namespace Mki_ms {
using NewOperationFunc = Operation*(*)();
using NewKernelFunc = const Kernel*(*)(const BinHandle *);
using NewAicpuKernelFunc = const Mki_ms::Kernel*(*)();

struct KernelCreatorInfo {
    NewKernelFunc func;
    std::string opName;
    std::string kernelName;
};

struct AicpuKernelCreatorInfo {
    NewAicpuKernelFunc func;
    std::string opName;
    std::string kernelName;
};

using OperationCreators = std::vector<NewOperationFunc>;
using KernelCreators = std::vector<KernelCreatorInfo>;
using AicpuKernelCreators = std::vector<AicpuKernelCreatorInfo>;
using BinaryBasicInfoMap = std::map<std::string, std::vector<BinaryBasicInfo>>;
}

#endif
