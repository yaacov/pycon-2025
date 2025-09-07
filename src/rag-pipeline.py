# RAG pipeline using vector store and IBM Granite LLM

# This script will load a vector store from mtv.md, use it for retrieval, and answer a question using IBM Granite LLM via transformers and optimum

# Steps:
# 1. Read and split mtv.md
# 2. Create vector store (FAISS)
# 3. Use RAG pipeline to answer a question
# 4. Print statistics (timing, etc.)

import time
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from transformers import AutoTokenizer, set_seed
from optimum.intel import OVModelForCausalLM
import torch
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from utils import print_header, print_time_metric, print_metric, print_content, print_inference_stats, print_generated_output

model_path = "ibm-granite/granite-3.3-2b-instruct"
device = "cpu"
question = "Can you tell me about MTV."
embedding_model_path = "ibm-granite/granite-embedding-30m-english"

embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

model = OVModelForCausalLM.from_pretrained(
    model_path,
    export=True,
    device=device,
    ov_config={"PERFORMANCE_HINT": "LATENCY"}
)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# A. Get context from vector store
print_header("A. RETRIEVING CONTEXT FROM VECTOR STORE")
retrieval_start = time.time()
retrieved_docs = retriever.invoke(question)
context = "\n".join([doc.page_content for doc in retrieved_docs])
retrieval_end = time.time()
retrieval_time = retrieval_end - retrieval_start
print_time_metric("Retrieval time", retrieval_time)
print_metric("Retrieved", f"{len(retrieved_docs)} document(s)")
print("Context:")
print_content(context)

# B. Build question with context prompt
print("")
print_header("B. BUILDING QUESTION WITH CONTEXT PROMPT")
prompt_start = time.time()
conv = [{
    "role": "user", 
    "content": f"Context: {context}\n\nQuestion: {question}"
}]
input_ids = tokenizer.apply_chat_template(conv, return_tensors="pt", thinking=False, return_dict=True, add_generation_prompt=True).to(device)
prompt_end = time.time()
prompt_time = prompt_end - prompt_start
print_time_metric("Prompt building time", prompt_time)
print("Full prompt:")
print_content(tokenizer.decode(input_ids['input_ids'][0], skip_special_tokens=True))

# C. Use exact verbatim code from granite-instruct-openvino.py
print("")
print_header("C. INFERENCE USING GRANITE OPENVINO")
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
