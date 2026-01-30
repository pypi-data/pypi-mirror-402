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

tensor_cpp_methods = ['addmm', 'logsumexp', 'reciprocal', 'flatten', 'isneginf', 'erf', 'put_', 'log', 'permute', 'where', 'sort', 'bitwise_or', '__or__', 'div_', '__itruediv__', 'chunk', 'mul_', '__imul__', 'narrow', 'view', 'baddbmm', 'min', 'fmod', 'var', 'squeeze', 'log_', 'prod', 'expm1', 'square', 't', 'imag', 'max', 'logical_xor', 'mul', 'mm', 'bincount', 'div', 'divide', 'diag', 'atan2', 'arctan2', 'index_select', 'sub_', '__isub__', 'greater_equal', 'ge', 'rsqrt', 'select', 'fill_', 'ceil', 'add_', '__iadd__', 'index_fill_', 'unbind', 'masked_scatter_', 'clone', 'gcd', 'tan', 'trunc', 'atan', 'arctan', 'greater', 'gt', 'mean', 'scatter_', 'std', 'frac', 'dot', 'isclose', 'sin', 'type_as', 'reshape', 'maximum', 'isinf', 'logical_not', 'sigmoid_', 'exp', 'xlogy', 'log10', 'copy_', 'remainder', 'fill_diagonal_', 'true_divide', 'floor', 'broadcast_to', 'eq', 'all', 'argmin', 'isfinite', 'masked_scatter', 'acosh', 'arccosh', 'masked_select', 'log2', 'atanh', 'arctanh', 'addbmm', 'addmv', 'tanh', 'bitwise_not', 'not_equal', 'ne', 'roll', 'masked_fill_', 'masked_fill', 'new_full', 'to', 'floor_divide', 'sqrt', 'subtract', 'transpose', 'scatter_add', 'take', 'argmax', 'inverse', 'matmul', 'new_ones', 'pow', '__pow__', 'median', 'nan_to_num', 'sigmoid', 'repeat', 'abs', 'absolute', '__abs__', 'new_empty', 'add', '__add__', 'less', 'lt', 'round', 'unsqueeze', 'logical_and', 'floor_divide_', '__ifloordiv__', 'tile', 'sinh', 'nansum', 'hardshrink', 'index_add', 'logaddexp2', 'sinc', 'index', 'erfc', 'view_as', 'repeat_interleave', 'cumsum', 'minimum', 'allclose', 'new_zeros', 'topk', 'expand_as', 'exp_', 'remainder_', '__imod__', 'gather', 'cos', '__mod__', 'sub', '__sub__', 'bitwise_xor', '__xor__', 'neg', 'negative', 'scatter', 'histc', 'outer', 'bitwise_and', '__and__', 'asinh', 'arcsinh', 'unique', 'split', 'real', 'kthvalue', 'addcdiv', 'cosh', 'count_nonzero', 'logaddexp', 'any', 'sum', 'logical_or', 'less_equal', 'le', 'index_copy_', 'clamp', 'clip', 'acos', 'arccos', 'argsort', 'lerp', 'log1p', 'asin', 'arcsin', 'tril', 'triu']
