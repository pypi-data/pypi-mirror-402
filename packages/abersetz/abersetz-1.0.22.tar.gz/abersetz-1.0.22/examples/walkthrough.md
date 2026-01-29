---
this_file: examples/walkthrough.md
---
# Sample Translation Walkthrough

```bash
abersetz tr planslate examples/poem_en.txt \
  --engine hysf \
  --output examples/out \
  --save-voc \
  --verbose
```

This command translates the poem and writes the result to `examples/out/poem_en.txt`. The vocabulary file is saved as `examples/out/poem_en.txt.voc