---
license: cc-by-4.0
dataset_info:
  features:
  - name: audio
    dtype: audio
  - name: id
    dtype: string
  - name: language
    dtype: string
  - name: endpoint_bool
    dtype: bool
  - name: midfiller
    dtype: bool
  - name: endfiller
    dtype: bool
  - name: synthetic
    dtype: bool
  - name: spoken_text
    dtype: 'null'
  - name: dataset
    dtype: string
  splits:
  - name: train
    num_bytes: 38491641356.0
    num_examples: 270429
  download_size: 36750468369
  dataset_size: 38491641356.0
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
---

Training dataset for Smart Turn v3.1.

Thank you to the following contributors whose audio samples are included in this dataset:

* The Pipecat team
* Liva AI: https://www.theliva.ai/
* Midcentury: https://www.midcentury.xyz/
* MundoAI: https://mundoai.world/

## License

This dataset is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See the [LICENSE](https://huggingface.co/datasets/pipecat-ai/smart-turn-data-v3.1-train/blob/main/LICENSE) file for the full license text.
