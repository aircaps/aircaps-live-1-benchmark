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
    num_bytes: 4836436489.0
    num_examples: 31527
  download_size: 4837751629
  dataset_size: 4836436489.0
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
---

Testing dataset for Smart Turn v3.2.

Thank you to the following contributors whose audio samples are included in this dataset:

* The Pipecat team
* Liva AI: https://www.theliva.ai/
* Midcentury: https://www.midcentury.xyz/
* MundoAI: https://mundoai.world/

Also, thank you to the following people for the CC-0 background noise sample data which has been used in this dataset:

* https://freesound.org/people/4team/sounds/214995/
* https://freesound.org/people/tomhannen/sounds/698090/
* https://freesound.org/people/craigsmith/sounds/675073/
* https://freesound.org/people/mrmayo/sounds/351265/
* https://freesound.org/people/martats/sounds/156983/
* https://freesound.org/people/Duisterwho/sounds/642196/
* https://freesound.org/people/el_boss/sounds/635967/
* https://freesound.org/people/clivew/sounds/577104/
* https://freesound.org/people/dbspin/sounds/396678/
* https://freesound.org/people/nikitralala/sounds/204406/
* https://freesound.org/people/outandaboutworcester/sounds/670290/
* https://freesound.org/people/bengomori/sounds/381697/
* https://freesound.org/people/wcarcary/sounds/155665/
* https://freesound.org/people/kentspublicdomain/sounds/324668/
* https://freesound.org/people/Hmuryj_sound-Kirill_Rozhkov/sounds/616358/
* https://freesound.org/people/kyles/sounds/451024/
* https://freesound.org/people/edgardomoreno/sounds/450361/
* https://freesound.org/people/chimerical/sounds/104279/
* https://freesound.org/people/lukabailen/sounds/723794/
* https://freesound.org/people/mrmayo/sounds/351264/
* https://freesound.org/people/outandaboutworcester/sounds/670289/
* https://freesound.org/people/outandaboutworcester/sounds/670291/
* https://freesound.org/people/Vecera_999/sounds/706805/
* https://freesound.org/people/Seamonstar/sounds/718604/
* https://freesound.org/people/JW_Audio/sounds/808266/
* https://freesound.org/people/Talitha5/sounds/509950/
* https://freesound.org/people/kyles/sounds/451105/
* https://freesound.org/people/Ultra-Edward/sounds/823831/
* https://freesound.org/people/seriousmedium33/sounds/543858/
* https://freesound.org/people/_vk/sounds/221848/
* https://freesound.org/people/holidayparade/sounds/278154/
* https://freesound.org/people/felix.blume/sounds/710089/
* https://freesound.org/people/kyles/sounds/454413/
* https://freesound.org/people/Geoff-Bremner-Audio/sounds/705787/
* https://freesound.org/people/Sauron974/sounds/273624/
* https://freesound.org/people/Chelly01/sounds/541117/
* https://freesound.org/people/TRP/sounds/577495/
* https://freesound.org/people/servozero/sounds/636268/
* https://freesound.org/people/Garuda1982/sounds/633121/
* https://freesound.org/people/joche.fernandez/sounds/460014/

## License

This dataset is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See the [LICENSE](https://huggingface.co/datasets/pipecat-ai/smart-turn-data-v3.2-test/blob/main/LICENSE) file for the full license text.
