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

tensor_cpp_methods = ['var', 'broadcast_to', 'narrow', 'imag', 'mul', 'new_zeros', 'nan_to_num', 'greater', 'gt', 'argsort', 'isneginf', 'log1p', 'unsqueeze', 'clamp', 'clip', 'reciprocal', 'std', 'rsqrt', 'baddbmm', 'cumsum', 'any', 'atan2', 'arctan2', 'trunc', 'index_copy_', 'min', 'bincount', 'type_as', 'isinf', 'clone', 'minimum', 'matmul', 'repeat', 'view_as', 'cosh', 'masked_scatter_', 'logsumexp', 'repeat_interleave', 'masked_fill', 'bitwise_xor', '__xor__', 'index_fill_', 'addmv', 'add', '__add__', 'logical_xor', 'kthvalue', 'remainder', 'atanh', 'arctanh', 'asinh', 'arcsinh', 'sigmoid_', 'reshape', 'logical_or', 'not_equal', 'ne', 'erf', 'neg', 'negative', 'tril', 'put_', 'all', 'topk', 'tanh', 'square', 'floor', 'tile', 'sinc', 'sub', '__sub__', 'acosh', 'arccosh', 'new_full', 'median', 'logaddexp2', 'exp_', 'sin', 'histc', 'logical_and', 'sinh', 'cos', 'prod', 'expand_as', 'tan', 'xlogy', 'bitwise_or', '__or__', 'chunk', 'log', 'flatten', 'sort', '__mod__', 'take', 'remainder_', '__imod__', 'scatter', 'floor_divide_', '__ifloordiv__', 'logaddexp', 'permute', 'addcdiv', 'log_', 'eq', 'where', 'outer', 'erfc', 'select', 'greater_equal', 'ge', 't', 'allclose', 'exp', 'isfinite', 'masked_fill_', 'mean', 'gcd', 'scatter_add', 'floor_divide', 'nansum', 'index', 'acos', 'arccos', 'triu', 'sub_', '__isub__', 'div', 'divide', 'expm1', 'count_nonzero', 'to', 'unbind', 'less', 'lt', 'view', 'unique', 'mul_', '__imul__', 'bitwise_and', '__and__', 'isclose', 'mm', 'div_', '__itruediv__', 'addmm', 'real', 'fill_', 'sum', 'atan', 'arctan', 'abs', 'absolute', '__abs__', 'masked_scatter', 'diag', 'subtract', 'true_divide', 'add_', '__iadd__', 'round', 'maximum', 'index_add', 'addbmm', 'fill_diagonal_', 'inverse', 'sqrt', 'index_select', 'less_equal', 'le', 'fmod', 'max', 'gather', 'copy_', 'ceil', 'split', 'argmin', 'squeeze', 'logical_not', 'transpose', 'roll', 'log2', 'new_empty', 'hardshrink', 'asin', 'arcsin', 'pow', '__pow__', 'masked_select', 'bitwise_not', 'new_ones', 'frac', 'dot', 'scatter_', 'sigmoid', 'log10', 'lerp', 'argmax']
