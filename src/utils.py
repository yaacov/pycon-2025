# Utility functions for colored output and formatting

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[97m'

def print_separator():
    """Print a colored separator line"""
    print(f"{Colors.OKBLUE}{'=' * 60}{Colors.ENDC}")

def print_header(text):
    """Print a colored header with separators"""
    print_separator()
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print_separator()

def print_metric(label, value, color=Colors.OKGREEN):
    """Print a metric with colored label and value"""
    print(f"{Colors.OKCYAN}{label}: {color}{value}{Colors.ENDC}")

def print_time_metric(label, value):
    """Print a time metric with warning color"""
    print_metric(label, f"{value:.2f} seconds", Colors.WARNING)

def print_content(content, color=Colors.OKGREEN):
    """Print content in specified color"""
    print(f"{color}{content}{Colors.ENDC}")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.OKGREEN}{Colors.BOLD}{message}{Colors.ENDC}")

def print_tokens_per_second(label, value):
    """Print tokens per second metric with warning color"""
    print_metric(label, f"{value:.2f} tokens/second", Colors.WARNING)

def print_inference_stats(inference_time, input_tokens, output_tokens, total_tokens, tokens_per_second):
    """Print standardized inference statistics"""
    print_header("INFERENCE STATISTICS")
    print_time_metric("Inference time", inference_time)
    print_metric("Input tokens", input_tokens)
    print_metric("Generated tokens", output_tokens)
    print_metric("Total tokens", total_tokens)
    print_tokens_per_second("Tokens per second", tokens_per_second)

def print_generated_output(output):
    """Print generated output with header"""
    print_header("GENERATED OUTPUT")
    print_content(output, Colors.WHITE)
