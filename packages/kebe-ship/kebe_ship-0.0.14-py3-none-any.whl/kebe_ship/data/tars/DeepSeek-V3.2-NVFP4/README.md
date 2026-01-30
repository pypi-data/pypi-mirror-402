---
pipeline_tag: text-generation
base_model:
- deepseek-ai/DeepSeek-V3.2
license: mit
library_name: Model Optimizer
tags:
- nvidia
- ModelOpt
- DeepSeekV3.2
- quantized
- NVFP4
- nvfp4
---

# Model Overview

## Description:
The NVIDIA DeepSeek-V3.2-NVFP4 model is a quantized version of DeepSeek AI’s DeepSeek-V3.2 model, an autoregressive language model that uses an optimized Transformer architecture. For more information, refer to the [DeepSeek-V3.2 model card](https://huggingface.co/deepseek-ai/DeepSeek-V3.2). The NVIDIA DeepSeek-V3.2-NVFP4 model was quantized using the [TensorRT Model Optimizer](https://github.com/NVIDIA/TensorRT-Model-Optimizer).

This model is ready for commercial/non-commercial use.  <br>

## Third-Party Community Consideration
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party’s requirements for this application and use case; see link to Non-NVIDIA [(DeepSeek V3.2) Model Card](https://huggingface.co/deepseek-ai/DeepSeek-V3.2).

### License/Terms of Use:
[MIT](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/mit.md)

### Deployment Geography:
Global <br>

### Use Case:
Developers looking to take off the shelf, pre-quantized models for deployment in AI Agent systems, chatbots, RAG systems, and other AI-powered applications. <br>

### Release Date:
Huggingface 01/20/2026 via https://huggingface.co/nvidia/DeepSeek-V3.2-NVFP4 <br>

## Model Architecture:
**Architecture Type:** Transformers  <br>
**Network Architecture:** DeepseekV32ForCausalLM <br>
**This model was developed based on [DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) <br>
**Number of model parameters: Undisclosed. <br>

## Input:
**Input Type(s):** Text <br>
**Input Format(s):** String <br>
**Input Parameters:** 1D (One-Dimensional): Sequences <br>
**Other Properties Related to Input:** DeepSeek recommends adhering to the following configurations when utilizing the DeepSeek-V3.2 series models, including benchmarking, to achieve the expected performance: \

- For local deployment, we recommend setting the sampling parameters to temperature = 1.0, top_p = 0.95. <br>

## Output:
**Output Type(s):** Text <br>
**Output Format:** String <br>
**Output Parameters:** 1D (One-Dimensional): Sequences <br>
**Other Properties Related to Output:** N/A <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA’s hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>

## Software Integration:
**Runtime Engine(s):** <br>
* TensorRT-LLM <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Blackwell <br>

**Preferred Operating System(s):** <br>
* Linux <br>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment

## Model Version(s):
** The model is quantized with nvidia-modelopt **v0.41.0**  <br>

## Training, Testing, and Evaluation Datasets:

## Calibration Dataset: 
** Link: [cnn_dailymail](https://huggingface.co/datasets/abisee/cnn_dailymail), [Nemotron-Post-Training-Dataset-v2](https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v2) <br>
** Data collection method: Automated. <br>
** Labeling method: Automated. <br>

## Training Datasets:
** Data Collection Method by Dataset: Undisclosed <br>
** Labeling Method by Dataset: Undisclosed<br>
** Properties: Undisclosed

## Testing Dataset:
** Data Collection Method by Dataset: Undisclosed <br>
** Labeling Method by Dataset: Undisclosed <br>
** Properties: Undisclosed <br>

## Evaluation Dataset: 
* Datasets: MMLU Pro, GPQA Diamond, LiveCodeBench V6, SciCode, AIME 2025 <br>
** Data collection method: Hybrid: Automated, Human <br>
** Labeling method: Hybrid: Human, Automated <br>


## Inference:
**Acceleration Engine:** TensorRT-LLM <br>
**Test Hardware:** B200 <br>

## Post Training Quantization
This model was obtained by quantizing the weights and activations of DeepSeek V3.2 to NVFP4 data type, ready for inference with TensorRT-LLM. Only the weights and activations of the linear operators within transformer blocks are quantized. This optimization reduces the number of bits per parameter from 8 to 4, reducing the disk size and GPU memory requirements by approximately 1.66x.

## Usage

### Deploy with TensorRT-LLM

To deploy the quantized NVFP4 checkpoint with [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) LLM API, follow the sample codes below (you need 8xB200 GPU and TensorRT LLM version 1.2.0rc8 or above):

* LLM API sample usage:
```
from tensorrt_llm import LLM, SamplingParams

def main():

    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]
    sampling_params = SamplingParams(temperature=1.0, top_p=0.95)

    llm = LLM(
        model="nvidia/DeepSeek-V3.2-NVFP4",
        tensor_parallel_size=8,
        enable_attention_dp=True,
        custom_tokenizer="deepseek_v32"
    )

    outputs = llm.generate(prompts, sampling_params)

    # Print the outputs.
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")


# The entry point of the program needs to be protected for spawning processes.
if __name__ == "__main__":
    main()

```

### Evaluation
The accuracy benchmark results are presented in the table below:
<table>
  <tr>
   <td><strong>Precision</strong>
   </td>
   <td><strong>MMLU Pro</strong>
   </td>
   <td><strong>GPQA Diamond</strong>
   </td>
   <td><strong>LiveCodeBench V6</strong>
   </td>
   <td><strong>SciCode</strong>
   </td>
   <td><strong>AIME 2025</strong>
   </td>
  </tr>
  <tr>
   <td>FP8
   </td>
   <td>0.802
   </td>
   <td>0.849
   </td>
   <td>0.756
   </td>
   <td>0.391
   </td>
   <td>0.934
   </td>
  </tr>
  <tr>
   <td>NVFP4
   </td>
   <td>0.799
   </td>
   <td>0.835
   </td>
   <td>0.756
   </td>
   <td>0.401
   </td>
   <td>0.923
   </td>
  </tr>
  <tr>
</table>

> Baseline: [DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2).
> Benchmarked with temperature=1.0, top_p=0.95, max num tokens 64000

## Model Limitations:
The base model was trained on data that contains toxic language and societal biases originally crawled from the internet. Therefore, the model may amplify those biases and return toxic responses especially when prompted with toxic prompts. The model may generate answers that may be inaccurate, omit key information, or include irrelevant or redundant text producing socially unacceptable or undesirable text, even if the prompt itself does not include anything explicitly offensive.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).