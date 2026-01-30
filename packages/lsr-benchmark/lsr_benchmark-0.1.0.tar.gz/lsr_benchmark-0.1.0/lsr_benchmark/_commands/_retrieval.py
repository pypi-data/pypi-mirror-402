import click
import sys
from tira.io_utils import log_message, verify_tira_installation, FormatMsgType
from tira.third_party_integrations import temporary_directory
from tira.check_format import check_format
from tira.rest_api_client import Client
from pathlib import Path
from lsr_benchmark.datasets import all_embeddings, all_datasets
import shutil
import yaml
from subprocess import Popen
from platform import system


def run_foo(docker_image, command, dataset_id, embedding, output_dir=None):
    if output_dir is not None and Path(output_dir).exists():
        return
    tira = Client()
    dataset_path = tira.download_dataset("lsr-benchmark", dataset_id)
    if embedding.lower() != "none":
        embeddings_dir = tira.get_run_output(f'lsr-benchmark/lightning-ir/{embedding}', dataset_id)
    else:
        embeddings_dir = None
    tmp_dir = temporary_directory()
    tira.local_execution.run(
        image=docker_image,
        command=command,
        input_dir=dataset_path,
        output_dir=tmp_dir,
        allow_network=False,
        input_run=embeddings_dir
    )

    result, msg = check_format(Path(tmp_dir), ["run.txt"], {})
    if result != FormatMsgType.OK:
        print(msg)
        raise ValueError(msg)

    tag = yaml.safe_load((Path(tmp_dir) / "retrieval-metadata.yml").read_text())["tag"]
    
    if output_dir is not None:
        from tira.io_utils import patch_ir_metadata
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp_dir, output_dir)
        patch_ir_metadata(output_dir, {"data": {"test collection": {"name": "/tira-data/input"}}}, {"data": {"test collection": {"name": dataset_id}}})
    
    return tag


@click.argument(
    "approaches",
    type=str,
    nargs=-1,
)
@click.option(
    "-o", "--out",
    type=str,
    required=True,
    multiple=False,
    help="The output directory to write to.",
)
@click.option(
    "--dataset",
    type=click.Choice(["all"] + all_datasets()),
    multiple=True,
    help="The datasets to run on.",
)
@click.option(
    "--embedding",
    type=click.Choice(["all", "none", ] + all_embeddings()),
    multiple=True,
    help="The datasets to run on.",
)
def retrieval(approaches: list[str], dataset: list[str], embedding: list[str], out: str) -> int:
    all_messages = []

    def print_message(message, level):
        all_messages.append((message, level))
        Popen("cls" if system() == "Windows" else "clear", shell=True)  # noqa: S602
        print(' '.join([sys.argv[0].split('/')[-1]] + sys.argv[1:]))
        for message, level in all_messages:
            log_message(message, level)

    if dataset is None or not dataset or "all" in dataset:
        dataset = all_datasets()

    if embedding is None or not embedding or "all" in embedding:
        embedding = all_embeddings()
    if embedding and "none" in embedding:
        embedding = ["none"]

    status = verify_tira_installation()

    if status != FormatMsgType.OK:
        print_message("Your TIRA installation is not valid. Please run 'tira-cli verify-installation' to resolve the problem", status)
        return 1

    print_message("Your TIRA installation is valid.", FormatMsgType.OK)
    
    tira = Client()
    approach_to_execution = {}
    for approach in approaches:
        docker_tag, zipped_code, remotes, commit, active_branch = tira.build_docker_image_from_code(
            Path(approach), log_message, False
        )
        if docker_tag in approach_to_execution.values():
            raise ValueError(f"Approach {approach} produces a docker tag that is already used by another approach.")
        cmd = (Path(approach) / "README.md").read_text().split("tira-cli code-submission")[1].split('--command')[1].split("'")[1]

        log_message(f"Approach {approach} is compiled.", FormatMsgType.OK)
        system_tag = run_foo(docker_tag, cmd, 'tiny-example-20251002_0-training', embedding[0])
        print_message(f"Approach {approach} compiled and produced valid outputs on example dataset (tag={system_tag}).", FormatMsgType.OK)
        approach_to_execution[approach] = {"tag": docker_tag, "command": cmd}

    stats = {}
    for d in dataset:
        for e in embedding:
            for approach in approaches:
                out_dir = Path(out) / d / e / approach
                try:
                    run_foo(approach_to_execution[approach]["tag"], approach_to_execution[approach]["command"], d, e, out_dir)
                except Exception:  # noqa: S112
                    continue
    for approach in stats:
        print_message(f"Approach {approach} produced valid outputs on {len(stats[approach]['datasets'])} datasets for {len(stats[approach]['embeddings'])} embeddings.", FormatMsgType.OK)
    
    return 0
