import torch
from transformers import PreTrainedModel
from .configuration_wesamoyo import WesamoyoConfig

class WesamoyoForCausalLM(PreTrainedModel):
    config_class = WesamoyoConfig
    
    def __init__(self, config):
        super().__init__(config)
        
        from model import WesamoyoTransformer, WesamoyoArgs
        
        config_dict = config.to_dict()
        
        # FIXED: Added "torchscript" and more
        keys_to_remove = [
            "_name_or_path", "transformers_version", "torch_dtype",
            "architectures", "model_type", "auto_map",
            "return_dict", "torchscript", "output_hidden_states",
            "output_attentions", "use_cache", "attention_bias",
            "attention_dropout", "bos_token_id", "eos_token_id",
            "hidden_act", "initializer_range", "rms_norm_eps",
            "tie_word_embeddings", "torchscript" 
        ]
        for key in keys_to_remove:
            config_dict.pop(key, None)
        
        args = WesamoyoArgs(**config_dict)
        self.model = WesamoyoTransformer(args)
        
    def forward(self, input_ids, **kwargs):
        return self.model(input_ids)