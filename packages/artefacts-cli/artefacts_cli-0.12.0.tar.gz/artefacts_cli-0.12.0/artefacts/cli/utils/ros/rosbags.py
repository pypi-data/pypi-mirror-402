import os
from glob import glob


def check_and_prepare_rosbags_for_upload(run, preexisting_rosbags):
    # Checks for a new rosbag after test completions. We look for the directory
    # as drilling down will find both the directory as well as the rosbag itself.
    rosbags = [
        path for path in glob("**/rosbag2*", recursive=True) if os.path.isdir(path)
    ]
    new_rosbags = set(rosbags).difference(set(preexisting_rosbags))
    from artefacts.cli.utils.ros.bagparser import BagFileParser

    if len(new_rosbags) > 0:
        run.logger.info(f"Found new rosbags: {new_rosbags}")
        rosbag_dir = new_rosbags.pop()
        run.log_artifacts(rosbag_dir, "rosbag")
        if "metrics" in run.params and isinstance(run.params["metrics"], list):
            # Search for database files in the directory
            # TODO: should go inside BagFileParser?
            db_files = glob(f"{rosbag_dir}/*.mcap")  # Ros2 Default
            if not db_files:
                db_files = glob(f"{rosbag_dir}/*.db3")  # Legacy
            if not db_files:
                raise FileNotFoundError(
                    "No .mcap or .db3 files found in the specified path. Attempted to find in "
                    f"{rosbag_dir}/*.mcap and {rosbag_dir}/*.db3"
                )
            db_file = db_files[0]

            bag = BagFileParser(db_file)
            for metric in run.params["metrics"]:
                try:
                    last_value = bag.get_last_message(metric)[1].data
                    run.log_metric(metric, last_value)
                except KeyError:
                    run.logger.error(f"Metric {metric} not found in rosbag, skipping.")
                except (TypeError, IndexError):
                    run.logger.error(
                        f"Metric {metric} not found. Is it being published?. Skipping."
                    )
