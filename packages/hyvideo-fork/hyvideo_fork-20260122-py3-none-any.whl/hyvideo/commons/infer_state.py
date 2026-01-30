# Licensed under the TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
#
# Unless and only to the extent required by applicable law, the Tencent Hunyuan works and any
# output and results therefrom are provided "AS IS" without any express or implied warranties of
# any kind including any warranties of title, merchantability, noninfringement, course of dealing,
# usage of trade, or fitness for a particular purpose. You are solely responsible for determining the
# appropriateness of using, reproducing, modifying, performing, displaying or distributing any of
# the Tencent Hunyuan works or outputs and assume any and all risks associated with your or a
# third party's use or distribution of any of the Tencent Hunyuan works or outputs and your exercise
# of rights and permissions under this agreement.
# See the License for the specific language governing permissions and limitations under the License.

from typing import Optional
from dataclasses import dataclass, field

@dataclass
class InferState:
    enable_sageattn: bool = False  # whether to use SageAttention
    sage_blocks_range: Optional[range] = None  # block range to use SageAttention
    enable_torch_compile: bool = False  # whether to use torch compile

    enable_cache: bool = False  # whether to use cache
    cache_type: str = "deepcache" # cache type
    no_cache_block_id: Optional[range] = None # block ids to skip
    cache_start_step: int = 11 # start step to skip
    cache_end_step: int = 45 # end step to skip
    total_steps: int = 50 # total steps
    cache_step_interval: int = 4 # step interval to skip

    use_fp8_gemm: bool = False  # whether to use fp8 gemm
    quant_type: str = "fp8-per-token-sgl"  # fp8 quantization type
    include_patterns: list = field(default_factory=lambda: ["double_blocks"])  # include patterns for fp8 gemm



__infer_state = None

def parse_range(value):
    if not value:
        return []
    
    result = set()
    # 先按逗号分割，支持形式 (1) 和 (3) 的初步拆分
    parts = value.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 处理范围形式 (2) 如 "1-3" 或 (3) 中的 "3-5"
            start, end = map(int, part.split('-'))
            result.update(range(start, end + 1))
        elif part:
            # 处理单个数字
            result.add(int(part))
            
    # 返回排序后的列表
    return sorted(list(result))

def initialize_infer_state(args):
    state = InferState()
    # Mapping from CLI argument names to InferState field names
    mapping = {
        'use_sageattn': 'enable_sageattn'
    }
    
    for field_name in state.__dataclass_fields__.keys():
        source_name = next((k for k, v in mapping.items() if v == field_name), field_name)
        if hasattr(args, source_name):
            val = getattr(args, source_name)
            if field_name in ['sage_blocks_range', 'no_cache_block_id']:
                val = parse_range(val)
            elif field_name == 'include_patterns' and isinstance(val, str):
                val = [p.strip() for p in val.split(',') if p.strip()]
            setattr(state, field_name, val)

    __infer_state = state
    return __infer_state

def get_infer_state():
    return __infer_state
