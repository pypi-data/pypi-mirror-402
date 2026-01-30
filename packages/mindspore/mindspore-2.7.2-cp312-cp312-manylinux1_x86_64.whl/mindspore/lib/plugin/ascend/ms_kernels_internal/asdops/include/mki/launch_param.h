/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_LAUNCH_PARAM_H
#define MKI_LAUNCH_PARAM_H

#include <string>
#include "mki/types.h"
#include "mki/tensor.h"
#include "mki/utils/any/any.h"

class aclTensor;

namespace Mki_ms {
class LaunchParam {
public:
    LaunchParam() = default;
    LaunchParam(const LaunchParam &other);
    LaunchParam &operator=(const LaunchParam &other);
    ~LaunchParam();

    void Reset();

    void SetParam(const Any &srcParam);

    template <typename T> const T &GetParam() const { return AnyCast<T>(specificParam_); }
    template <typename T> T &GetParam() { return AnyCast<T>(specificParam_); }
    const Any &GetParam() const { return specificParam_; }
    Any &GetParam() { return specificParam_; }

    void AddInTensor(const Tensor &tensor);
    void AddInTensor(const aclTensor *tensor);
    size_t GetInTensorCount() const;
    const Tensor &GetInTensor(size_t pos) const;
    Tensor &GetInTensor(size_t pos);
    const SVector<Tensor> &GetInTensors() const;
    SVector<Tensor> &GetInTensors();

    void AddOutTensor(const Tensor &tensor);
    void AddOutTensor(const aclTensor *tensor);
    size_t GetOutTensorCount() const;
    const Tensor &GetOutTensor(size_t pos) const;
    Tensor &GetOutTensor(size_t pos);
    const SVector<Tensor> &GetOutTensors() const;
    SVector<Tensor> &GetOutTensors();

    std::string ToString() const;

private:
    Any specificParam_;
    SVector<Tensor> inTensors_;
    SVector<Tensor> outTensors_;
};

void *GetStorageAddr(const aclTensor *tensor);
} // namespace Mki_ms

#endif
