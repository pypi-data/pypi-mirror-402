"""Useful functions for s3 buckets"""

from __future__ import annotations

import datetime
import re
from typing import Iterable, List

import loguru
from botocore.response import StreamingBody
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import DeleteTypeDef, ObjectIdentifierTypeDef

from dai_python_commons import dai_error

# pylint: disable=no-member


class S3Utils:
    """
    Class provides functions to modify s3 buckets
    """

    RAW_BUCKET_PATTERN = re.compile(r"se-sl-tf-dai-[^-]*-data-raw")

    @staticmethod
    def delete_objects_by_prefix(
        boto_s3_client: S3Client,
        bucket_name: str,
        prefix: str,
        logger: loguru.Logger,
    ) -> int:
        """
        Deletes all objects with given prefix from a bucket

        :param boto_s3_client: S3 client to be used
        :param bucket_name: Name of the bucket
        :param prefix: Prefix of objects that should be removed
        :param logger: The logger
        :return: Number of objects deleted
        """
        logger.info(f"Deleting objects with prefix {prefix} from bucket {bucket_name}")

        paginator = boto_s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        # gather all objects to be deleted
        to_delete = []
        for item in page_iterator.search("Contents"):
            if not item:
                break
            to_delete.append({"Key": item["Key"]})

        # delete the objects
        return S3Utils.delete_objects(
            boto_s3_client=boto_s3_client,
            bucket_name=bucket_name,
            to_delete=to_delete,
            logger=logger,
        )

    @staticmethod
    def delete_objects(
        boto_s3_client: S3Client,
        bucket_name: str,
        to_delete: List[ObjectIdentifierTypeDef],
        logger: loguru.Logger,
    ) -> int:
        """
        Deletes the specified objects in `to_delete` and returns the number of deleted objects.

        `to_delete` should be in the following format:

            [
                {
                    'Key': 'prefix'
                }
            ]

        :param boto_s3_client: S3 client to be used
        :param bucket_name: Name of the bucket
        :param to_delete: list of objects to delete
        :param logger: The logger
        :return: Number of objects deleted
        """

        start_index = 0
        while start_index < len(to_delete):
            end_index = min(len(to_delete), start_index + 1000)
            batch_to_delete = DeleteTypeDef(Objects=to_delete[start_index:end_index])
            logger.debug(f"Deleting {batch_to_delete}")
            response = boto_s3_client.delete_objects(
                Bucket=bucket_name, Delete=batch_to_delete
            )

            # If something went wrong raise an error
            if "Errors" in response and len(response["Errors"]) > 0:
                raise dai_error.DaiS3DeleteObjectError(
                    s3_bucket=bucket_name, error_infos=response["Errors"]
                )

            start_index = end_index

        logger.info(f"Number of objects deleted: {len(to_delete)}")

        return len(to_delete)

    @staticmethod
    def iter_file_paths_in_prefix(
        boto_s3_client: S3Client,
        bucket_name: str,
        prefix: str,
        logger: loguru.Logger,
        max_size: int,
    ) -> Iterable[List[ObjectIdentifierTypeDef]]:
        """
        Returns a Iterable over lists of dicts representing file paths in the format:

            [
                {
                    'Key': 'prefix'
                }
            ]

        NOTE: Files larger than max_size are never returned!

        :param boto_s3_client: S3 client to be used
        :param bucket_name: Name of the bucket
        :param prefix: Prefix where to list files
        :param logger: The logger
        :param max_size: The size in bytes that limits how many files are returned in one iteration
        :yields: lists of file path dicts
        """

        paginator = boto_s3_client.get_paginator("list_objects_v2")
        prefix = prefix if prefix.endswith("/") else f"{prefix}/"
        available_file_paths = []
        for item in paginator.paginate(
            Bucket=bucket_name, Prefix=prefix, Delimiter="/"
        ).search("Contents"):
            # Ignore directories, i.e. suffix '/'
            if item and not item["Key"].endswith("/"):
                available_file_paths.append({"Key": item["Key"], "Size": item["Size"]})

        prefixes = []
        size = 0
        for item in available_file_paths:
            if item["Size"] + size > max_size and len(prefixes) > 0:
                logger.debug(
                    f'In "{bucket_name}/{prefix}" yields partial results: {prefixes} at size {size}'
                )
                yield prefixes
                size = 0
                prefixes.clear()

            if item["Size"] < max_size:
                prefixes.append({"Key": item["Key"]})
                size += item["Size"]

        logger.debug(f'In "{bucket_name}/{prefix}" yields last results: {prefixes}')

        yield prefixes

    @staticmethod
    def file_paths_in_prefix(
        boto_s3_client: S3Client,
        bucket_name: str,
        prefix: str,
        logger: loguru.Logger,
    ) -> List[ObjectIdentifierTypeDef]:
        """
        Returns a list of dicts representing file paths in the format:

            [
                {
                    'Key': 'prefix'
                }
            ]

        :param boto_s3_client: S3 client to be used
        :param bucket_name: Name of the bucket
        :param prefix: Prefix where to list files
        :param logger: The logger
        :return: A list of file path dicts
        """
        paginator = boto_s3_client.get_paginator("list_objects_v2")
        prefix = prefix if prefix.endswith("/") else f"{prefix}/"
        file_paths = []
        for item in paginator.paginate(
            Bucket=bucket_name, Prefix=prefix, Delimiter="/"
        ).search("Contents"):
            # Ignore directories, i.e. suffix '/'
            if item and not item["Key"].endswith("/"):
                file_paths.append({"Key": item["Key"]})

        logger.debug(f'In "{bucket_name}/{prefix}" found: {file_paths}')

        return file_paths

    @staticmethod
    def is_raw_bucket(bucket_name: str) -> bool:
        """Checks that bucket_name matches RAW_BUCKET_PATTERN regex"""
        return S3Utils.RAW_BUCKET_PATTERN.match(bucket_name) is not None

    @staticmethod
    def get_last_modified(
        boto_s3_client: S3Client,
        bucket_name: str,
        key: str,
        logger: loguru.Logger,
    ) -> datetime.datetime:
        """
        Gets the last modified stamp for a object stored in s3

        :param boto_s3_client: Boto3 s3 client
        :param bucket_name: Name of s3 bucket
        :param key: Object key
        :param logger: Logger object
        :return: Last modified value
        :raise DaiS3Error: If unable to get head of object.
        """
        response = boto_s3_client.head_object(Bucket=bucket_name, Key=key)
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            error_info = response.get("Error", {})
            logger.error(
                f"Unable to obtain LastModified for s3://{bucket_name}/{key}. Error info: {error_info}"
            )
            raise dai_error.DaiS3Error(
                error_info.get(
                    "Message",
                    "Unable to get head of object and in turn the last modified timestamp of the file.",
                )
            )

        return response["LastModified"]

    @staticmethod
    def read_s3_file(s3_client: S3Client, bucket_name: str, key: str) -> StreamingBody:
        """
        Get content of an S3 object

        :param s3_client: Boto3 s3 client
        :param bucket_name: Name of s3 bucket
        :param key: Object key
        :return: Http response body
        """
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response["Body"]

        return content
