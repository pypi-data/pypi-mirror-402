from transformers import PretrainedConfig

class WesamoyoConfig(PretrainedConfig):
    model_type = "wesamoyo"
    
    def __init__(
        self,
        vocab_size=16384,        # FIXED: Your model is 16K vocab
        dim=512,                 # FIXED: Your model is 512 dim
        inter_dim=512,           # FIXED: Your model
        moe_inter_dim=512,       # FIXED: Your model
        n_layers=6,              # FIXED: Your model has 6 layers
        n_dense_layers=1,        # FIXED: Your model
        n_heads=8,               # FIXED: Your model has 8 heads
        n_routed_experts=64,     # FIXED: Your model has 64 experts
        n_shared_experts=2,      # FIXED: Your model has 2 shared
        n_activated_experts=6,   # FIXED: Your model activates 6
        n_expert_groups=1,       # FIXED: Your model
        n_limited_groups=1,      # FIXED: Your model
        route_scale=1.0,         # FIXED: Your model
        score_func="softmax",    # FIXED: Your model uses softmax
        q_lora_rank=0,           # FIXED: Your model
        kv_lora_rank=512,        # FIXED: Your model
        qk_nope_head_dim=128,    # FIXED: Your model
        qk_rope_head_dim=64,     # FIXED: Your model
        v_head_dim=128,          # FIXED: Your model
        dtype="bf16",            # FIXED: Your model uses bf16
        scale_fmt=None,          # FIXED: Your model
        max_batch_size=8,        # FIXED: Your model
        max_seq_len=16384,       # FIXED: Your model is 16K context
        original_seq_len=4096,   # FIXED: Your YARN params
        rope_theta=10000.0,      # FIXED: Your YARN params
        rope_factor=40.0,        # FIXED: Your YARN params
        beta_fast=32,            # FIXED: Your YARN params
        beta_slow=1,             # FIXED: Your YARN params
        mscale=1.0,              # FIXED: Your YARN params
        **kwargs
    ):
        super().__init__(**kwargs)
        # Set ALL params to match your actual 293M model
        self.vocab_size = vocab_size
        self.dim = dim
        # ... set all 25+ parameters to match your model