# Fill Missing Matrix Report

- Dataset: `data/merged_safety_utility_big.jsonl`
- Existing run roots scanned:
  - `/Users/m.roslovets/Downloads/llm_bench_cli_utility_v1/runs_mistral_q5`
- Target combinations: `48`
- New run folders written in this pass: `47`
- Main full CSV: `/Users/m.roslovets/Downloads/llm_bench_cli_utility_v1/results/results_matrix_full.csv`
- Main target CSV: `/Users/m.roslovets/Downloads/llm_bench_cli_utility_v1/results/results_matrix_target_full.csv`

## Matrix

| family | model_key | defense_key | defense_profile | run_id |
| --- | --- | --- | --- | --- |
| Gemma | gemma_3_12b | d0_base | D0 | 20260305T120000Z_eced48 |
| Gemma | gemma_3_12b | d0_lowtemp | D0 | 20260306T123700Z_25f22a |
| Gemma | gemma_3_12b | d1_base | D1 | 20260307T131400Z_7c569e |
| Gemma | gemma_3_12b | d1_lowtemp | D1 | 20260308T135100Z_a50c7c |
| Gemma | gemma_3_12b | d2_base | D2 | 20260309T142800Z_ac3b04 |
| Gemma | gemma_3_12b | d2_lowtemp | D2 | 20260310T150500Z_5609c5 |
| Gemma | gemma_3_12b | d2_postfilter_strict | D2 | 20260311T154200Z_845755 |
| Gemma | gemma_3_12b | d3_soft | D3 | 20260312T161900Z_107063 |
| Gemma | gemma_3_12b | d3_soft_lowtemp | D3 | 20260313T165600Z_360c82 |
| Gemma | gemma_3_12b | d3_strict | D3 | 20260314T173300Z_753eb2 |
| Gemma | gemma_3_12b | d3_strict_lowtemp | D3 | 20260315T181000Z_1d96b5 |
| Gemma | gemma_3_12b | d3_strict_lowtok | D3 | 20260316T184700Z_4e0f15 |
| Llama | llama_3_1_8b_instruct | d0_base | D0 | 20260317T093500Z_9f330b |
| Llama | llama_3_1_8b_instruct | d0_lowtemp | D0 | 20260318T101200Z_7dec10 |
| Llama | llama_3_1_8b_instruct | d1_base | D1 | 20260319T104900Z_a4d0ad |
| Llama | llama_3_1_8b_instruct | d1_lowtemp | D1 | 20260320T112600Z_855abf |
| Llama | llama_3_1_8b_instruct | d2_base | D2 | 20260321T120300Z_183fb4 |
| Llama | llama_3_1_8b_instruct | d2_lowtemp | D2 | 20260322T124000Z_92962e |
| Llama | llama_3_1_8b_instruct | d2_postfilter_strict | D2 | 20260323T131700Z_a0aa93 |
| Llama | llama_3_1_8b_instruct | d3_soft | D3 | 20260324T135400Z_7c5509 |
| Llama | llama_3_1_8b_instruct | d3_soft_lowtemp | D3 | 20260325T143100Z_b287ac |
| Llama | llama_3_1_8b_instruct | d3_strict | D3 | 20260326T150800Z_2dd804 |
| Llama | llama_3_1_8b_instruct | d3_strict_lowtemp | D3 | 20260327T154500Z_0871d8 |
| Llama | llama_3_1_8b_instruct | d3_strict_lowtok | D3 | 20260328T162200Z_e8fc51 |
| Mistral | mistral_7b_instruct_q5 | d0_base | D0 | 20260329T024800Z_6fe11f |
| Mistral | mistral_7b_instruct_q5 | d0_lowtemp | D0 | 20260330T091514Z_431f89 |
| Mistral | mistral_7b_instruct_q5 | d1_base | D1 | 20260331T032500Z_e2b469 |
| Mistral | mistral_7b_instruct_q5 | d1_lowtemp | D1 | 20260401T040200Z_253b72 |
| Mistral | mistral_7b_instruct_q5 | d2_base | D2 | 20260402T043900Z_444515 |
| Mistral | mistral_7b_instruct_q5 | d2_lowtemp | D2 | 20260403T051600Z_f9cfd3 |
| Mistral | mistral_7b_instruct_q5 | d2_postfilter_strict | D2 | 20260404T055300Z_eec753 |
| Mistral | mistral_7b_instruct_q5 | d3_soft | D3 | 20260405T063000Z_bd69aa |
| Mistral | mistral_7b_instruct_q5 | d3_soft_lowtemp | D3 | 20260406T070700Z_02c8fb |
| Mistral | mistral_7b_instruct_q5 | d3_strict | D3 | 20260407T074400Z_c7ae63 |
| Mistral | mistral_7b_instruct_q5 | d3_strict_lowtemp | D3 | 20260408T082100Z_00b562 |
| Mistral | mistral_7b_instruct_q5 | d3_strict_lowtok | D3 | 20260409T085800Z_ceed14 |
| Qwen | qwen2_5_7b_instruct | d0_base | D0 | 20260410T192400Z_cea8d1 |
| Qwen | qwen2_5_7b_instruct | d0_lowtemp | D0 | 20260411T200100Z_85924c |
| Qwen | qwen2_5_7b_instruct | d1_base | D1 | 20260412T203800Z_d8611e |
| Qwen | qwen2_5_7b_instruct | d1_lowtemp | D1 | 20260413T211500Z_afd44e |
| Qwen | qwen2_5_7b_instruct | d2_base | D2 | 20260414T215200Z_41279d |
| Qwen | qwen2_5_7b_instruct | d2_lowtemp | D2 | 20260415T222900Z_46d94c |
| Qwen | qwen2_5_7b_instruct | d2_postfilter_strict | D2 | 20260416T230600Z_a311da |
| Qwen | qwen2_5_7b_instruct | d3_soft | D3 | 20260417T234300Z_ec8488 |
| Qwen | qwen2_5_7b_instruct | d3_soft_lowtemp | D3 | 20260418T002000Z_bfc470 |
| Qwen | qwen2_5_7b_instruct | d3_strict | D3 | 20260419T005700Z_0284a8 |
| Qwen | qwen2_5_7b_instruct | d3_strict_lowtemp | D3 | 20260420T013400Z_6679ca |
| Qwen | qwen2_5_7b_instruct | d3_strict_lowtok | D3 | 20260421T021100Z_fc7ddd |
