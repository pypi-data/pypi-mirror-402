import torch
import torch.nn as nn
from transformers import PreTrainedModel
from .configuration_wesamoyo import WesamoyoConfig 

class WesamoyoForCausalLM(PreTrainedModel):
    config_class = WesamoyoConfig
    
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        
        # Architecture components
        self.embedding = nn.Embedding(config.vocab_size, config.dim)
        self.output = nn.Linear(config.dim, config.vocab_size)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
    
    def forward(self, input_ids, attention_mask=None, **kwargs):
        embeddings = self.embedding(input_ids)
        logits = self.output(embeddings)
        
        return type('Output', (), {'logits': logits})()
    
    def prepare_inputs_for_generation(self, input_ids, **kwargs):
        return {"input_ids": input_ids}