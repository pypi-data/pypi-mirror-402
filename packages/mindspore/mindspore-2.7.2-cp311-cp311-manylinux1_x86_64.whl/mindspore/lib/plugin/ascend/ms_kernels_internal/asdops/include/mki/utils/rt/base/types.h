/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_RT_BASE_TYPES_H
#define MKI_UTILS_RT_BASE_TYPES_H
#include <cstdint>
#include <string>

#ifdef __cplusplus
extern "C" {
#endif

typedef void *MkiDevice;
typedef void *MkiRtStream;

enum MkiRtDevBinaryMagic : uint32_t {
    MKIRT_DEV_BINARY_MAGIC_ELF = 0x43554245U,
    MKIRT_DEV_BINARY_MAGIC_ELF_AIVEC = 0x41415246U,
    MKIRT_DEV_BINARY_MAGIC_ELF_AICUBE = 0x41494343U,
};

typedef enum {
    MKIRT_SUCCESS = 0,
    MKIRT_ERROR_NOT_INITIALIZED = -1,
    MKIRT_ERROR_NOT_IMPLMENT = -2,
    MKIRT_ERROR_ASCEND_ENV_NOT_EXIST = -3,
    MKIRT_ERROR_LOAD_RUNTIME_FAIL = -4,
    MKIRT_ERROR_FUNC_NOT_EXIST = -5,
    MKIRT_ERROR_OPEN_BIN_FILE_FAIL = -6,
    MKIRT_ERROR_PARA_CHECK_FAIL = -7,
} MkiRtError;

typedef enum {
    MKIRT_MEMCOPY_HOST_TO_HOST = 0,
    MKIRT_MEMCOPY_HOST_TO_DEVICE,
    MKIRT_MEMCOPY_DEVICE_TO_HOST,
    MKIRT_MEMCOPY_DEVICE_TO_DEVICE, // device to device, 1P &P2P
    MKIRT_MEMCOPY_MANAGED,
    MKIRT_MEMCOPY_ADDR_DEVICE_TO_DEVICE,
    MKIRT_MEMCOPY_HOST_TO_DEVICE_EX, // host to device ex(only used for 8 bytes)
    MKIRT_MEMCOPY_DEVICE_TO_HOST_EX, // device to host ex
} MkiRtMemCopyType;

typedef enum {
    MKIRT_MEM_DEFAULT = 0,    // default memeory on device
    MKIRT_MEM_HBM = 0x2,      // HBM memory on device
    MKIRT_MEM_RDMA_HBM = 0x3, // RDMA-HBM memory on device
    MKIRT_MEM_DDR = 0x4,      // DDR memory on device
    MKIRT_MEM_SPM = 0x8,      // shaed physical memory on device
    MKIRT_MEM_P2P_HBM = 0x10, // HBM memory on other 4p device
    MKIRT_MEM_P2P_DDR = 0x11, // DDR memory on other device
    MKIRT_MEM_DDR_NC = 0x20,  // DDR memory of non-cache
    MKIRT_MEM_TS_4G = 0x40,
    MKIRT_MEM_TS = 0x80,
    MKIRT_MEM_HOST = 0x81, // memory on host
    MKIRT_MEM_RESERVED = 0x100,
    MKIRT_MEM_L1 = (0x1 << 16),
    MKIRT_MEM_L2 = (0x1 << 17),
} MkiRtMemType;

typedef void *MkiRtModule;

typedef enum {
    MKIRT_MODULE_OBJECT = 0, // 原始object文件
    MKIRT_MODULE_BIN = 1,    // bin头 + 连续原始object
    MKIRT_MODULE_FUSEIO_BIN  // fusionbin头 + 连续的bin
} MkiRtModuleType;

typedef struct {
    MkiRtModuleType type = MKIRT_MODULE_OBJECT;
    uint32_t version = 0;
    const void *data = nullptr;
    uint64_t dataLen = 0;
    uint32_t magic = MKIRT_DEV_BINARY_MAGIC_ELF_AICUBE;
} MkiRtModuleInfo;

typedef struct {
    uint32_t addrOffset{0};
    uint32_t dataOffset{0};
} RtHostInputInfoT;

typedef struct {
    void *args{nullptr};
    RtHostInputInfoT *hostInputInfoPtr{nullptr};
    uint32_t argsSize{0};
    uint32_t tilingAddrOffset{0};
    uint32_t tilingDataOffset{0};
    uint16_t hostInputInfoNum{0};
    uint8_t hasTiling{0};
    uint8_t isNoNeedH2DCopy{0};
    uint8_t reserved[4] = {0};
} RtArgsExT;

#pragma pack(push, 1)

typedef struct {
    uint8_t *kernelSoBuf;        // the starting address of custom operator so buf
    uint32_t kernelSoBufLen;     // the length of custom operator so buf
    uint8_t *kernelSoName;       // the starting address of custom operator so name
    uint32_t kernelSoNameLen;    // the length of custom operator so name
} RtLoadOpFromBufArgs;

typedef struct  {
    uint32_t soNum;
    uint64_t args;
} RtBatchLoadOpFromBufArgs;

#pragma pack(pop)

typedef struct {
    const char *soName;      // defined for so name
    const char *kernelName;  // defined for kernel type name
    const char *opName;      // defined for operator name
} RtKernelLaunchNamesT;

typedef struct {
    void *args{nullptr}; // args host mem addr
    RtHostInputInfoT *hostInputInfoPtr{nullptr}; // nullptr means no host mem input
    RtHostInputInfoT *kernelOffsetInfoPtr{nullptr}; // KernelOffsetInfo, it is different for CCE Kernel and fwk kernel
    uint32_t argsSize{0};
    uint16_t hostInputInfoNum{0}; // hostInputInfo num
    uint16_t kernelOffsetInfoNum{0}; // KernelOffsetInfo num
    uint32_t soNameAddrOffset{0}; // just for CCE Kernel, default value is 0xffff for FWK kernel
    uint32_t kernelNameAddrOffset{0}; // just for CCE Kernel, default value is 0xffff for FWK kernel
    bool isNoNeedH2DCopy{0}; // is no need host to device copy: 0 means need H2D copy,
                               // other means doesn't need H2D copy.
    uint8_t reserved[3] = {0};
} RtAicpuArgsExT;

typedef struct {
    uint8_t qos{0};
    uint8_t partId{0};
    uint8_t schemMode{0};
    uint8_t res[1] = {0};
} RtTaskCfgInfoT;

typedef struct {
    uint64_t tilingId = 0;
    uint32_t blockDim = 0;
    void *args = nullptr;
    uint32_t argSize = 0;
    RtArgsExT *argsEx = nullptr;
} MkiRtKernelParam;

typedef struct {
    uint32_t blockDim = 0;
    void *args = nullptr;
    uint32_t argSize = 0;
    RtArgsExT *argsEx = nullptr;
    RtAicpuArgsExT *aicpuArgsEx = nullptr;
} MkiRtAicpuKernelParam;

#ifdef __cplusplus
}
#endif
#endif
