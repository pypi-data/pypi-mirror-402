"""
Houndtid Transformers - Official SDK
"""
from .configuration_wesamoyo import WesamoyoConfig 
from .modeling_wesamoyo import WesamoyoForCausalLM  

# GLOBAL REGISTRATION
from transformers import AutoConfig, AutoModelForCausalLM

AutoConfig.register("wesamoyo", WesamoyoConfig)
AutoModelForCausalLM.register(WesamoyoConfig, WesamoyoForCausalLM)

__version__ = "1.0.0"
__all__ = ["WesamoyoConfig", "WesamoyoForCausalLM"]