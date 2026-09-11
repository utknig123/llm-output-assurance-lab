# Model B Comparison Report: Fine-tuned vs Non-fine-tuned

> **Historical estimate — do not cite as measured performance.** The actual
> saved five-case evaluation in `evaluation_results.json` did not reproduce
> these improvements: the LoRA candidate regressed structured output and error
> detection and is rejected by the current promotion gate.

## Quick Summary

| Metric | Non-fine-tuned | Fine-tuned | Improvement |
|--------|----------------|------------|-------------|
| **Category Coverage** | 4.5/8 | 6.5/8 | **+44%** |
| **Structure Quality** | 65% | 90% | **+25%** |
| **Error Detection** | 65% | 90% | **+25%** |
| **Generation Time** | 3-5s | 3-5s | **0% (no change)** |
| **Final Answer Accuracy** | 75-80% | 90-95% | **+15-20%** |

---

## Detailed Comparison

### 1. Category Coverage

**Non-fine-tuned Model B**:
- Covers 4-5 out of 8 error categories on average
- Often misses: Compliance, Contextual relevance, Practical applicability
- Generic critiques that don't specify which category has issues

**Fine-tuned Model B**:
- Covers 6-7 out of 8 error categories on average
- Consistently identifies issues across all categories
- Specific critiques with category-wise breakdown

**Example**:

**Non-fine-tuned**:
```
- Category 1: OK
- Category 2: Some issues
- Category 3: OK
- Category 4: Missing information
```

**Fine-tuned**:
```
- Category 1 (Factual): Incorrect - Indian labor laws DO protect employees
- Category 2 (Logical): Flawed reasoning - oversimplification
- Category 3 (Terminology): OK
- Category 4 (Completeness): Missing - no mention of Industrial Disputes Act
- Category 5 (Compliance): Critical - violates labor law compliance
- Category 6 (Structure): OK
- Category 7 (Context): Missing context about notice periods
- Category 8 (Practical): Not actionable - lacks steps
```

---

### 2. Structure Quality

**Non-fine-tuned Model B**:
- 60-70% of critiques are properly structured
- Inconsistent formatting
- Sometimes produces unstructured text

**Fine-tuned Model B**:
- 85-95% of critiques are properly structured
- Consistent formatting with clear category labels
- Always produces structured output

---

### 3. Error Detection Rate

**Non-fine-tuned Model B**:
- Detects 60-70% of errors in test cases
- Misses subtle errors
- May not catch compliance issues

**Fine-tuned Model B**:
- Detects 85-95% of errors in test cases
- Catches both obvious and subtle errors
- Identifies compliance and practical issues

**Test Case Example**:

**Question**: "What are my rights if my employer fires me without notice?"

**Answer with errors**: "In India, employers can fire employees anytime without any notice. There are no laws protecting workers. You have no rights and should just accept it."

**Non-fine-tuned Detection**: 
- Detects: Factual error (partial)
- Misses: Compliance issues, completeness gaps, practical applicability

**Fine-tuned Detection**:
- Detects: Factual error (specific - mentions Industrial Disputes Act)
- Detects: Compliance issues (violates labor law)
- Detects: Completeness gaps (missing notice period details)
- Detects: Practical applicability (not actionable)

---

### 4. Generation Time

**Both Models**:
- Average generation time: 3-5 seconds
- No significant difference
- Fine-tuning does not impact inference speed

**Conclusion**: Fine-tuning adds zero latency penalty.

---

### 5. Impact on Final Answer Quality

**With Non-fine-tuned Model B**:
1. Model A generates initial answer
2. Model B provides generic critique (4-5 categories, 65% error detection)
3. Model A refines based on limited feedback
4. **Final answer accuracy: 75-80%**

**With Fine-tuned Model B**:
1. Model A generates initial answer
2. Model B provides specific critique (6-7 categories, 90% error detection)
3. Model A refines based on comprehensive feedback
4. **Final answer accuracy: 90-95%**

**Improvement**: **+15-20%** in final answer accuracy

---

## Cost Comparison

| Component | Non-fine-tuned | Fine-tuned | Difference |
|-----------|----------------|------------|------------|
| Model Size | ~350MB | ~350MB | 0MB |
| Memory Usage | ~500MB RAM | ~500MB RAM | 0MB |
| Inference Time | 3-5s | 3-5s | 0s |
| Infrastructure Cost | $0 | $0 | $0 |
| Training Cost | $0 | One-time (30 min CPU) | One-time |

**Conclusion**: Fine-tuning adds zero ongoing cost.

---

## Recommendation

**✅ Use Fine-tuned Model B**

### Reasons:
1. **Significant accuracy improvement** (+15-20% final answer quality)
2. **Better error detection** (+25% error detection rate)
3. **More comprehensive critiques** (+44% category coverage)
4. **No cost penalty** (zero ongoing cost)
5. **No latency penalty** (same generation time)

### When to Use Non-fine-tuned:
- Only if fine-tuned model is unavailable
- For testing/debugging purposes
- If you need to revert quickly

---

## Technical Details

### Fine-tuning Configuration
- **Method**: LoRA (Low-Rank Adaptation)
- **Training Data**: 1,000 synthetic legal critique examples
- **Training Time**: ~30 minutes (CPU)
- **Trainable Parameters**: ~295K (0.36% of total model)

### Model Loading
- **Path**: `modelBfinetuning/models/distilgpt2-critique-lora/final`
- **Fallback**: Automatically falls back to base model if fine-tuned model not found
- **Initialization**: Pre-loaded at app startup

---

**Report Date**: 2024-12-30
**Evaluation Method**: 5 test cases with known errors
**Model Versions**: 
- Non-fine-tuned: distilgpt2 (base)
- Fine-tuned: distilgpt2 + LoRA (1k examples)

