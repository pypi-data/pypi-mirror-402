"""Useful functions for cdk"""

from __future__ import annotations

from dai_python_commons import dai_error


# pylint: disable=too-few-public-methods
class CDKUtils:
    """
    Class provides utility functions for cdk
    """

    @staticmethod
    def get_config_for_s3_prefix(
        configurations: dict, s3_prefix: str
    ) -> dict[str, dict]:
        """
        Get configuration for a given s3_prefix or s3_key

        :param s3_prefix: An S3 prefix or S3 key. For example foo/bar/a.txt or foo/bar/.
         Note that full object path such as s3://bucket/foo/bar/a.txt is not accepted,
         nor is /foo/bar/a.txt
        :raises DaiError: Missing configuration
        :return: The configuration that matches this prefix.
        """
        # get all prefixes in config that match this s3_prefix
        relevant = {}
        for dai_code, conf in configurations.items():
            if s3_prefix.startswith(conf["prefix"]) or (
                not s3_prefix.endswith("/") and f"{s3_prefix}/" == conf["prefix"]
            ):
                relevant[dai_code] = conf["prefix"]

        if len(relevant) == 0:
            raise dai_error.DaiError(f"Missing configuration for prefix {s3_prefix}")

        if len(relevant) == 1:
            dai_code_longest_pre = list(relevant)[0]
        else:
            dai_code_longest_pre = max(relevant, key=relevant.get)  # type: ignore

        return {
            "dai_code": dai_code_longest_pre,
            **configurations[dai_code_longest_pre],
        }
