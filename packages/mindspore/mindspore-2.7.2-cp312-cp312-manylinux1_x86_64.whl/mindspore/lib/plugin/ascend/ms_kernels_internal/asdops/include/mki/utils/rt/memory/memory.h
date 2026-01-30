/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_RT_MEMORY_MEMORY_H
#define MKI_UTILS_RT_MEMORY_MEMORY_H
#include "mki/utils/rt/base/types.h"
#ifdef __cplusplus
extern "C" {
#endif
namespace Mki_ms {
int MkiRtMemMallocDevice(void **devPtr, uint64_t size, MkiRtMemType memType);
int MkiRtMemFreeDevice(void *devPtr);
int MkiRtMemMallocHost(void **hostPtr, uint64_t size);
int MkiRtMemFreeHost(void *hostPtr);
int MkiRtMemCopy(void *dstPtr, uint64_t dstLen, const void *srcPtr, uint64_t srcLen, MkiRtMemCopyType copyType);
int MkiRtMemCopyAsync(void *dstPtr, uint64_t dstLen, const void *srcPtr, uint64_t srcLen, MkiRtMemCopyType copyType,
                      void *stream);
int MkiRtMemSetAsync(void *dstPtr, uint64_t destMax, uint32_t value, uint64_t count, void *stream);
int MkiRtIpcSetMemoryName(const void *ptr, uint64_t byteCount, const char *name, uint32_t len);
int MkiRtIpcOpenMemory(void **ptr, const char *name);
int MkiRtSetIpcMemPid(const char *name, int32_t pid[], int num);
}
#ifdef __cplusplus
}
#endif
#endif
