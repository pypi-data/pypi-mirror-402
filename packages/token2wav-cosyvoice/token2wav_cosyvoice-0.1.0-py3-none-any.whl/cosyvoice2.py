"""
Compatibility module for cosyvoice2 classes referenced in YAML configs.
This module provides backward compatibility for hyperpyyaml imports.
"""

# Import all classes that might be referenced in YAML configs
from cosyvoice.flow.flow import CausalMaskedDiffWithXvec, MaskedDiffWithXvec
from cosyvoice.flow.flow_matching import ConditionalCFM, CausalConditionalCFM
from cosyvoice.hifigan.generator import HiFTGenerator
from cosyvoice.llm.llm import Qwen2LM, TransformerLM
from cosyvoice.transformer.upsample_encoder import UpsampleConformerEncoder
from cosyvoice.cli.model import CosyVoice2Model, CosyVoiceModel

# Make classes available at module level for hyperpyyaml
__all__ = [
    'CausalMaskedDiffWithXvec',
    'MaskedDiffWithXvec',
    'ConditionalCFM',
    'CausalConditionalCFM',
    'HiFTGenerator',
    'Qwen2LM',
    'TransformerLM',
    'UpsampleConformerEncoder',
    'CosyVoice2Model',
    'CosyVoiceModel',
]
