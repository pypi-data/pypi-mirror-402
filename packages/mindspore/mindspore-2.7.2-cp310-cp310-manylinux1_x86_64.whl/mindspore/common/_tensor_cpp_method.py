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

tensor_cpp_methods = ['allclose', 'prod', 'atan', 'arctan', 'atan2', 'arctan2', 'fill_', 'isclose', 'repeat_interleave', 'index', 'log2', 'mean', 'sqrt', 'any', 'div_', '__itruediv__', 'count_nonzero', 'maximum', 'not_equal', 'ne', 'nan_to_num', 'sinc', 'minimum', 'nansum', 'logical_not', 'eq', 'median', 'ceil', 'sinh', 'isfinite', 'bitwise_xor', '__xor__', 'acos', 'arccos', 'log', 'chunk', 'where', 'addmv', 'square', 'atanh', 'arctanh', 'imag', 'expand_as', 'kthvalue', 'remainder_', '__imod__', 'floor_divide_', '__ifloordiv__', 'put_', 'tril', 'less_equal', 'le', 't', 'repeat', 'erf', 'mul', 'dot', 'sin', 'masked_fill_', 'frac', 'xlogy', 'logsumexp', 'narrow', 'index_select', 'hardshrink', 'copy_', 'split', 'cos', 'unsqueeze', 'greater', 'gt', 'argsort', 'matmul', 'index_add', 'addbmm', 'broadcast_to', 'cosh', 'var', 'lerp', 'masked_select', 'masked_scatter_', 'diag', 'view', 'subtract', 'asinh', 'arcsinh', 'view_as', 'roll', 'index_copy_', 'asin', 'arcsin', 'floor_divide', 'transpose', 'log_', 'unbind', 'true_divide', 'tan', 'max', 'reshape', 'squeeze', 'sigmoid_', 'exp', 'tanh', 'addmm', 'histc', 'mm', 'isneginf', 'sub_', '__isub__', 'sigmoid', 'type_as', 'fill_diagonal_', 'abs', 'absolute', '__abs__', 'log1p', 'log10', 'neg', 'negative', 'bincount', 'gather', 'scatter', 'flatten', 'masked_scatter', 'clone', 'unique', 'mul_', '__imul__', 'new_ones', '__mod__', 'logaddexp2', 'masked_fill', 'addcdiv', 'bitwise_and', '__and__', 'rsqrt', 'argmax', 'outer', 'acosh', 'arccosh', 'baddbmm', 'inverse', 'logical_xor', 'sort', 'argmin', 'scatter_add', 'all', 'new_zeros', 'new_empty', 'floor', 'reciprocal', 'div', 'divide', 'expm1', 'index_fill_', 'trunc', 'sum', 'permute', 'pow', '__pow__', 'logaddexp', 'less', 'lt', 'bitwise_not', 'new_full', 'greater_equal', 'ge', 'exp_', 'real', 'erfc', 'tile', 'logical_or', 'topk', 'logical_and', 'to', 'cumsum', 'clamp', 'clip', 'triu', 'sub', '__sub__', 'isinf', 'add_', '__iadd__', 'std', 'take', 'fmod', 'select', 'gcd', 'bitwise_or', '__or__', 'round', 'remainder', 'scatter_', 'min', 'add', '__add__']
