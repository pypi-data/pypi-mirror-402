from transformers import PretrainedConfig

class WesamoyoConfig(PretrainedConfig):
    model_type = "wesamoyo"
    
    def __init__(
        self,
        vocab_size=129280,
        dim=7168,
        inter_dim=18432,
        moe_inter_dim=2048,
        n_layers=61,
        n_dense_layers=3,
        n_heads=128,
        n_routed_experts=256,
        n_shared_experts=1,
        n_activated_experts=8,
        n_expert_groups=8,
        n_limited_groups=4,
        route_scale=2.5,
        score_func="sigmoid",
        q_lora_rank=1536,
        kv_lora_rank=512,
        qk_nope_head_dim=128,
        qk_rope_head_dim=64,
        v_head_dim=128,
        dtype="fp8",
        scale_fmt=None,
        max_batch_size=8,
        max_seq_len=16384,
        **kwargs
    ):
        super().__init__(**kwargs)
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