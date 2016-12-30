# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# import os
import ssl
# import xml.etree.ElementTree as ET
import boto
from boto import s3
from boto.exception import S3ResponseError
import boto.s3.connection
from monocyte.handler import Resource, Handler

US_STANDARD_REGION = "us-east-1"
SIGV4_REGIONS = ['eu-central-1']
AVAILABILITY_ZONES = {'EU': 'eu-west-1'}


class Bucket(Handler):
    NR_KEYS_TO_SHOW = 4

    def __init__(self, *args, **kwargs):
        self._old_match_hostname = getattr(ssl, 'match_hostname', None)
        ssl.match_hostname = self._new_match_hostname
        super(Bucket, self).__init__(*args, **kwargs)

    def _new_match_hostname(self, cert, hostname):
        hostnames = ['.s3{0}{1}.amazonaws.com'.format(separator, region.name)
                     for separator in ['.', '-'] for region in self.regions]
        hostnames.extend(['.s3.amazonaws.com', '.s3-amazonaws.com'])
        for hname in hostnames:
            if hostname.endswith(hname):
                pos = hostname.find(hname)
                hostname = hostname[:pos].replace('.', '') + hostname[pos:]
        return self._old_match_hostname(cert, hostname)

    def map_location(self, region):
        return AVAILABILITY_ZONES.get(region, region)

    def fetch_regions(self):
        return s3.regions()

    def fetch_unwanted_resources(self):
        checked_buckets = []
        for region in self.regions:
            self.logger.info('Checking connected region %s', region.name)
            conn = self.connect_to_region(region.name)
            for bucket in conn.get_all_buckets():
                result = self.check_if_unwanted_resource(conn, bucket,
                                                         checked_buckets)
                if result:
                    yield result
        #os.putenv('S3_USE_SIGV4', 'False')

    def check_if_unwanted_resource(self, conn, bucket, checked_buckets):
        if bucket.name in checked_buckets:
            return
        try:
            region = bucket.get_location()
        except S3ResponseError as exc:
            if exc.status == 400:
                #if exc.error_code == 'AuthorizationHeaderMalformed':
                #    # Fix conn's region in case it was wrong
                #    # TODO: Check coverage; is this code really used?
                #    conn.auth_region_name = ET.fromstring(exc.body).find(
                #        './Region').text
                #    region = conn.auth_region_name
                #    self.logger.warning(
                #        "bucket %s wrong location -> location "
                #        "updated for connection: %s", bucket.name, region)
                #else:
                # See https://github.com/boto/boto/issues/2741
                self.logger.warning("get_location() crashed for %s, "
                                 "skipping", bucket.name)
            elif exc.status == 404:
                # This can happen due to race conditions (bucket being deleted
                # just now).
                # Also, local testing showed the curious case of a deleted
                # bucket that was still listed in four regions.
                self.logger.warning(
                    "Bucket '%s' was found by get_all_buckets(), but "
                    "get_location() failed with 404 Not Found", bucket.name)
            else:
                self.logger.error("Failed to get location for bucket "
                                      "{0}".format(bucket.name))
            return
        except ssl.CertificateError as exc:
            # Bucket is in a SIGV4 Region but connection is not SIGV4
            self.logger.warning('ssl.CertificateError for bucket %s with '
                             'connected host %s', bucket.name,
                             conn.host)
            return
        region = region if region else US_STANDARD_REGION
        checked_buckets.append(bucket.name)
        if self.region_filter(region):
            resource_wrapper = Resource(resource=bucket,
                                        resource_type=self.resource_type,
                                        resource_id=bucket.name,
                                        creation_date=bucket.creation_date,
                                        region=self.map_location(
                                            region))
            if bucket.name in self.ignored_resources:
                self.logger.info(
                    'IGNORE ' + self.to_string(resource_wrapper))
                return
            return resource_wrapper

    def to_string(self, resource):
        return "s3 bucket found in {0}, with name {1}, created {2} and {3} entries".format(
            resource.region, resource.wrapped.name,
            resource.wrapped.creation_date,
            len(self.apply_bucket_function(resource, 'get_all_keys')))

    def summary(self, resource):
        num_keys = len(self.apply_bucket_function(resource, 'get_all_keys'))
        skipped_keys = 0
        key_summary = []
        for nr, key in enumerate(self.apply_bucket_function(resource, 'list')):
            if nr >= Bucket.NR_KEYS_TO_SHOW:
                skipped_keys = num_keys - Bucket.NR_KEYS_TO_SHOW
                break
            key_summary.append(key.name)
        return num_keys, ', '.join(key_summary), skipped_keys

    def delete(self, resource):
        if self.dry_run and resource.wrapped.name != 'mk11.eu-central':
            num_keys, key_summary, skipped_keys = self.summary(resource)
            msg = "%s: %s entries would be removed: %s" % (
                resource.wrapped.name, num_keys, key_summary)
            if skipped_keys:
                msg += "... %s keys omitted" % skipped_keys
            self.logger.info(msg)
        else:
            keys_list = self.apply_bucket_function(resource, 'list')
            self.apply_bucket_function(resource=resource,
                                       function_name='delete_keys',
                                       keys=keys_list)
            self.logger.info("Initiating deletion of %s", resource.wrapped.name)
            self.apply_s3_function(resource=resource,
                                   function_name='delete_bucket',
                                   bucket=resource.wrapped.name)

    def connect_to_region(self, region, bucket_name=''):
        kwargs = {'region_name': region}
        if region in SIGV4_REGIONS:
            #os.putenv('S3_USE_SIGV4', 'True')
            kwargs['host'] = 's3.{0}.amazonaws.com'.format(region)
        #else:
        #    os.putenv('S3_USE_SIGV4', 'False')
        if '.' in bucket_name:
            kwargs[
                'calling_format'] = boto.s3.connection.OrdinaryCallingFormat()
        return s3.connect_to_region(**kwargs)

    def apply_bucket_function(self, resource, function_name, **kwargs):
        conn = self.connect_to_region(resource.region,
                                      resource.wrapped.name)
        bucket = conn.get_bucket(resource.wrapped.name)
        return getattr(bucket, function_name)(**kwargs)

    def apply_s3_function(self, resource, function_name, **kwargs):
        conn = self.connect_to_region(resource.region,
                                      resource.wrapped.name)
        return getattr(conn, function_name)(**kwargs)
