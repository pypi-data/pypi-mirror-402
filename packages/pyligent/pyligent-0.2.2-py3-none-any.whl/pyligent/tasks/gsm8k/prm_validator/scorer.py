import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

# Import your PRM class and SYSTEM exactly as you defined them
# (i.e., from the file where you put PRMScorer and SYSTEM).
# If your module path differs, adjust this import.

SYSTEM = ""


class PRMScorer:
    def __init__(self, model_name="Qwen/Qwen2.5-Math-PRM-7B", device="auto"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_name,
            device_map=device,
            dtype=torch.bfloat16,
            trust_remote_code=True,
        ).eval()
        self.step_sep = "<extra_0>"
        self.step_sep_id = self.tokenizer.encode(self.step_sep)[0]

    @torch.no_grad()
    def step_reward(self, question, path: str, action: str) -> float:
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"{question}\n\nPATH:\n{path}\n\nNext action?"},
            {"role": "assistant", "content": action + self.step_sep},
        ]
        convo = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        # print(convo)
        input_ids = self.tokenizer.encode(convo, return_tensors="pt").to(
            self.model.device
        )
        outputs = self.model(input_ids=input_ids, use_cache=False)
        logits = outputs[0]  # (1, seq_len, 2)
        token_mask = input_ids == self.step_sep_id  # (1, seq_len)
        probs = F.softmax(logits, dim=-1) * token_mask.unsqueeze(-1)  # (1, seq_len, 2)
        pos_probs = probs[0][token_mask[0]].view(-1, 2)[:, 1]  # (#steps, )
        return float(pos_probs[-1].item())  # reward for the newest step
