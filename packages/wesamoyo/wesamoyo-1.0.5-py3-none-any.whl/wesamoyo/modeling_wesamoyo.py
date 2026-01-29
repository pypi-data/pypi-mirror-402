import torch
from transformers import PreTrainedModel
from .configuration_wesamoyo import WesamoyoConfig

class WesamoyoForCausalLM(PreTrainedModel):
    config_class = WesamoyoConfig
    
    def __init__(self, config):
        super().__init__(config)
        
        # Import your REAL model.py
        from model import WesamoyoTransformer, WesamoyoArgs
        
        # Convert config to args that match your 293M model
        config_dict = config.to_dict()
        
        # Remove Hugging Face specific keys
        keys_to_remove = [
            "_name_or_path", "transformers_version", "torch_dtype",
            "architectures", "model_type", "auto_map"
        ]
        for key in keys_to_remove:
            config_dict.pop(key, None)
        
        # Create args for your REAL model
        args = WesamoyoArgs(**config_dict)
        self.model = WesamoyoTransformer(args)
        
    def forward(self, input_ids, **kwargs):
        return self.model(input_ids)