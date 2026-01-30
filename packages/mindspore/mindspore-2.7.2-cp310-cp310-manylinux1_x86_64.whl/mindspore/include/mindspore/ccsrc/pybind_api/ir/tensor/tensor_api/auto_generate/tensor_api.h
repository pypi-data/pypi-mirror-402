/**
 * Copyright 2024 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PYBIND_API_IR_TENSOR_API_H_
#define MINDSPORE_MINDSPORE_CCSRC_PYBIND_API_IR_TENSOR_API_H_
#include "pybind11/pybind11.h"

namespace py = pybind11;
namespace mindspore {
namespace tensor {

PyObject* TensorMethodAllclose(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodProd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAtan(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAtan2(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFill_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIsclose(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRepeatInterleave(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIndex(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLog2(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMean(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSqrt(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAny(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodDiv_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCountNonzero(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaximum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNotEqual(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNanToNum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSinc(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMinimum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNansum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogicalNot(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodEq(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMedian(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCeil(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSinh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIsfinite(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBitwiseXor(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAcos(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLog(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodChunk(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodWhere(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAddmv(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSquare(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAtanh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodImag(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodExpandAs(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodKthvalue(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRemainder_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFloorDivide_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodPut_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTril(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLessEqual(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodT(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRepeat(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodErf(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMul(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodDot(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSin(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaskedFill_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFrac(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodXlogy(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogsumexp(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNarrow(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIndexSelect(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodHardshrink(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCopy_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSplit(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCos(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodUnsqueeze(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodGreater(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodArgsort(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMatmul(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIndexAdd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAddbmm(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBroadcastTo(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCosh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodVar(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLerp(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaskedSelect(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaskedScatter_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodDiag(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodView(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSubtract(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAsinh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodViewAs(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRoll(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIndexCopy_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAsin(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFloorDivide(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTranspose(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLog_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodUnbind(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTrueDivide(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTan(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMax(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodReshape(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSqueeze(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSigmoid_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodExp(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTanh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAddmm(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodHistc(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMm(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIsneginf(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSub_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSigmoid(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTypeAs(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFillDiagonal_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAbs(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLog1p(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLog10(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNeg(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBincount(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodGather(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodScatter(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFlatten(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaskedScatter(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodClone(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodUnique(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMul_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNewOnes(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodModMagic(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogaddexp2(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMaskedFill(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAddcdiv(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBitwiseAnd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRsqrt(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodArgmax(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodOuter(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAcosh(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBaddbmm(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodInverse(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogicalXor(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSort(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodArgmin(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodScatterAdd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAll(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNewZeros(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNewEmpty(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFloor(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodReciprocal(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodDiv(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodExpm1(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIndexFill_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTrunc(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodPermute(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodPow(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogaddexp(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLess(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBitwiseNot(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodNewFull(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodGreaterEqual(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodExp_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodReal(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodErfc(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTile(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogicalOr(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTopk(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodLogicalAnd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTo(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodCumsum(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodClamp(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTriu(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSub(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodIsinf(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAdd_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodStd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodTake(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodFmod(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodSelect(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodGcd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodBitwiseOr(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRound(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodRemainder(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodScatter_(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodMin(PyObject* self, PyObject* py_args, PyObject* py_kwargs);
PyObject* TensorMethodAdd(PyObject* self, PyObject* py_args, PyObject* py_kwargs);

}  // namespace tensor
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PYBIND_API_IR_TENSOR_API_H_