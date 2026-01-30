/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_LOADER_OP_SCHEDULE_H
#define MKI_LOADER_OP_SCHEDULE_H
#include <vector>
#include <string>
#include <unordered_map>
#include <memory>
#include "mki/run_info.h"
#include "mki/operation.h"
#include "mki_loader/creator.h"

namespace Mki_ms {
class Loader;
class OpScheduleBase {
public:
    OpScheduleBase(const OpScheduleBase&) = delete;
    OpScheduleBase& operator=(const OpScheduleBase&) = delete;
    OpScheduleBase();
    virtual ~OpScheduleBase();
    std::vector<Operation *> GetAllOperations() const;
    Operation *GetOperationByName(const std::string &opName) const;
    Kernel *GetKernelInstance(const std::string &kernelName) const;
    virtual void UpdateLoader();

protected:
    void AddAllOperations(const OperationCreators &opCreators, const KernelCreators &kerCreators,
        const AicpuKernelCreators &aicpuKerCreators, const BinaryBasicInfoMap &binMap);
    void UpdateLoaderBinary(const OperationCreators &opCreators, const KernelCreators &kerCreators,
        const AicpuKernelCreators &aicpuKerCreators, const BinaryBasicInfoMap &binMap);

private:
    void AddOperationByName(Operation *op);
    void AddOperationKernels(const Operation *op);
    void AddKernel(Kernel const *kernel);

private:
    std::unique_ptr<Loader> loader_;
    std::unordered_map<std::string, Mki_ms::Operation *> opMap_;
    KernelMap kernelMap_;
};
} // namespace Mki_ms

#endif
