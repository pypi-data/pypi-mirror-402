# Lightning-ir Embeddigns

This directory contains the lightning-ir baseline to produce embeddings for the lsr-benchmark.

## Development

This directory is [configured as DevContainer](https://code.visualstudio.com/docs/devcontainers/containers), i.e., you can open this directory with VS Code or some other DevContainer compatible IDE to work directly in the Docker container with all dependencies installed.

If you want to run it locally, please install the dependencies via `pip3 install -r requirements.txt`.

To make predictions on a dataset, run:

Run it via:

```
# allow that models can be downloaded (only in the dev-container)
export HF_HUB_OFFLINE=0
./lightning-ir.py \
    --dataset tiny-example-20251002_0-training \
    --model webis/bert-bi-encoder \
    --output foo
```

## Submission

Code submission to tira via (remove the --dry-run for upload):

```
tira-cli code-submission \
    --path . \
    --task lsr-benchmark \
    --tira-vm-id lightning-ir \
    --dataset tiny-example-20251002_0-training \
    --command '/lightning-ir.py --dataset $inputDataset --output $outputDir --model naver/splade-v3' \
    --mount-hf-model naver/splade-v3 \
    --dry-run
```

