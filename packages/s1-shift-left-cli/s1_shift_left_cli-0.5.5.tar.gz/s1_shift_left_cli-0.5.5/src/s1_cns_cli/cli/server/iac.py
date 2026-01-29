import os
import logging
import tempfile
import uuid
import shutil
import json
from s1_cns_cli.cli.utils import decode_base_64, write_to_file, get_home_path
from s1_cns_cli.cli.registry import IacFramework, InvalidGraphConnection, MissingRequiredFlagsException, InvalidInputException
from s1_cns_cli.cli.scan import iac as iac_helper
from s1_cns_cli.s1graph.cloudformation.runner import Runner as CloudformationRunner
from s1_cns_cli.s1graph.helm.runner import Runner as HelmRunner
from s1_cns_cli.s1graph.kubernetes.runner import Runner as KubernetesRunner
from s1_cns_cli.s1graph.terraform.plan_runner import Runner as TerraFormPlanRunner
from s1_cns_cli.s1graph.terraform.runner import Runner as TerraFormRunner
from s1_cns_cli.s1graph.runner_filter import RunnerFilter

LOGGER = logging.getLogger("cli")


def get_runner(framework: str):
    if framework == IacFramework.HELM.value:
        return HelmRunner()
    elif framework == IacFramework.TERRAFORM.value:
        return TerraFormRunner()
    elif framework == IacFramework.TERRAFORM_PLAN.value:
        return TerraFormPlanRunner()
    elif framework == IacFramework.KUBERNETES.value:
        return KubernetesRunner()
    elif framework == IacFramework.CLOUDFORMATION.value:
        return CloudformationRunner()
    else:
        return None


def get_filter(framework: str):
    if framework == IacFramework.HELM.value:
        return RunnerFilter(framework=["helm"], download_external_modules=True)
    elif framework == IacFramework.TERRAFORM.value:
        return RunnerFilter(framework=["terraform"], download_external_modules=True)
    elif framework == IacFramework.TERRAFORM_PLAN.value:
        return RunnerFilter(framework=["terraform_plan"], download_external_modules=True)
    elif framework == IacFramework.KUBERNETES.value:
        return RunnerFilter(framework=["kubernetes"], download_external_modules=True)
    elif framework == IacFramework.CLOUDFORMATION.value:
        return RunnerFilter(framework=["cloudformation"], download_external_modules=True)
    else:
        return None


def create_graph(framework, file_extension, file_content, cleanup=True):
    base_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    file_path = os.path.join(base_dir, str(uuid.uuid4()))
    try:

        file_path += file_extension
        runner = get_runner(framework)
        runner_filter = get_filter(framework)
        if runner is None or runner_filter is None:
            raise Exception(f"Framework: {framework} not supported")

        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        write_to_file(file_path, file_content)
        graph = runner.generate_graph(base_dir, runner_filter)
        return graph, base_dir
    except Exception as e:
        raise e
    finally:
        if cleanup and os.path.exists(base_dir):
            shutil.rmtree(base_dir, ignore_errors=True)


def validate_args(args):
    log_error = "Missing required parameters. Require: --filename, --file-content, --output-file, --frameworks"
    if args.generate_graph:
        if args.file_name == "" or args.file_content == "" or args.output_file == "" or len(args.frameworks) == 0:
            raise MissingRequiredFlagsException(log_error)
        if len(args.frameworks) > 1:
            raise InvalidInputException("Only ony one framework is allowed with --generate-graph.")
    if args.evaluate_rego:
        if args.file_name == "" or args.file_content == "" or args.output_file == "" or len(args.frameworks) == 0 or args.rego_script == ""\
                or args.primary_resource_type == "":
            raise MissingRequiredFlagsException(f"{log_error}, --rego-script, --primary-resource-type")
        if len(args.frameworks) > 1:
            raise InvalidInputException("Only ony one framework is allowed with --evaluate-rego.")


def generate_graph(args):
    LOGGER.info("Graph generation initiated.")

    validate_args(args)

    framework = args.frameworks[0]
    split_file_name = os.path.splitext(args.file_name)
    if len(split_file_name) != 2:
        raise InvalidInputException("Wrong filename, please provide filename with extension. Example - sample.tf")

    file_extension = split_file_name[1]
    file_content = decode_base_64(args.file_content)
    output_path = args.output_file

    graph, _ = create_graph(framework, file_extension, file_content)

    write_to_file(output_path, json.dumps(graph))
    LOGGER.info(f"Graph generated and written at {output_path}")
    return 0


def evaluate_rego(args):
    base_dir = None
    try:
        LOGGER.info("Rego evaluation initiated.")

        validate_args(args)

        split_file_name = os.path.splitext(args.file_name)
        if len(split_file_name) != 2:
            raise InvalidInputException("Wrong filename, please provide filename with extension. Example - sample.tf")

        file_extension = split_file_name[1]
        file_content = decode_base_64(args.file_content)
        framework = args.frameworks[0]
        rego_script = decode_base_64(args.rego_script)

        if args.connections == "":
            args.connections = "{}"
        connections = json.loads(args.connections)
        primary_resource_type = args.primary_resource_type

        if "isVulnerable" not in rego_script:
            LOGGER.error("Invalid rego script")
            return 1

        graph, base_dir = create_graph(framework, file_extension, file_content, cleanup=False)
        grouped_nodes_by_resource_type = iac_helper.group_nodes_by_resource_type(graph["nodes"])
        graph_nodes_by_id = iac_helper.get_graph_nodes_by_id(graph["nodes"])
        grouped_links_by_source = iac_helper.group_links(graph["links"], "source")
        grouped_links_by_target = iac_helper.group_links(graph["links"], "target")

        results = iac_helper.evaluate_plugin_on_graph("", generate_plugin_data(connections, rego_script),
                                                      grouped_nodes_by_resource_type[primary_resource_type],
                                                      grouped_links_by_source, grouped_links_by_target,
                                                      framework, graph_nodes_by_id,
                                                      os.path.join(get_home_path(".s1cns")), False)

        write_to_file(args.output_file, json.dumps(generate_evaluation_result(results)))
        LOGGER.info(f"Result generated and and written at {args.output_file}")
        return 0
    except InvalidGraphConnection as e:
        LOGGER.error(e)
        return 1
    except Exception as e:
        LOGGER.error(e)
        return 1
    finally:
        # Clean up the temporary directory after results are generated
        if base_dir is not None and os.path.exists(base_dir):
            shutil.rmtree(base_dir, ignore_errors=True)


def generate_evaluation_result(results):
    return {
        "output": {
            "code": "VULNERABLE" if len(results) > 0 else "NOT_VULNERABLE",
            "data": {
                "context": {},
                "isVulnerable": len(results) > 0
            }
        }
    }


def generate_plugin_data(connections, rego_script):
    return {
        "id": "id",
        "severity": "severity",
        "description": "description",
        "title": "title",
        "impact": "impact",
        "info_link": "info_link",
        "recommended_action": "recommended_action",
        "connections": connections,
        "rego": rego_script
    }