/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_RT_DEVICE_DEVICE_H
#define MKI_UTILS_RT_DEVICE_DEVICE_H
#include "mki/utils/rt/base/types.h"

#ifdef __cplusplus
extern "C" {
#endif
namespace Mki_ms {
int MkiRtDeviceGetCount(int32_t *devCount);
int MkiRtDeviceGetIds(int32_t *devIds, int32_t devIdNum);
int MkiRtDeviceGetCurrent(int32_t *devId);
int MkiRtDeviceSetCurrent(int32_t devId);
int MkiRtDeviceResetCurrent(int32_t devId);
int MkiRtDeviceSetSocVersion(const char *version);
int MkiRtDeviceGetSocVersion(std::string &version, uint32_t maxLen);
int MkiRtDeviceGetBareTgid(uint32_t *pid);
int MkiRtDeviceGetPairDevicesInfo(uint32_t devId, uint32_t otherDevId, int32_t infoType, int64_t *val);
}
#ifdef __cplusplus
}
#endif
#endif
