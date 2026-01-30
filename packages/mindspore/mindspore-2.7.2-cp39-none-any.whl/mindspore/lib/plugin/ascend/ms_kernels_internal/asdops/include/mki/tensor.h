/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_TENSOR_H
#define MKI_TENSOR_H
#include <string>
#include <vector>
#include "mki/types.h"
#include "mki/utils/SVector/SVector.h"

namespace Mki_ms {
struct TensorDesc {
    TensorDType dtype = TENSOR_DTYPE_UNDEFINED;
    TensorFormat format = TENSOR_FORMAT_UNDEFINED;
    Mki_ms::SVector<int64_t> dims;
    std::vector<int64_t> strides;
    int64_t offset = 0;
    int64_t Numel() const;
    void View(const Mki_ms::SVector<int64_t> &newDims);
    bool IsContiguous() const;
    std::string ToString() const;
};

struct Tensor {
    TensorDesc desc;
    void *data = nullptr;
    size_t dataSize = 0;
    void *hostData = nullptr;
    int64_t Numel() const;
    void View(const Mki_ms::SVector<int64_t> &newDims);
    bool IsContiguous() const;
    std::string ToString() const;
};
} // namespace Mki_ms

#endif
