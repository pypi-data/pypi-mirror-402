/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_RT_BACKEND_HELP_MACRO_H
#define MKI_UTILS_RT_BACKEND_HELP_MACRO_H

#define CHECK_FUNC_EIXST_RETURN(func)                                                                              \
    if ((func) == nullptr) {                                                                                       \
        return MKIRT_ERROR_FUNC_NOT_EXIST;                                                                         \
    }

#define CHECK_STATUS_RETURN(fun)                                                                                   \
    do {                                                                                                           \
        int ret = (fun);                                                                                           \
        if (ret == 0) {                                                                                            \
            return MKIRT_SUCCESS;                                                                                  \
        } else {                                                                                                   \
            return ret;                                                                                            \
        }                                                                                                          \
    } while (0)

#define CHECK_STATUS_WITH_DESC_RETURN(ret, funcName)                                                               \
    if ((ret) == 0) {                                                                                              \
        MKI_LOG(DEBUG) << (funcName) << " success";                                                                \
        return MKIRT_SUCCESS;                                                                                      \
    } else {                                                                                                       \
        MKI_LOG(ERROR) << (funcName) << " fail, error:" << (ret);                                                  \
        return ret;                                                                                                \
    }

#define CHECK_INITED_RETURN(ret)                                                                                   \
    if ((ret) != MKIRT_SUCCESS) {                                                                                  \
        return ret;                                                                                                \
    }

#define CHECK_FUN_PARA_RETURN(para)                                                                                \
    if ((para) == nullptr) {                                                                                       \
        return MKIRT_ERROR_PARA_CHECK_FAIL;                                                                        \
    }

#endif
