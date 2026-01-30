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

tensor_cpp_methods = ['baddbmm', 'log', 'less_equal', 'le', 'argsort', 'logsumexp', 'mm', 'squeeze', 'masked_fill_', 'cos', 'narrow', 'view_as', 'index', 'isfinite', 'index_add', 'sum', 'prod', 'floor', 'to', 'rsqrt', 'triu', 'add', '__add__', 'tile', 'nan_to_num', 'eq', 'var', 'index_fill_', 'trunc', 'addcdiv', 'unbind', 't', 'logical_xor', 'exp', 'chunk', 'bincount', 'mean', 'argmin', 'expand_as', 'floor_divide_', '__ifloordiv__', 'log_', 'sin', 'min', 'dot', 'atan2', 'arctan2', 'count_nonzero', 'tan', 'isneginf', 'logaddexp2', 'frac', 'div_', '__itruediv__', 'diag', 'imag', 'exp_', 'clone', 'not_equal', 'ne', 'masked_select', 'scatter_', 'neg', 'negative', 'logical_and', 'less', 'lt', 'atan', 'arctan', 'mul_', '__imul__', 'broadcast_to', 'reciprocal', 'tril', 'asin', 'arcsin', 'sort', 'isclose', 'ceil', 'sinc', 'cumsum', 'real', 'new_full', 'scatter', 'fill_', 'bitwise_xor', '__xor__', 'sigmoid_', 'mul', 'sub', '__sub__', 'logical_or', 'take', 'nansum', '__mod__', 'any', 'repeat_interleave', 'logaddexp', 'expm1', 'addbmm', 'unsqueeze', 'lerp', 'reshape', 'all', 'histc', 'sigmoid', 'kthvalue', 'sub_', '__isub__', 'topk', 'add_', '__iadd__', 'index_select', 'scatter_add', 'matmul', 'new_ones', 'std', 'hardshrink', 'div', 'divide', 'bitwise_or', '__or__', 'masked_scatter_', 'outer', 'log10', 'maximum', 'log1p', 'remainder_', '__imod__', 'log2', 'erf', 'view', 'allclose', 'tanh', 'abs', '__abs__', 'absolute', 'flatten', 'greater_equal', 'ge', 'sinh', 'addmv', 'minimum', 'inverse', 'unique', 'roll', 'new_empty', 'fmod', 'asinh', 'arcsinh', 'masked_fill', 'median', 'permute', 'gather', 'sqrt', 'clamp', 'clip', 'cosh', 'fill_diagonal_', 'logical_not', 'put_', 'true_divide', 'transpose', 'round', 'split', 'square', 'select', 'where', 'acosh', 'arccosh', 'pow', '__pow__', 'isinf', 'masked_scatter', 'greater', 'gt', 'bitwise_and', '__and__', 'floor_divide', 'erfc', 'remainder', 'addmm', 'acos', 'arccos', 'atanh', 'arctanh', 'bitwise_not', 'max', 'type_as', 'gcd', 'argmax', 'copy_', 'index_copy_', 'new_zeros', 'subtract', 'xlogy', 'repeat']
