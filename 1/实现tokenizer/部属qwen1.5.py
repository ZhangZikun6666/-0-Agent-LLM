import torch
from transformers import AutoModelForCausalLM,AutoTokenizer

#指定模型ID
model_id = "Qwen/Qwen1.5-0.5B-Chat"

#设置设备 优先使用GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

#加载分词器
tokenizer = AutoTokenizer.from_pretrained(model_id)

#加载模型
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

print("模型和分词器加载完毕")

messages = [
    {"role":"system","content":"You are a helpful assistant"},
    {"role":"user","content":"你好,请介绍你自己"}
]

#使用分词器的模板格式化输入
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

#编码输入文本
model_inputs = tokenizer([text],return_tensors="pt").to(device)

print("编码后输入文本")
print(model_inputs)

