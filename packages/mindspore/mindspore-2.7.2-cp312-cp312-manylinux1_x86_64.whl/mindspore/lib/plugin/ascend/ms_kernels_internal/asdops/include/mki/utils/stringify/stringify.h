/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_STRINGIFY_H
#define MKI_STRINGIFY_H

#include <functional>
#include <map>
#include <string>
#include "mki/utils/any/any.h"

namespace Mki_ms {
using StringifyFunc = std::function<std::string(const Any &)>;

class Stringify {
public:
    Stringify(size_t typeHashCode, StringifyFunc func) noexcept;
    static std::string ToString(const Any &param);
private:
    static std::map<size_t, StringifyFunc> converterMap_;
};
} // namespace Mki_ms

#define REG_STRINGIFY(typename, func) \
    static Mki_ms::Stringify g_register_##func(typeid(typename).hash_code(), func)

#endif
