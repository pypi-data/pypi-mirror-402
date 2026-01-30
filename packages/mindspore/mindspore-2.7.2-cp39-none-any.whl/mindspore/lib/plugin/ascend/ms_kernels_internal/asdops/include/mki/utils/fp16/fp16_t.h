/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */

#ifndef MKI_UTILS_FP_16_FP_16_T_H
#define MKI_UTILS_FP_16_FP_16_T_H

#include <cstdint>
#include <cmath>
#include <algorithm>
#include <ostream>

namespace Mki_ms {
/**
 * @ingroup Fp16T
 * @brief   Half precision float
 *          bit15:   1 bit SIGN
 *          bit14-10:5 bit EXP
 *          bit0-9:  10bit MAN
 */
struct Fp16T {
    uint16_t val = 0;

public:
    // Constructor without any param
    Fp16T(void) { val = 0x0u; }

    // Constructor with all type
    template <typename T>
    explicit Fp16T(const T &value) { *this = value; }

    // Constructor with an uint16_t value
    explicit Fp16T(const uint16_t &uiVal) : val(uiVal) {}

    // copy constructor
    Fp16T(const Fp16T &fp16) : val(fp16.val) {}

    // Override addition operator to performing Fp16T addition
    Fp16T operator+(const Fp16T fp16) const;

    // Override addition operator to performing Fp16T subtraction
    Fp16T operator-(const Fp16T fp16) const;

    // Override multiplication operator to performing Fp16T multiplication
    Fp16T operator*(const Fp16T fp16) const;

    // Override division operator to performing Fp16T division
    Fp16T operator/(const Fp16T fp16) const;

    // Override addition operator to performing Fp16T addition
    Fp16T operator+=(const Fp16T fp16);

    // Override addition operator to performing Fp16T subtraction
    Fp16T operator-=(const Fp16T fp16);

    // Override multiplication operator to performing Fp16T multiplication
    Fp16T operator*=(const Fp16T fp16);

    // Override division operator to performing Fp16T division
    Fp16T operator/=(const Fp16T fp16);

    // Override Fp16T if-equal comparison
    bool operator==(const Fp16T &fp16) const;

    // Override Fp16T not-equal comparison
    bool operator!=(const Fp16T &fp16) const;

    // Override Fp16T greater-than comparison
    bool operator>(const Fp16T &fp16) const;

    // Override Fp16T greater-equal comparison
    bool operator>=(const Fp16T &fp16) const;

    // Override Fp16T less-than comparison
    bool operator<(const Fp16T &fp16) const;

    // Override Fp16T less-equal comparison
    bool operator<=(const Fp16T &fp16) const;

    // convert float to Fp16T
    Fp16T &operator=(const int8_t &iVal);

    // convert int16_t to Fp16T
    Fp16T &operator=(const int16_t &iVal);

    // convert int32_t to Fp16T
    Fp16T &operator=(const int32_t &iVal);

    // convert uint8_t to Fp16T
    Fp16T &operator=(const uint8_t &uiVal);

    // convert uint16_t to Fp16T
    Fp16T &operator=(const uint16_t &uiVal);

    // convert uint32_t to Fp16T
    Fp16T &operator=(const uint32_t &uiVal);

    // copy Fp16T to a new Fp16T
    Fp16T &operator=(const Fp16T &fp16);

    // convert float to Fp16T
    Fp16T &operator=(const float &fVal);

    // convert double to Fp16T
    Fp16T &operator=(const double &dValue);

    // convert Fp16T to int8_t
    operator int8_t() const;

    // convert Fp16T to int16_t
    operator int16_t() const;

    // convert Fp16T to int32_t
    operator int32_t() const;

    // convert Fp16T to uint8_t
    operator uint8_t() const;

    // convert Fp16T to uint16_t
    operator uint16_t() const;

    // convert Fp16T to unint32_t
    operator uint32_t() const;

    // convert Fp16T to float/fp32
    operator float() const;

    // convert Fp16T to double/fp64
    operator double() const;

    /**
     * @brief   whether a Fp16T is inifinite
     * @return  Returns 1:+INF -1:-INF 0:not INF
     */
    int IsInf() const;

    // Convert Fp16T to int8_t
    int8_t ToInt8();

    // Convert Fp16T to int16_t
    int16_t ToInt16();

    // Convert Fp16T to int32_t
    int32_t ToInt32();

    // Convert Fp16T to uint8_t
    uint8_t ToUInt8();

    // Convert Fp16T to uint16_t
    uint16_t ToUInt16();

    // Convert Fp16T to uint32_t
    uint32_t ToUInt32();

    // Convert Fp16T to float/fp32
    float ToFloat();

    // Convert Fp16T to double/fp64
    double ToDouble();
};

using fp16_t = Fp16T;

std::ostream &operator<<(std::ostream &os, const Fp16T &fp16);
}; // namespace Mki_ms

#endif // MKI_UTILS_FP_16_FP_16_T_H
