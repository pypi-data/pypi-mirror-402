/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_DL_DL_H
#define MKI_UTILS_DL_DL_H
#include <string>
#include <atomic>

namespace Mki_ms {
class Dl {
public:
    explicit Dl(const std::string &dlFilePath, bool checkSymlinks = true);
    ~Dl();
    Dl(const Dl &) = delete;
    Dl &operator=(const Dl &) = delete;
    void *GetSymbol(const std::string &symbolName) const;
    bool IsValid() const;
private:
    std::string GetNewMemFdFileName() const;
    std::atomic_bool dlSuccess_{false};
private:
    int memFd_ = 0;
    void *dlHandle_ = nullptr;
};
} // namespace Mki_ms
#endif
