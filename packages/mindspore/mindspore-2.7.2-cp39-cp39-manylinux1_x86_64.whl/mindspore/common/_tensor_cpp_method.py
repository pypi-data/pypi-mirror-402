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

tensor_cpp_methods = ['min', 'broadcast_to', 'index_fill_', 'sinh', 'logsumexp', 'addcdiv', 'repeat', 'atan2', 'arctan2', 'var', 'where', 'erf', 'asinh', 'arcsinh', 'square', 'reshape', 'logical_xor', 'gather', 'minimum', 'new_ones', 'histc', 'argmin', 'mean', 'addmm', 'eq', 'logical_and', 'topk', 'chunk', 'addmv', 'rsqrt', 'div_', '__itruediv__', 'expm1', 'diag', 'masked_scatter', 'sigmoid', 'floor_divide', 'ceil', 'bitwise_or', '__or__', 'flatten', 'log2', 'narrow', 'sub_', '__isub__', 'bitwise_not', 'count_nonzero', 'index_add', 'isinf', 'new_full', 'acosh', 'arccosh', 'not_equal', 'ne', 'mul_', '__imul__', 'allclose', 'tanh', 'sigmoid_', 'logaddexp', 'roll', 'bitwise_xor', '__xor__', 'masked_fill', 'mul', 'logaddexp2', 'masked_scatter_', 'scatter', 'fill_', 'std', 'isfinite', 'cosh', 'new_empty', 'mm', 'select', 'index_copy_', 'scatter_', 't', 'frac', 'outer', 'tan', 'floor', 'expand_as', 'any', 'log10', 'less', 'lt', 'add_', '__iadd__', 'real', 'argmax', 'view', 'add', '__add__', 'new_zeros', 'bincount', 'bitwise_and', '__and__', 'scatter_add', 'cos', 'copy_', 'inverse', 'remainder', 'sqrt', 'neg', 'negative', 'exp', 'imag', 'view_as', 'isneginf', 'clamp', 'clip', 'div', 'divide', 'logical_or', 'median', 'prod', 'sin', 'erfc', 'baddbmm', 'index', 'tril', 'all', 'subtract', 'argsort', 'sinc', 'log', 'matmul', 'sub', '__sub__', 'acos', 'arccos', 'fmod', 'sum', 'clone', '__mod__', 'repeat_interleave', 'round', 'put_', 'floor_divide_', '__ifloordiv__', 'take', 'pow', '__pow__', 'fill_diagonal_', 'split', 'gcd', 'remainder_', '__imod__', 'trunc', 'unbind', 'unsqueeze', 'greater_equal', 'ge', 'unique', 'squeeze', 'lerp', 'maximum', 'masked_fill_', 'tile', 'permute', 'less_equal', 'le', 'logical_not', 'nansum', 'cumsum', 'dot', 'hardshrink', 'greater', 'gt', 'to', 'masked_select', 'index_select', 'kthvalue', 'asin', 'arcsin', 'xlogy', 'log1p', 'atan', 'arctan', 'transpose', 'type_as', 'atanh', 'arctanh', 'sort', 'true_divide', 'max', 'isclose', 'reciprocal', 'abs', 'absolute', '__abs__', 'addbmm', 'exp_', 'log_', 'nan_to_num', 'triu']
