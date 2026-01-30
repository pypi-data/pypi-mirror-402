# Copyright 2024 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Add tensor cpp methods for stub tensor"""

tensor_cpp_methods = ['flatten', 'cumsum', 'broadcast_to', 'greater', 'gt', 'masked_fill_', 'type_as', 'logical_or', 'repeat_interleave', 'log', 'greater_equal', 'ge', 'sqrt', 'any', 'isneginf', 'kthvalue', 'fill_', 'all', 'triu', 'clamp', 'clip', 'var', 'mul', 'index_select', 'floor_divide', 'erfc', 'addbmm', 'tanh', 'outer', 'lerp', 'where', 'ceil', 'rsqrt', '__mod__', 'roll', 'unique', 'bitwise_or', '__or__', 'imag', 'logical_and', 'chunk', 'allclose', 'scatter_add', 'mean', 'logsumexp', 'index_copy_', 'remainder', 'sinc', 't', 'median', 'new_full', 'sin', 'addcdiv', 'diag', 'maximum', 'nan_to_num', 'trunc', 'sort', 'unsqueeze', 'addmm', 'put_', 'isfinite', 'hardshrink', 'fill_diagonal_', 'mm', 'fmod', 'narrow', 'bincount', 'div', 'divide', 'reshape', 'squeeze', 'logaddexp2', 'new_empty', 'atan2', 'arctan2', 'select', 'tan', 'view', 'index_fill_', 'floor_divide_', '__ifloordiv__', 'addmv', 'logaddexp', 'masked_scatter', 'clone', 'count_nonzero', 'atanh', 'arctanh', 'reciprocal', 'bitwise_and', '__and__', 'histc', 'baddbmm', 'tile', 'exp_', 'unbind', 'max', 'topk', 'atan', 'arctan', 'less_equal', 'le', 'gather', 'scatter', 'take', 'logical_xor', 'frac', 'inverse', 'matmul', 'eq', 'neg', 'negative', 'new_ones', 'expand_as', 'sub', '__sub__', 'pow', '__pow__', 'isclose', 'sinh', 'minimum', 'square', 'floor', 'add_', '__iadd__', 'sum', 'log1p', 'bitwise_not', 'bitwise_xor', '__xor__', 'dot', 'add', '__add__', 'copy_', 'acosh', 'arccosh', 'acos', 'arccos', 'argmin', 'mul_', '__imul__', 'log_', 'masked_select', 'cosh', 'round', 'masked_scatter_', 'true_divide', 'less', 'lt', 'index_add', 'isinf', 'split', 'div_', '__itruediv__', 'transpose', 'argsort', 'cos', 'argmax', 'erf', 'log2', 'scatter_', 'not_equal', 'ne', 'xlogy', 'index', 'min', 'expm1', 'view_as', 'logical_not', 'gcd', 'nansum', 'repeat', 'sigmoid_', 'remainder_', '__imod__', 'prod', 'subtract', 'asinh', 'arcsinh', 'abs', 'absolute', '__abs__', 'sigmoid', 'sub_', '__isub__', 'asin', 'arcsin', 'new_zeros', 'exp', 'real', 'std', 'to', 'tril', 'masked_fill', 'log10', 'permute']
