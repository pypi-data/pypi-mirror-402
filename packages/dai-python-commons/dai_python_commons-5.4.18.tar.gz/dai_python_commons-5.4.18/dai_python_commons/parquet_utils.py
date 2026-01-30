"""Functionality to modify parquet files in an S3 bucket"""

from __future__ import annotations

import gc
import io
import os
from dataclasses import dataclass
from typing import Optional

import boto3
import loguru
import pandas as pd

from dai_python_commons.s3_utils import S3Utils


@dataclass
class ParquetFileLocation:
    """
    Class that contains information about parquet files location in S3.

    args:
        source_bucket (str): The bucket where the parquet files to be merged are located.
        source_prefix (str): The prefix (ie 'folder') where the parquet files are located.
        destination_bucket (str): The bucket where the larger parquet file should be located. It can be the same as the
        source bucket.

        destination_prefix (str): The prefix (ie 'folder') where the merged file should be written
        compression (str): Type of compression. Accepted values are 'NONE', 'SNAPPY', 'GZIP', 'BROTLI', 'LZ4', 'ZSTD'
        remove_files_at_destination (bool): whether the files at the destination folder should be removed before
        writing the merged parquet file

        keep_source_files (bool): whether the source files should be kept after merge
        maximum_file_size (int): only parse sets of files which totals (in Bytes) under this limit
    """

    # pylint: disable=R0902
    source_bucket: str
    source_prefix: str
    destination_bucket: str = ""
    destination_prefix: str = ""
    consolidated_filename_prefix: str = ""
    compression: Optional[str] = "SNAPPY"
    remove_files_at_destination: bool = False
    keep_source_files: bool = True
    total_files_size: int = 1024 * 1024 * 1024  # 1GB


class ParquetUtils:
    """
    Class that provides functionality for manipulating parquet files
    """

    # pylint: disable=no-member,too-many-locals
    VALID_COMPRESSION_TYPES = {"none", "snappy", "gzip", "lz4", "zstd"}

    @staticmethod
    def s3_merge_files_in_place(
        boto3_session: boto3.Session,
        parquet_file_location: ParquetFileLocation,
        logger: loguru.Logger,
        compression: str = "snappy",
        keep_source_files: bool = False,
    ) -> int:
        """
         Merge many small parquet files into one larger parquet file. In place.

         Manually uses a bytesIO buffer of raw bytes as working area for parquet
         files. This ensures we never store more data in memory than necessary.
         The same buffer is used to both read input parquet and write the final
         file. The only additional data variable of considarable size is the
         current DataFrame of merged data being constructed.

        :param boto3_session: Boto3 session
        :param parquet_file_location: s3 bucket and prefix location where parquet files will be merged
        :param logger: The logger
        :param compression: Type of compression. Accepted values are 'none', 'snappy', 'gzip', 'brotli', 'lz4', 'zstd'
        :param keep_source_files: True to keep the source files, False to delete them.
        :return:
        """
        data_path = f"s3://{parquet_file_location.source_bucket}/{parquet_file_location.source_prefix}"
        logger.info(
            f"Merging files from {data_path} to {data_path}, compression: {compression}"
        )

        boto_s3_client = boto3_session.client("s3")
        num_rows = 0

        file_paths_iter = S3Utils.iter_file_paths_in_prefix(
            boto_s3_client=boto_s3_client,
            bucket_name=parquet_file_location.source_bucket,
            prefix=parquet_file_location.source_prefix,
            logger=logger,
            max_size=parquet_file_location.total_files_size,
        )
        for file_paths in file_paths_iter:
            if len(file_paths) < 2:
                logger.info(
                    f"file paths is less than 2 files, no reason to merge: {file_paths}"
                )
                continue
            logger.info(f"Reading and merging {file_paths}")

            # We want to make sure we use minimum amount of memory so we use
            # a manually manage Byte buffer. Since this is intended to run in
            # a lambda which uses RAM for disks files wont help.
            parquet_bytes = io.BytesIO()

            # Allocate the consolidated frame for use in the loop and afterwards.
            consolidated_frame = pd.DataFrame()

            # Loop over all keys in file_paths, leaving the BytesIO buffer empty
            # after looping
            for key_dict in file_paths:
                # Where in s3 is this file path?
                key = key_dict["Key"]

                # Get the parquet file from s3 into our BytesIO buffer
                boto_s3_client.download_fileobj(
                    Bucket=parquet_file_location.source_bucket,
                    Key=key,
                    Fileobj=parquet_bytes,
                )

                # after writing to the buffer the buffer pointer needs to be
                # reset before reading the result to a dataframe.
                parquet_bytes.seek(0)

                # Sort the columns of the frame.
                new_unsorted_frame = pd.read_parquet(parquet_bytes)
                new_frame = new_unsorted_frame[sorted(new_unsorted_frame.columns)]

                # Join the frames, inplace extends the memory of the frame instead of allocating a new one.
                # Drawback is slower access to columns on read but this frame is only read once (for write)
                # and written many times in a memory constrained environment.
                consolidated_frame = pd.concat(
                    [consolidated_frame, new_frame], ignore_index=True
                )

                # Before reading another frame into the memory bytes buffer
                # We move to the start of it and reset the rest (so that it is empty)
                parquet_bytes.seek(0)
                parquet_bytes.truncate(0)

            current_frame_rows = consolidated_frame.size
            num_rows += current_frame_rows

            # Key in s3 to write the finial consolidated_frame to
            key = os.path.join(
                parquet_file_location.source_prefix,
                f"{parquet_file_location.consolidated_filename_prefix}consolidated_rows_{num_rows}.parquet",
            )

            logger.debug(f"Shape of the table {consolidated_frame.shape}")
            logger.info(f"Writing to the destination path {data_path} with key {key}")

            try:
                # Write the final frame to the buffer.
                # The buffer pointer must at this point be at buffer start.
                consolidated_frame.to_parquet(parquet_bytes, compression=compression.lower())  # type: ignore

                # Reset buffer pointer after writing to it
                parquet_bytes.seek(0)

                # clear mem of the frame as it is now in the bytes-buffer.
                del consolidated_frame
                gc.collect()

                # Upload the filebuffer to the key in s3
                boto_s3_client.upload_fileobj(
                    Fileobj=parquet_bytes,
                    Bucket=parquet_file_location.source_bucket,
                    Key=key,
                )
                logger.info(
                    f"Done merging, {current_frame_rows} rows were written at prefix {data_path}"
                )

                # Clean up original files from the path
                if not keep_source_files:
                    logger.info("Removing source files")
                    logger.debug(f"Removing these files {file_paths}")
                    S3Utils.delete_objects(
                        boto_s3_client=boto_s3_client,
                        bucket_name=parquet_file_location.source_bucket,
                        to_delete=file_paths,
                        logger=logger,
                    )
            except Exception:
                logger.exception(
                    f"Caught error when trying to write out merged parquet files: {file_paths} to key {key}"
                )
                raise

            # manually trigger garbage collection before trying this on the
            # next set of files in path
            gc.collect()

        if num_rows == 0:
            logger.warning(f"No files found at {data_path}, nothing to merge")

        return num_rows

    @staticmethod
    def s3_merge_files(
        boto3_session: boto3.Session,
        parquet_file_location: ParquetFileLocation,
        logger: loguru.Logger,
    ) -> int:
        """
        Merge many small parquet files into one larger parquet file. From source to destination.
        Exception will be raised if source is equals to destination.
        Does NOT respect 'total_files_size' in {parquet_file_location}!
        Will consume all available memory if given a large enough amount of
        files to to merge.

        :param boto3_session: Boto3 session
        :param parquet_file_location: ParquetFileLocation contains info about the files location in the s3 bucket
        :param logger: The logger
        :return: Number of rows in the parquet file
        """
        source_bucket = parquet_file_location.source_bucket
        source_prefix = parquet_file_location.source_prefix
        remove_files_at_destination = parquet_file_location.remove_files_at_destination

        ParquetUtils._source_and_destination_not_same(parquet_file_location)

        source_data_path = f"s3://{parquet_file_location.source_bucket}/{parquet_file_location.source_prefix}"
        destination_data_path = f"s3://{parquet_file_location.destination_bucket}/{parquet_file_location.destination_prefix}"

        logger.info(
            f"Merging files from {source_data_path} to {destination_data_path},"
            f" compression: {parquet_file_location.compression}, "
            f"remove_files_at_destination={parquet_file_location.remove_files_at_destination}"
        )

        # check if there are any files present
        s3_client = boto3_session.client("s3")
        file_paths = S3Utils.file_paths_in_prefix(
            boto_s3_client=s3_client,
            bucket_name=source_bucket,
            prefix=source_prefix,
            logger=logger,
        )
        if len(file_paths) == 0:
            logger.warning(f"No files found at {source_data_path}, nothing to merge")
            return 0

        if remove_files_at_destination:
            ParquetUtils._remove_files(
                parquet_file_location, destination_data_path, logger, s3_client
            )

        logger.debug(f"Reading data from {source_data_path}")

        file_paths = S3Utils.file_paths_in_prefix(
            boto_s3_client=s3_client,
            bucket_name=parquet_file_location.source_bucket,
            prefix=parquet_file_location.source_prefix,
            logger=logger,
        )

        files = []
        for file_path in file_paths:
            file = S3Utils.read_s3_file(
                s3_client=s3_client,
                bucket_name=parquet_file_location.source_bucket,
                key=file_path["Key"],
            ).read()
            files.append(io.BytesIO(file))

        pq_table = pd.read_parquet(files.pop(0))
        pq_table = pq_table[sorted(pq_table.columns)]
        for file in files:
            new_frame = pd.read_parquet(file)
            pq_table = pd.concat([pq_table, new_frame], ignore_index=True)

        num_rows = pq_table.size

        logger.debug(f"Shape of the table {pq_table.shape}")

        compression = parquet_file_location.compression
        if compression:
            compression = compression.lower()
        else:
            compression = "none"

        try:
            logger.debug(f"Writing to the destination {destination_data_path}")
            with io.BytesIO() as con:
                pq_table.to_parquet(con, compression=compression)  # type: ignore

                key = os.path.join(
                    parquet_file_location.destination_prefix,
                    f"consolidated_rows_{num_rows}.parquet",
                )
                s3_client.put_object(
                    Body=con.getvalue(),
                    Bucket=parquet_file_location.destination_bucket,
                    Key=key,
                )

            gc.collect()

            logger.info(
                f"Done merging, {pq_table.size} rows were written at {destination_data_path}"
            )
            if not parquet_file_location.keep_source_files:
                logger.info("Removing source files")
                logger.debug(f"Removing these files {file_paths}")
                S3Utils.delete_objects(
                    boto_s3_client=s3_client,
                    bucket_name=source_bucket,
                    to_delete=file_paths,
                    logger=logger,
                )
        except Exception:
            logger.exception(
                f"Caught error when trying to merge parquet files: {file_paths}"
            )
            raise

        return pq_table.size

    @staticmethod
    def _remove_files(parquet_file_location, destination_data_path, logger, s3_client):
        """removes files at the destination bucket, assigned in the parquet_file_location"""
        logger.debug(f"Removing all files at {destination_data_path}")
        S3Utils.delete_objects_by_prefix(
            boto_s3_client=s3_client,
            bucket_name=parquet_file_location.destination_bucket,
            prefix=parquet_file_location.destination_prefix,
            logger=logger,
        )

    @staticmethod
    def _source_and_destination_not_same(parquet_file_location):
        """checks that source bucket and destination bucket is not the same"""
        if (
            parquet_file_location.source_bucket
            == parquet_file_location.destination_bucket
            and parquet_file_location.source_prefix.rstrip("/")
            == parquet_file_location.destination_prefix.rstrip("/")
        ):
            raise ValueError("Source and destination cannot be the same!")
