# -*- coding: utf-8 -*-
# Copyright 2019-2021 CERN
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
#
# Authors:
# - Matt Snyder <msnyder@bnl.gov>, 2019-2021
# - Martin Barisits <martin.barisits@cern.ch>, 2019
# - Benedikt Ziemons <benedikt.ziemons@cern.ch>, 2020
# - Radu Carpa <radu.carpa@cern.ch>, 2021

import logging

from rucio.transfertool.transfertool import Transfertool
from .globus_library import bulk_submit_xfer, submit_xfer, bulk_check_xfers


class GlobusTransferTool(Transfertool):
    """
    Globus implementation of Transfertool abstract base class
    """
    def __init__(self, external_host):
        """
        Initializes the transfertool

        :param external_host:   The external host where the transfertool API is running
        """
        # TODO: initialize vars from config file here

    def submit(self, files, job_params, timeout=None):
        """
        Submit transfers to globus API

        :param files:        List of dictionaries describing the file transfers.
        :param job_params:   Dictionary containing key/value pairs, for all transfers.
        :param timeout:      Timeout in seconds.
        :returns:            Globus transfer identifier.
        """

        source_path = files[0]['sources'][0]
        logging.info('source_path: %s' % source_path)

        source_endpoint_id = files[0]['metadata']['source_globus_endpoint_id']

        # TODO: use prefix from rse_protocol to properly construct destination url
        # parse and assemble dest_path for Globus endpoint
        dest_path = files[0]['destinations'][0]
        logging.info('dest_path: %s' % dest_path)

        # TODO: rucio.common.utils.construct_url logic adds unnecessary '/other' into file path
        # s = dest_path.split('/') # s.remove('other') # dest_path = '/'.join(s)

        destination_endpoint_id = files[0]['metadata']['dest_globus_endpoint_id']
        job_label = files[0]['metadata']['request_id']

        task_id = submit_xfer(source_endpoint_id, destination_endpoint_id, source_path, dest_path, job_label, recursive=False)

        return task_id

    def bulk_submit(self, transfers, timeout=None):
        """
        Submit a bulk transfer to globus API

        :param files:        List of dictionaries describing the file transfers.
        :param job_params:   Dictionary containing key/value pairs, for all transfers.
        :param timeout:      Timeout in seconds.
        :returns:            Globus transfer identifier.
        """

        # TODO: support passing a recursive parameter to Globus
        submitjob = [
            {
                # Some dict elements are not needed by globus transfertool, but are accessed by further common fts/globus code
                'sources': [s[1] for s in transfer.legacy_sources],
                'destinations': [transfer.dest_url],
                'metadata': {
                    'src_rse': transfer.src.rse.name,
                    'dst_rse': transfer.dst.rse.name,
                    'scope': str(transfer.rws.scope),
                    'name': transfer.rws.name,
                    'source_globus_endpoint_id': transfer.src.rse.attributes['globus_endpoint_id'],
                    'dest_globus_endpoint_id': transfer.dst.rse.attributes['globus_endpoint_id'],
                    'filesize': transfer.rws.byte_count,
                },
            }
            for transfer in transfers
        ]
        task_id = bulk_submit_xfer(submitjob, recursive=False)

        return task_id

    def bulk_query(self, transfer_ids, timeout=None):
        """
        Query the status of a bulk of transfers in globus API

        :param transfer_ids: Globus task identifiers as a list.
        :returns: Transfer status information as a dictionary.
        """
        if not isinstance(transfer_ids, list):
            transfer_ids = [transfer_ids]

        job_responses = bulk_check_xfers(transfer_ids)

        return job_responses

    def bulk_update(self, resps, request_ids):
        """
        bulk update request_state for globus transfers

        :param resps: dictionary containing task IDs and current status
        # TODO: do we need request IDs?
        :param request_ids original list of rucio request IDs

        counter = 0
        for task_id in resps:
            requests = get_requests_by_transfer(external_host=None, transfer_id=task_id, session=None)
            logging.debug('requests: %s' % requests)
            for request_id in requests:
                transfer_core.update_transfer_state(external_host=None, transfer_id=request_id, state=resps[task_id][file_state])
                counter += 1

        return counter
        """
        pass

    def cancel(self):
        pass

    def query(self, transfer_ids, details=False, timeout=None):
        """
        Query the status of a transfer in Globus Online.

        :param transfer_ids: transfer identifiers as list of strings.
        :param details:      Switch if detailed information should be listed.
        :param timeout:      Timeout in seconds.
        :returns:            Transfer status information as a list of dictionaries.
        """
        pass

    def update_priority(self):
        pass
