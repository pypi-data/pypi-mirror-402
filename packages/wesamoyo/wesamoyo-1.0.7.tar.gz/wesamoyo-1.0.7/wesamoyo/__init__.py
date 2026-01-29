"""
Houndtid Transformers - Official SDK
"""
from .configuration_wesamoyo import WesamoyoConfig 
from .modeling_wesamoyo import WesamoyoForCausalLM  

__version__ = "1.0.7"
__all__ = ["WesamoyoConfig", "WesamoyoForCausalLM"]

# LAZY REGISTRATION - only when needed
def register_with_transformers():
    """Register Wesamoyo with Hugging Face transformers"""
    from transformers import AutoConfig, AutoModelForCausalLM
    AutoConfig.register("wesamoyo", WesamoyoConfig)
    AutoModelForCausalLM.register(WesamoyoConfig, WesamoyoForCausalLM)

# Auto-register if transformers is available
try:
    import transformers
    register_with_transformers()
except ImportError:
    pass