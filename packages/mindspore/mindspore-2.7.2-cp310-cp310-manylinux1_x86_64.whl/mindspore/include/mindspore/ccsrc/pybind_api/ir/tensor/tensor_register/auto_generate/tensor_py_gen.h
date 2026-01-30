/**
 * Copyright 2025 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef TENSOR_PY_GEN_H
#define TENSOR_PY_GEN_H

#include "pybind_api/ir/tensor/tensor_api/auto_generate/tensor_api.h"
#include "pybind11/pybind11.h"
#include "pybind_api/ir/tensor/tensor_register/tensor_func_reg.h"

namespace py = pybind11;
namespace mindspore {
namespace tensor {

#define DEFINE_TENSOR_METHOD_CPYWRAPPER(NAME)                                                          \
  static PyObject *TensorMethod##NAME##_CPyWrapper(PyObject *self, PyObject *args, PyObject *kwargs) { \
    PyObject* result;                                                                                  \
    try {                                                                                              \
      result = TensorMethod##NAME(self, args, kwargs);                                                 \
    } catch (py::error_already_set &e) {                                                               \
      e.restore();                                                                                     \
      return NULL;                                                                                     \
    } catch (const std::runtime_error &e) {                                                            \
      if (dynamic_cast<const py::index_error *>(&e)) {                                                 \
        PyErr_SetString(PyExc_IndexError, e.what());                                                   \
      } else if (dynamic_cast<const py::value_error *>(&e)) {                                          \
        PyErr_SetString(PyExc_ValueError, e.what());                                                   \
      } else if (dynamic_cast<const py::type_error *>(&e)) {                                           \
        PyErr_SetString(PyExc_TypeError, e.what());                                                    \
      } else {                                                                                         \
        PyErr_SetString(PyExc_RuntimeError, e.what());                                                 \
      }                                                                                                \
      return NULL;                                                                                     \
    }                                                                                                  \
    return result;                                                                                     \
  }


#define DEFINE_TENSOR_METHODS_CPYWRAPPERS()         \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Allclose) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Prod) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Atan) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Atan2) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Fill_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Isclose) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(RepeatInterleave) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Index) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Log2) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Mean) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sqrt) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Any) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Div_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(CountNonzero) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Maximum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NotEqual) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NanToNum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sinc) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Minimum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Nansum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(LogicalNot) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Eq) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Median) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Ceil) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sinh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Isfinite) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(BitwiseXor) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Acos) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Log) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Chunk) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Where) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Addmv) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Square) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Atanh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Imag) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(ExpandAs) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Kthvalue) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Remainder_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(FloorDivide_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Put_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Tril) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(LessEqual) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(T) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Repeat) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Erf) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Mul) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Dot) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sin) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(MaskedFill_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Frac) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Xlogy) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Logsumexp) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Narrow) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(IndexSelect) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Hardshrink) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Copy_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Split) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Cos) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Unsqueeze) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Greater) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Argsort) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Matmul) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(IndexAdd) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Addbmm) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(BroadcastTo) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Cosh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Var) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Lerp) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(MaskedSelect) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(MaskedScatter_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Diag) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(View) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Subtract) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Asinh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(ViewAs) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Roll) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(IndexCopy_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Asin) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(FloorDivide) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Transpose) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Log_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Unbind) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(TrueDivide) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Tan) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Max) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Reshape) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Squeeze) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sigmoid_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Exp) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Tanh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Addmm) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Histc) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Mm) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Isneginf) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sub_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sigmoid) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(TypeAs) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(FillDiagonal_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Abs) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Log1p) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Log10) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Neg) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Bincount) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Gather) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Scatter) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Flatten) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(MaskedScatter) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Clone) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Unique) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Mul_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NewOnes) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(ModMagic) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Logaddexp2) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(MaskedFill) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Addcdiv) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(BitwiseAnd) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Rsqrt) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Argmax) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Outer) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Acosh) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Baddbmm) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Inverse) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(LogicalXor) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sort) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Argmin) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(ScatterAdd) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(All) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NewZeros) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NewEmpty) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Floor) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Reciprocal) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Div) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Expm1) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(IndexFill_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Trunc) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Permute) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Pow) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Logaddexp) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Less) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(BitwiseNot) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(NewFull) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(GreaterEqual) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Exp_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Real) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Erfc) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Tile) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(LogicalOr) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Topk) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(LogicalAnd) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(To) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Cumsum) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Clamp) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Triu) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Sub) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Isinf) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Add_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Std) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Take) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Fmod) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Select) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Gcd) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(BitwiseOr) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Round) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Remainder) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Scatter_) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Min) \
  DEFINE_TENSOR_METHOD_CPYWRAPPER(Add)

extern PyMethodDef *TensorMethods;
}  // namespace tensor
}  // namespace mindspore
#endif  // TENSOR_PY_GEN_H