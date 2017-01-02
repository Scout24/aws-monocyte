from __future__ import absolute_import, print_function, division
"""Check for ACM certificates that will expire soon

ACM is the "AWS Certificate Manager" that usually renews your certificates
automatically, so you don't have to. However, there's a few details in the
fine print at

    https://docs.aws.amazon.com/acm/latest/userguide/acm-renewal.html

which means it is not 100% guaranteed to work. And once we are at it, we
can also check imported certificates (which cannot be renewed by ACM).
"""

import datetime
import boto3
from monocyte.handler import Resource, Handler

# ACM attempts to renew SSL certificates 60 before expiration. If it
# is still not renewed 55 days before expiration, something is wrong.
MIN_VALID_DAYS = 55

class Certificate(Handler):
    def fetch_regions(self):
        from boto import ec2
        return ec2.regions()
        return ['global']

    def fetch_unwanted_resources(self):
        client = boto3.client('acm')
        response = client.list_certificates(CertificateStatuses=['ISSUED'])
        certificate_arns = [summary['CertificateArn'] for summary in response['CertificateSummaryList']]

        limit = datetime.datetime.now() + datetime.timedelta(days=MIN_VALID_DAYS)

        expired_certificates = []
        for certificate_arn in certificate_arns:
            response = client.describe_certificate(CertificateArn=certificate_arn)
            certificate = response['Certificate']

            # Remove time zone information so we can compare with normal datetimes.
            not_after = datetime.datetime.replace(certificate['NotAfter'], tzinfo=None)

            if not_after > limit:
                continue

            resource_wrapper = Resource(
                resource="Certificate for " + certificate['DomainName'],
                resource_type=self.resource_type,
                resource_id=certificate_arn,
                creation_date=certificate.get('CreatedAt', certificate.get('ImportedAt')),
                region="global",
                reason="will expired soon")
            self.logger.error("YIELD")
            yield resource_wrapper

    def to_string(self, resource):
        table = resource.wrapped
        return "{summary} with ARN {arn}, created at {creation_date} will expire soon.".format(
            summary=resource.wrapped, arn=resource.resource_id,
            creation_date=resource.creation_date)

    def delete(self, resource):
        if self.dry_run:
            return
        raise NotImplementedError("ACM certificates are never deleted.")
