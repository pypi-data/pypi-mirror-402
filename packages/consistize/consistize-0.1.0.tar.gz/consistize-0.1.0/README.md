# consistize

Check whether an image is consistent with a set of reference images using OpenAI
vision models.

## Install

```bash
pip install -e .
```

## Usage

```python
from consistize import Consistize

checker = Consistize(
    reference_images=["./refs/ref1.jpg", "./refs/ref2.jpg"],
)

result = checker.run("./inputs/target.jpg")
print(result.consistency_score)
print(result.inconsistent_parts)
print(result.background_fix_prompts)
```

Set `OPENAI_API_KEY` in your environment or pass `api_key` to `Consistize`.

### Custom prompt or model

```python
result = checker.run(
    "./inputs/target.jpg",
    prompt="Check the first image against the references; focus on lighting.",
    model="gpt-5.2-pro"
)
```
