/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_STATUS_STATUS_H
#define MKI_UTILS_STATUS_STATUS_H
#include <string>

namespace Mki_ms {
class Status {
public:
    Status() noexcept;
    ~Status();
    Status(const Status &other);
    Status &operator=(const Status &other);
    Status(Status &&other) noexcept;
    Status &operator=(Status &&other);
    bool Ok() const;
    std::string ToString() const;
    int Code() const;
    std::string Message() const;

public:
    static Status OkStatus();
    static Status FailStatus(int code, const std::string &msg = "");

private:
    Status(int code, const std::string &msg);
    int GetLen() const;
    int GetCode() const;
    const char *GetMsg() const;
    void RemoveMsg();

private:
    uint8_t *rep_{nullptr};
};

#define OP_TILING_CHECK_STATUS_RETURN(ret)                                                                         \
    do {                                                                                                           \
        if (!(ret).Ok()) {                                                                                         \
            MKI_LOG_ERROR << (ret).ToString();                                                                     \
            return ret;                                                                                            \
        }                                                                                                          \
    } while (0)

#define OP_TILING_CHECK_STATUS_RETURN_VOID(ret)                                                                    \
    do {                                                                                                           \
        if (!(ret).Ok()) {                                                                                         \
            MKI_LOG_ERROR << (ret).ToString();                                                                     \
            return;                                                                                                \
        }                                                                                                          \
    } while (0)
} // namespace Mki_ms
#endif
