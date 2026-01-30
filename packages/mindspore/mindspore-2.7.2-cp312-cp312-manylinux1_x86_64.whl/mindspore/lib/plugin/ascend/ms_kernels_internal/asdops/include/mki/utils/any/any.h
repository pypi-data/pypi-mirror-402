/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_ANY_ANY_H
#define MKI_UTILS_ANY_ANY_H
#include <memory>
#include <typeinfo>

namespace Mki_ms {
class Any {
public:
    Any() = default;
    ~Any() = default;

    Any(const Any &other)
    {
        if (other.dataPtr_) {
            dataPtr_ = other.dataPtr_->Clone();
        }
    }

    Any &operator=(const Any &other)
    {
        dataPtr_ = std::move(Any(other).dataPtr_);
        return *this;
    }

    Any(Any &&other) : dataPtr_(std::move(other.dataPtr_)) {}

    Any &operator=(Any &&other)
    {
        dataPtr_ = std::move(other.dataPtr_);
        return *this;
    }

    template <typename T> using DecayType = typename std::decay<T>::type;
    template <typename T, typename std::enable_if<!std::is_same<DecayType<T>, Any>::value, bool>::type = true>
    Any(T &&data)
    {
        dataPtr_.reset(new InternalDataImpl<DecayType<T>>(std::forward<T>(data)));
    }

    template <typename T, typename std::enable_if<!std::is_same<DecayType<T>, Any>::value, bool>::type = true>
    Any &operator=(T &&data)
    {
        dataPtr_.reset(new InternalDataImpl<DecayType<T>>(std::forward<T>(data)));
        return *this;
    }

    bool HasValue() const { return dataPtr_ != nullptr; }

    const std::type_info &Type() const { return HasValue() ? dataPtr_->Type() : typeid(void); }

    template <typename T> const T &Cast() const
    {
        CheckType<T>();
        CheckBind<T>();
        return static_cast<const InternalDataImpl<T> *>(dataPtr_.get())->data_;
    }

    void Reset() { dataPtr_.reset(); }

private:
    template <typename T> void CheckType() const
    {
        if (Type().hash_code() != typeid(T).hash_code()) {
            throw std::bad_cast();
        }
    }

    template <typename T> void CheckBind() const
    {
        if (!HasValue()) {
            throw std::bad_cast();
        }
    }

private:
    struct InternalData {
        InternalData() = default;
        virtual ~InternalData() = default;
        virtual const std::type_info &Type() const = 0;
        virtual std::unique_ptr<InternalData> Clone() const = 0;
    };

    template <typename T> struct InternalDataImpl : public InternalData {
        T data_;
        explicit InternalDataImpl(const T &data) : data_(data) {}
        explicit InternalDataImpl(T &&data) : data_(std::move(data)) {}
        const std::type_info &Type() const override { return typeid(T); }
        std::unique_ptr<InternalData> Clone() const override
        {
            return std::make_unique<InternalDataImpl<T>>(data_);
        }
    };

private:
    std::unique_ptr<InternalData> dataPtr_;
};

template <typename T> const T &AnyCast(const Any &any) { return any.Cast<T>(); }
} // namespace Mki_ms

#endif
