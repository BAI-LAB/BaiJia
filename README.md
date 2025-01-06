# BaiJia: A Large-Scale Role-Playing Agent Corpus of Chinese Historical Characters

BaiJia is a role-playing agent corpus focused on Chinese historical characters. It aims to enhance the role-playing capabilities of large language models (LLMs) by providing high-quality, low-resource data.

## Project Structure

- **Baijia_Lite**: A publicly available portion of the dataset for experimentation and evaluation.
- **Eval_Question**: A set of evaluation questions to assess the performance of LLMs.
- **Eval_Resume**: A collection of character resumes used for role-playing evaluations.

## Evaluation Dimensions

We provide six comprehensive dimensions to evaluate the role-playing performance of LLMs:

1. **Character Consistency (CC)**  
   - Alignment with character background.
   - Alignment with historical dynasty context.
2. **Dialogue Ability (DA)**  
   - Coherence and logical flow of dialogue.  
   - Interactivity in conversations.
3. **Character Appeal (CA)**  
   - Charm and attractiveness of the character.  
   - Emotional impact during interactions.
4. **Emotional Expression & Intellectual Depth (EI)**  
   - Authentic emotional expressions.  
   - Intellectual and philosophical insights.
5. **Creativity & Role Depth Expansion (CR)**  
   - Character personality and innovative thinking.  
   - Complexity and further development of the character.
6. **Cultural & Historical Appropriateness (CHA)**  
   - Language style matching character identity and historical era.  
   - Alignment with the historical and cultural context of the era.

## Fine-Tuning with Baijia_Lite

We used **Demo_Baijia** for supervised fine-tuning (SFT) and published the adapter model on Hugging Face. You can find the model at the following link:

**[Baijia_Lite Adapter on Hugging Face](https://huggingface.co/datasets/Jiazhengg/BaiJia_Demo/tree/main)**

### Evaluation Results After Fine-Tuning

After using Demo_Baijia data for SFT, the adapter's performance was evaluated based on the six key dimensions. The table below shows the scores of the base model (Qwen) and the fine-tuned model (BaiJia_Demo), along with the percentage improvement:

| Dimension | Qwen Score | Baijia_Lite Score | Improvement (%) |
|-----------|------------|-------------------|-----------------|
| **CC**    | 4.10       | 4.41              | **7.56%**       |
| **DA**    | 4.20       | 4.30              | **2.38%**       |
| **CA**    | 4.04       | 4.18              | **3.47%**       |
| **EI**    | 4.67       | 4.69              | **0.49%**       |
| **CR**    | 3.94       | 4.04              | **2.53%**       |
| **CHA**   | 4.39       | 4.48              | **2.05%**       |

These results demonstrate the improved ability of the BaiJia_Demo fine-tuned adapter in all dimensions, with notable gains in **Character Consistency (CC)** and **Character Appeal (CA)**.

## Usage Instructions

1. Use **Baijia_Lite** as the dataset for SFT.
2. Combine **Eval_Question** and **Eval_Resume** to evaluate the role-playing ability of your language models.
3. Evaluate models based on the six key dimensions mentioned above.
## Citation

If you find this project useful, please consider citing our paper:

```bibtex
@misc{bai2024baijia,
    title={BaiJia: A Large-Scale Role-Playing Agent Corpus of Chinese Historical Characters},
    author={Ting Bai and Jiazheng Kang and Jiayang Fan},
    year={2024},
    eprint={2412.20024},
    archivePrefix={arXiv},
    primaryClass={cs.AI}
}
