/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_RT_STREAM_STREAM_H
#define MKI_UTILS_RT_STREAM_STREAM_H
#include "mki/utils/rt/base/types.h"

#ifdef __cplusplus
extern "C" {
#endif
namespace Mki_ms {
int MkiRtStreamCreate(MkiRtStream *stream, int32_t priority = 0);
int MkiRtStreamDestroy(MkiRtStream stream);
int MkiRtStreamSynchronize(MkiRtStream stream);
int MkiRtStreamGetId(MkiRtStream stream, int32_t *streamId);
}
#ifdef __cplusplus
}
#endif
#endif
