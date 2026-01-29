from transformers import PretrainedConfig

class WesamoyoConfig(PretrainedConfig):
    model_type = "wesamoyo"
    
    def __init__(
        self,
        vocab_size=16384,
        dim=512,
        inter_dim=512,
        moe_inter_dim=512,
        n_layers=6,
        n_dense_layers=1,
        n_heads=8,
        n_routed_experts=64,
        n_shared_experts=2,
        n_activated_experts=6,
        n_expert_groups=1,
        n_limited_groups=1,
        route_scale=1.0,
        score_func="softmax",
        q_lora_rank=0,
        kv_lora_rank=512,
        qk_nope_head_dim=128,
        qk_rope_head_dim=64,
        v_head_dim=128,
        dtype="bf16",
        scale_fmt=None,
        max_batch_size=8,
        max_seq_len=16384,
        original_seq_len=4096,
        rope_theta=10000.0,
        rope_factor=40.0,
        beta_fast=32,
        beta_slow=1,
        mscale=1.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        # SET ALL PARAMETERS
        self.vocab_size = vocab_size
        self.dim = dim
        self.inter_dim = inter_dim
        self.moe_inter_dim = moe_inter_dim
        self.n_layers = n_layers
        self.n_dense_layers = n_dense_layers
        self.n_heads = n_heads
        self.n_routed_experts = n_routed_experts
        self.n_shared_experts = n_shared_experts
        self.n_activated_experts = n_activated_experts
        self.n_expert_groups = n_expert_groups
        self.n_limited_groups = n_limited_groups
        self.route_scale = route_scale
        self.score_func = score_func
        self.q_lora_rank = q_lora_rank
        self.kv_lora_rank = kv_lora_rank
        self.qk_nope_head_dim = qk_nope_head_dim
        self.qk_rope_head_dim = qk_rope_head_dim
        self.v_head_dim = v_head_dim
        self.dtype = dtype
        self.scale_fmt = scale_fmt
        self.max_batch_size = max_batch_size
        self.max_seq_len = max_seq_len
        self.original_seq_len = original_seq_len
        self.rope_theta = rope_theta
        self.rope_factor = rope_factor
        self.beta_fast = beta_fast
        self.beta_slow = beta_slow
        self.mscale = mscale