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

tensor_cpp_methods = ['erfc', 'flatten', 'atan', 'arctan', 'minimum', 'sinh', 'floor_divide_', '__ifloordiv__', 'fmod', 'log', 'add', '__add__', 'add_', '__iadd__', 'var', 'logical_not', 'index', 'sin', 'cumsum', 'scatter_', 'expm1', 'narrow', 'mean', 'baddbmm', 'argmin', 'log1p', 'asin', 'arcsin', 'neg', 'negative', 'hardshrink', 'permute', 'copy_', 'sum', 'not_equal', 'ne', 'masked_scatter', 'view_as', 'greater_equal', 'ge', 'logsumexp', 'mm', 'allclose', 'put_', 'erf', 'unique', 'logaddexp2', 'prod', 'repeat', 'dot', 'maximum', 'masked_fill_', 'index_copy_', 'broadcast_to', 'logical_xor', 'tril', 'addmm', 'div_', '__itruediv__', 'any', 'fill_diagonal_', 'all', 'new_empty', 'to', 'unsqueeze', 'trunc', 'isfinite', 'floor_divide', 'transpose', 'unbind', 'count_nonzero', 'tile', 'bitwise_or', '__or__', 'tan', 'sqrt', 'masked_scatter_', 'atanh', 'arctanh', 'exp_', 'scatter_add', 'min', 'addbmm', 'sinc', 'view', 'median', 'where', 'isinf', 'cosh', 'kthvalue', 'repeat_interleave', 'rsqrt', 'topk', 't', 'histc', 'pow', '__pow__', 'cos', 'logaddexp', 'nansum', 'floor', 'acosh', 'arccosh', 'chunk', 'take', 'new_full', 'inverse', 'real', 'roll', 'squeeze', 'less_equal', 'le', 'diag', 'triu', 'type_as', 'index_fill_', 'split', 'acos', 'arccos', 'clone', 'true_divide', 'masked_select', 'new_ones', 'imag', '__mod__', 'outer', 'isclose', 'log10', 'bincount', 'remainder', 'mul', 'less', 'lt', 'index_select', 'square', 'sub_', '__isub__', 'reciprocal', 'addmv', 'round', 'fill_', 'logical_and', 'index_add', 'bitwise_and', '__and__', 'xlogy', 'subtract', 'std', 'log_', 'tanh', 'nan_to_num', 'mul_', '__imul__', 'sigmoid_', 'frac', 'isneginf', 'sort', 'eq', 'atan2', 'arctan2', 'gather', 'addcdiv', 'new_zeros', 'clamp', 'clip', 'expand_as', 'div', 'divide', 'exp', 'greater', 'gt', 'select', 'bitwise_not', 'sigmoid', 'reshape', 'sub', '__sub__', 'gcd', 'matmul', 'argmax', 'max', 'argsort', 'log2', 'bitwise_xor', '__xor__', 'abs', '__abs__', 'absolute', 'remainder_', '__imod__', 'lerp', 'masked_fill', 'ceil', 'logical_or', 'scatter', 'asinh', 'arcsinh']
