from os import path

from absl import flags

from autofl.benchmark import bench_fl

module_dir = path.dirname(__file__)  # directory in which this module resides
root_dir = path.abspath(path.join(module_dir, "../.."))  # project root dir
output_dir_default = path.abspath(path.join(root_dir, "output"))
results_dir_default = path.abspath(path.join(root_dir, "results"))

# following: https://abseil.io/docs/cpp/guides/flags#flags-best-practices
# we will define our flags in this file
FLAGS = flags.FLAGS

flags.DEFINE_string(
    "output_dir", output_dir_default, "Output directory as absolute path"
)

flags.DEFINE_string(
    "results_dir", results_dir_default, "Results directory as absolute path"
)

flags.DEFINE_enum("benchmark_type", "fl", ["fl", "ea"], "Type of benchmark to run")

flags.DEFINE_string(
    "benchmark_name", None, "Name of the benchmark to be run e.g. 'integration_test'"
)

flags.DEFINE_string("group_name", None, "Group name to be plotted")
