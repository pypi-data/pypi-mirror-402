import tinker

sc = tinker.ServiceClient()
tc = sc.create_lora_training_client(
    base_model="openai/gpt-oss-20b",
    rank=1,
    seed=0,
    train_mlp=False,
    train_attn=False,
    train_unembed=False,
)
path = tc.save_weights_for_sampler(name="gpt-oss-20b-base-like").result().path
print(path)