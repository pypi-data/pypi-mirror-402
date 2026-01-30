/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_OPERATIONIR_OPERATION_IR_CFG_H
#define MKI_UTILS_OPERATIONIR_OPERATION_IR_CFG_H

#include <map>
#include "operation_ir.h"
#include "mki/utils/status/status.h"

namespace Mki_ms {
class OperationIrCfg {
public:
    OperationIrCfg();
    ~OperationIrCfg();
    Status Load(const std::string &fileName);
    OperationIr *GetOperationIr(const std::string &opKey);

private:
    bool IsValidOpKey(const std::string &key) const;

private:
    std::map<std::string, OperationIr> data_;
};
} // namespace Mki_ms
#endif
