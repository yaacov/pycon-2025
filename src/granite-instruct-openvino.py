from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer, set_seed
import time
from utils import print_inference_stats, print_generated_output

model_path="ibm-granite/granite-3.3-2b-instruct"
device="cpu"

# Using Optimum Intel for CPU optimization
# This will automatically convert to OpenVINO format for better CPU performance
model = OVModelForCausalLM.from_pretrained(
    model_path,
    export=True,  # Export to OpenVINO format if not already done
    device=device,
    ov_config={"PERFORMANCE_HINT": "LATENCY"}  # Optimize for latency
)
tokenizer = AutoTokenizer.from_pretrained(
        model_path
)

conv = [{
    "role": "user", 
    "content":"Can you tell me about MTV."
}]

input_ids = tokenizer.apply_chat_template(conv, return_tensors="pt", thinking=False, return_dict=True, add_generation_prompt=True).to(device)

set_seed(42)

# Start timing
start_time = time.time()

output = model.generate(
    **input_ids,
    max_new_tokens=1024,
)

# End timing
end_time = time.time()
inference_time = end_time - start_time

prediction = tokenizer.decode(output[0, input_ids["input_ids"].shape[1]:], skip_special_tokens=True)

# Calculate statistics
input_tokens = input_ids["input_ids"].shape[1]
output_tokens = output.shape[1] - input_tokens
total_tokens = output.shape[1]
tokens_per_second = output_tokens / inference_time

# Print results and statistics
print_inference_stats(inference_time, input_tokens, output_tokens, total_tokens, tokens_per_second)
print_generated_output(prediction)
