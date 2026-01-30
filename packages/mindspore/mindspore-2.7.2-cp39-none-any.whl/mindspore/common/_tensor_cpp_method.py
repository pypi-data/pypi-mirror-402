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

tensor_cpp_methods = ['trunc', 'tan', 'div', 'divide', 'diag', 'tanh', 'chunk', 'view_as', 'logical_or', 'logical_and', 'isclose', 'roll', 'baddbmm', 'xlogy', 'allclose', 'addcdiv', 'erfc', 'sin', 'index_add', 'acosh', 'arccosh', 'less_equal', 'le', 'true_divide', 'all', 'masked_scatter', 'repeat_interleave', 'transpose', 'bitwise_and', '__and__', 'log1p', 'repeat', 'atan', 'arctan', 'split', 'exp_', 'logsumexp', 'atan2', 'arctan2', 'imag', 'asinh', 'arcsinh', 'real', 'sort', 'greater', 'gt', 'broadcast_to', 'copy_', 'to', 'index_select', 'mean', 'where', 'unsqueeze', 'logical_xor', 'addmm', 'round', 'masked_fill_', 'sigmoid_', 'div_', '__itruediv__', 'sum', 'count_nonzero', 'new_ones', 'matmul', 'scatter', 'any', 'index_fill_', 'inverse', 'type_as', 'median', 'fill_', 'minimum', 'bitwise_xor', '__xor__', 'logical_not', 'triu', 'nan_to_num', 'rsqrt', 'log', 'cos', 'sqrt', 'greater_equal', 'ge', 'dot', 'sub_', '__isub__', 'bitwise_or', '__or__', 'isfinite', 'topk', 'permute', 'expand_as', 'cumsum', 'addmv', 'sub', '__sub__', 'outer', 'index_copy_', 'nansum', 'scatter_', 'fill_diagonal_', 'erf', 'max', 'min', 'pow', '__pow__', 'neg', 'negative', 'mul_', '__imul__', 'isinf', 'masked_select', 'hardshrink', 'masked_fill', 'log_', 'logaddexp2', 'add_', '__iadd__', 'bincount', 't', 'new_full', 'argsort', 'abs', '__abs__', 'absolute', 'kthvalue', 'unbind', 'logaddexp', 'maximum', 'expm1', 'put_', 'fmod', 'argmin', 'add', '__add__', 'not_equal', 'ne', 'histc', 'select', 'clamp', 'clip', 'cosh', 'bitwise_not', 'square', 'scatter_add', 'eq', 'subtract', 'floor_divide_', '__ifloordiv__', 'floor', 'std', 'sinh', 'sigmoid', 'exp', 'new_zeros', 'masked_scatter_', 'log10', 'reciprocal', 'lerp', 'remainder', 'mul', 'log2', 'sinc', 'index', 'gcd', 'remainder_', '__imod__', 'addbmm', 'var', 'argmax', 'tril', 'prod', 'gather', 'acos', 'arccos', 'new_empty', 'unique', 'frac', 'atanh', 'arctanh', 'floor_divide', 'flatten', 'ceil', 'less', 'lt', 'tile', '__mod__', 'view', 'isneginf', 'mm', 'take', 'reshape', 'clone', 'squeeze', 'narrow', 'asin', 'arcsin']
