import os
import logging

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_db_anonymiser.database_sanitizer.config import Configuration
from django_db_anonymiser.database_sanitizer.dump import run

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-local-dumpfile",
            action="store_true",
            help="Keep local dump file, rather than cleaning it up.",
        )
        parser.add_argument(
            "--skip-s3-upload",
            action="store_true",
            help="Skip uploading to S3.",
        )
        parser.add_argument(
            "--presign",
            action="store_true",
            help="Generates and logs a presigned URL for the uploaded file.",
        )

    def configure(self):
        self.keep_local_dumpfile = False
        self.skip_s3_upload = False
        self.presign = False
        self.dump_file_name = settings.DB_ANONYMISER_DUMP_FILE_NAME
        self.temporary_dump_location = getattr(
            settings,
            "DB_ANONYMISER_TEMPORARY_DUMP_LOCATION",
            f"/tmp/{self.dump_file_name}",
        )
        try:
            self.config_location = settings.DB_ANONYMISER_CONFIG_LOCATION
        except AttributeError:
            raise CommandError(
                "DB_ANONYMISER_CONFIG_LOCATION must be set in django settings."
            )
        additional_s3_params = {}
        aws_endpoint_url = getattr(settings, "DB_ANONYMISER_AWS_ENDPOINT_URL", None)
        if aws_endpoint_url:
            additional_s3_params[
                "endpoint_url"
            ] = settings.DB_ANONYMISER_AWS_ENDPOINT_URL
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.DB_ANONYMISER_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.DB_ANONYMISER_AWS_SECRET_ACCESS_KEY,
            region_name=settings.DB_ANONYMISER_AWS_REGION,
            **additional_s3_params,
        )
        self.s3_bucket_name = settings.DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME

    def handle(self, *args, **options):
        logger.info("Starting DB dump and anonymiser")
        self.configure()

        if options["keep_local_dumpfile"]:
            self.keep_local_dumpfile = True

        if options["skip_s3_upload"]:
            self.skip_s3_upload = True
        
        if options["presign"]:
            self.presign = True

        try:
            self.dump_anonymised_db()
            self.write_to_s3()
            logger.info("DB dump and anonymiser was successful!")
            if self.presign:
                self.generate_presigned_url()
        finally:
            self.cleanup()

    def dump_anonymised_db(self):
        db_details = settings.DATABASES["default"]
        postgres_url = f"postgresql://{db_details['USER']}:{db_details['PASSWORD']}@{db_details['HOST']}:{db_details['PORT']}/{db_details['NAME']}"
        logger.info(
            "Writing anonymised dumpfile to temporary location %s", self.dump_file_name
        )
        with open(self.temporary_dump_location, "w") as outfile:
            run(
                url=postgres_url,
                config=Configuration.from_file(self.config_location),
                output=outfile,
            )
        logger.info("Writing anonymised dumpfile complete")

    def write_to_s3(self):
        if self.skip_s3_upload:
            return
        logger.info("Writing file %s to S3", self.dump_file_name)
        self.s3_client.upload_file(
            self.temporary_dump_location, self.s3_bucket_name, self.dump_file_name
        )
        logger.info("Writing file to S3 complete")
    
    def generate_presigned_url(self):
        presigned = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.s3_bucket_name, 'Key': self.dump_file_name},
            ExpiresIn=600
        )
        logger.info("Presigned URL: %s", presigned)

    def cleanup(self):
        if self.keep_local_dumpfile:
            return
        logger.info("Cleaning up temporary files")
        try:
            os.remove(self.temporary_dump_location)
        except FileNotFoundError:
            pass
        logger.info("Clean up complete")
