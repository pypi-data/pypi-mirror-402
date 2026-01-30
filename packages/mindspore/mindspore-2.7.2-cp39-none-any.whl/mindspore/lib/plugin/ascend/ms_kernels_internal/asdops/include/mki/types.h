/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_TYPES_H
#define MKI_TYPES_H

#include <cstddef>
#include <string>

namespace Mki_ms {
enum TensorDType : int {
    TENSOR_DTYPE_UNDEFINED = -1,
    TENSOR_DTYPE_FLOAT = 0,
    TENSOR_DTYPE_FLOAT16 = 1,
    TENSOR_DTYPE_INT8 = 2,
    TENSOR_DTYPE_INT32 = 3,
    TENSOR_DTYPE_UINT8 = 4,
    TENSOR_DTYPE_INT16 = 6,
    TENSOR_DTYPE_UINT16 = 7,
    TENSOR_DTYPE_UINT32 = 8,
    TENSOR_DTYPE_INT64 = 9,
    TENSOR_DTYPE_UINT64 = 10,
    TENSOR_DTYPE_DOUBLE = 11,
    TENSOR_DTYPE_BOOL = 12,
    TENSOR_DTYPE_STRING = 13,
    TENSOR_DTYPE_COMPLEX64 = 16,
    TENSOR_DTYPE_COMPLEX128 = 17,
    TENSOR_DTYPE_BF16 = 27,
    TENSOR_DTYPE_INT4 = 29,
    TENSOR_DTYPE_UINT1 = 30,
    TENSOR_DTYPE_COMPLEX32 = 33,
    TENSOR_DTYPE_HIFLOAT8 = 34,
    TENSOR_DTYPE_FLOAT8_E5M2 = 35,
    TENSOR_DTYPE_FLOAT8_E4M3FN = 36,
    TENSOR_DTYPE_FLOAT8_E8M0 = 37,
    TENSOR_DTYPE_FLOAT6_E3M2 = 38,
    TENSOR_DTYPE_FLOAT6_E2M3 = 39,
    TENSOR_DTYPE_FLOAT4_E2M1 = 40,
    TENSOR_DTYPE_FLOAT4_E1M2 = 41,
};

enum TensorFormat : int {
    TENSOR_FORMAT_UNDEFINED = -1,
    TENSOR_FORMAT_NCHW = 0,
    TENSOR_FORMAT_NHWC = 1,
    TENSOR_FORMAT_ND = 2,
    TENSOR_FORMAT_NC1HWC0 = 3,
    TENSOR_FORMAT_FRACTAL_Z = 4,
    TENSOR_FORMAT_NC1HWC0_C04 = 12,
    TENSOR_FORMAT_HWCN = 16,
    TENSOR_FORMAT_NDHWC = 27,
    TENSOR_FORMAT_FRACTAL_NZ = 29,
    TENSOR_FORMAT_NCDHW = 30,
    TENSOR_FORMAT_NDC1HWC0 = 32,
    TENSOR_FORMAT_FRACTAL_Z_3D = 33,
    TENSOR_FORMAT_NC = 35,
    TENSOR_FORMAT_NCL = 47,
    TENSOR_FORMAT_FRACTAL_NZ_C0_16 = 50,
    TENSOR_FORMAT_FRACTAL_NZ_C0_32 = 51,
};

enum ErrorType : int {
    NO_ERROR = 0,
    ERROR_INVALID_VALUE = 1,
    ERROR_OPERATION_NOT_EXIST = 2,
    ERROR_TACTIC_NOT_EXIST = 3,
    ERROR_KERNEL_NOT_EXIST = 4,
    ERROR_ATTR_NOT_EXIST = 5,
    ERROR_ATTR_INVALID_TYPE = 6,
    ERROR_LAUNCH_KERNEL_ERROR = 7,
    ERROR_SYNC_STREAM_ERROR = 8,
    ERROR_INFERSHAPE_ERROR = 9,
    ERROR_NOT_CONSISTANT = 10,
    ERROR_ALLOC_HOST = 11,
    ERROR_MEMERY_COPY_ERROR = 12,
    ERROR_RUN_TIME_ERROR = 13
};

size_t GetTensorElementSize(const TensorDType dtype);
TensorDType GetDTypeWithStr(const std::string &typeStr);
TensorFormat GetFormatWithStr(const std::string &formatStr);
const std::string &GetStrWithDType(int dType);
const std::string &GetStrWithFormat(int format);
} // namespace Mki_ms

#endif
