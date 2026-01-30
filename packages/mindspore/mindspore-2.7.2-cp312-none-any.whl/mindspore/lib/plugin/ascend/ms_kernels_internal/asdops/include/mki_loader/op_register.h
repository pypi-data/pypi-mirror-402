/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_LOADER_OP_REGISTER_H
#define MKI_LOADER_OP_REGISTER_H

#include <map>
#include <vector>
#include "mki/base/kernel_base.h"
#include "mki/base/aicpu_kernel_base.h"
#include "mki/base/operation_base.h"
#include "mki/utils/assert/assert.h"
#include "mki/utils/log/log.h"
#include "mki_loader/op_schedule_base.h"

#define MACRO_TO_STR_INTERNAL(name) #name
#define MACRO_TO_STR(name) MACRO_TO_STR_INTERNAL(name)
#define MKI_NAMESPACE_LOG(level, spaceName) MKI_LOG(level) << (MACRO_TO_STR_INTERNAL(spaceName))

namespace OpSpace {
using namespace Mki_ms;
class OperationRegister {
public:
    OperationRegister(const char *opName, NewOperationFunc func) noexcept
    {
        MKI_CHECK(opName != nullptr, "opName is nullptr", return);
        auto &operationCreators = GetOperationCreators();
        operationCreators.push_back(func);
        MKI_NAMESPACE_LOG(DEBUG, OpSpace) << " register operation " << opName;
    }

    static OperationCreators &GetOperationCreators()
    {
        static OperationCreators operationCreators;
        return operationCreators;
    }
};

class KernelRegister {
public:
    KernelRegister(const char *opName, const char *kerName, NewKernelFunc func) noexcept
    {
        MKI_CHECK(opName != nullptr, "opName is nullptr", return);
        MKI_CHECK(kerName != nullptr, "kerName is nullptr", return);
        auto &kernelCreators = GetKernelCreators();
        kernelCreators.push_back({ func, opName, kerName });
        MKI_NAMESPACE_LOG(DEBUG, OpSpace) << " register kernel " << kerName << " of operation " << opName;
    }

    static KernelCreators &GetKernelCreators()
    {
        static KernelCreators kernelCreators;
        return kernelCreators;
    }
};

class AicpuKernelRegister {
public:
    AicpuKernelRegister(const char *opName, const char *kerName, NewAicpuKernelFunc func) noexcept
    {
        MKI_CHECK(opName != nullptr, "opName is nullptr", return);
        MKI_CHECK(kerName != nullptr, "kerName is nullptr", return);
        auto &kernelCreators = GetKernelCreators();
        kernelCreators.push_back({ func, opName, kerName });
        MKI_NAMESPACE_LOG(DEBUG, OpSpace) << " register aicpu kernel " << kerName << " of operation " << opName;
    }

    static AicpuKernelCreators &GetKernelCreators()
    {
        static AicpuKernelCreators kernelCreators;
        return kernelCreators;
    }
};

class KernelBinaryRegister {
public:
    KernelBinaryRegister(const char *soc, const char *kernelName, const uint8_t *binary, uint32_t binaryLen) noexcept
    {
        MKI_CHECK(kernelName != nullptr, "kernelName is nullptr", return);
        MKI_CHECK(soc != nullptr, "target soc is nullptr", return);
        MKI_CHECK(binary != nullptr, "binary addr is nullptr", return);
        auto &binaryMap = GetKernelBinaryMap();
        binaryMap[std::string(kernelName)].push_back({ binary, binaryLen, soc });
        MKI_NAMESPACE_LOG(DEBUG, OpSpace) << " register kernel binary " << kernelName << "-" << soc << " success";
    }

    static BinaryBasicInfoMap &GetKernelBinaryMap()
    {
        static BinaryBasicInfoMap binaryMap;
        return binaryMap;
    }
};

class OpSchedule final : public Mki_ms::OpScheduleBase {
public:
    OpSchedule()
    {
        AddAllOperations(OperationRegister::GetOperationCreators(),
            KernelRegister::GetKernelCreators(),
            AicpuKernelRegister::GetKernelCreators(),
            KernelBinaryRegister::GetKernelBinaryMap());
    }
    void UpdateLoader() override
    {
        UpdateLoaderBinary(OperationRegister::GetOperationCreators(),
            KernelRegister::GetKernelCreators(),
            AicpuKernelRegister::GetKernelCreators(),
            KernelBinaryRegister::GetKernelBinaryMap());
    }
    ~OpSchedule() override {}
};

#define REG_OPERATION(opName)                                                                                       \
    Mki_ms::Operation *GetOperation##opName()                                                                          \
    {                                                                                                               \
        static opName op##opName(#opName);                                                                          \
        return &op##opName;                                                                                         \
    }                                                                                                               \
    static OperationRegister op##opName##register = OperationRegister(#opName, GetOperation##opName)

#define REG_KERNEL_BASE(kerName)                                                                                    \
    Mki_ms::Kernel const *GetKernel##kerName(const Mki_ms::BinHandle *binHandle)                                          \
    {                                                                                                               \
        static kerName ker##kerName(#kerName, binHandle);                                                           \
        SetKernelSelfCreator(ker##kerName, [=](){ return new (std::nothrow) kerName(#kerName, binHandle); });       \
        return &ker##kerName;                                                                                       \
    }                                                                                                               \
    static KernelRegister ker##kerName##register = KernelRegister(OperationPlaceHolder, #kerName, GetKernel##kerName)

#define REG_AICPU_KERNEL_BASE(kerName)                                                                             \
    Mki_ms::Kernel const *GetAicpuKernel##kerName()                                                                   \
    {                                                                                                              \
        static std::string aicpuKernelName = MACRO_TO_STR(kerName##AicpuKernelPlaceHolder);                        \
        static kerName ker##kerName(#kerName, aicpuKernelName.c_str());                                            \
        SetAicpuKernelSelfCreator(ker##kerName, [=](){ return new kerName(#kerName, aicpuKernelName.c_str()); });  \
        return &ker##kerName;                                                                                      \
    }                                                                                                              \
    static AicpuKernelRegister ker##kerName##register =                                                            \
        AicpuKernelRegister(OperationPlaceHolder, #kerName, GetAicpuKernel##kerName)

#define REG_KERNEL(soc, kerName, binary)                                                                           \
    static KernelBinaryRegister bin##kerName##soc##register =                                                      \
           KernelBinaryRegister(#soc, #kerName, binary, sizeof(binary))
} // namespace OpSpace

#endif
