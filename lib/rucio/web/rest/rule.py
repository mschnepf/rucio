#!/usr/bin/env python
# Copyright European Organization for Nuclear Research (CERN)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Vincent Garonne, <vincent.garonne@cern.ch>, 2012
# - Martin Barisits, <martin.barisits@cern.ch>, 2013

import datetime

from logging import getLogger, StreamHandler, DEBUG
from json import dumps, loads

from web import application, ctx, data, header, BadRequest, Created, InternalError, Unauthorized, OK

from rucio.api.authentication import validate_auth_token
from rucio.api.rule import add_replication_rule, delete_replication_rule, get_replication_rule
from rucio.common.exception import InsufficientQuota, RuleNotFound, AccessDenied
from rucio.common.utils import generate_http_error

logger = getLogger("rucio.rule")
sh = StreamHandler()
sh.setLevel(DEBUG)
logger.addHandler(sh)

urls = ('/', 'Rule',
        '/(.+)', 'Rule')


class Rule:
    """ REST APIs for replication rules. """

    def GET(self, rule_id):
        """ get rule information for given rule id.

        HTTP Success:
            200 OK

        HTTP Error:
            401 Unauthorized
            404 Not Found
            500 InternalError

        :returns: JSON dict containing informations about the requested user.
        """

        auth_token = ctx.env.get('HTTP_X_RUCIO_AUTH_TOKEN')

        auth = validate_auth_token(auth_token)

        if auth is None:
            raise generate_http_error(401, 'CannotAuthenticate', 'Cannot authenticate with given credentials')

        try:
            rule = get_replication_rule(rule_id)
        except RuleNotFound, e:
            raise generate_http_error(404, 'RuleNotFound', e.args[0][0])
        except Exception, e:
            raise InternalError(e)

        dict = rule
        for key, value in dict.items():
            if isinstance(value, datetime):
                dict[key] = value.strftime('%Y-%m-%dT%H:%M:%S')

        return dumps(dict)

    def PUT(self):
        raise BadRequest()

    def POST(self):
        """
        Create a new replication rule.

        HTTP Success:
            201 Created

        HTTP Error:
            400 Bad Request
            401 Unauthorized
            404 Not Found
            409 Conflict
            500 Internal Error
        """

        header('Content-Type', 'application/octet-stream')
        auth_token = ctx.env.get('HTTP_X_RUCIO_AUTH_TOKEN')

        auth = validate_auth_token(auth_token)

        if auth is None:
            raise Unauthorized()

        json_data = data()
        try:
            params = loads(json_data)
            dids = params['dids']
            account = params['account']
            copies = params['copies']
            rse_expression = params['rse_expression']
            grouping = params['grouping']
            weight = params['weight']
            lifetime = params['lifetime']
            locked = params['locked']
            subscription_id = params['subscription_id']
        except ValueError:
            raise generate_http_error(400, 'ValueError', 'Cannot decode json parameter list')

        try:
            rule_ids = add_replication_rule(dids=dids, copies=copies, rse_expression=rse_expression, weight=weight, lifetime=lifetime, grouping=grouping, account=account, locked=locked, subscription_id=subscription_id, issuer=auth['account'])
        #TODO: Add all other error cases here
        except InsufficientQuota, e:
            raise generate_http_error(409, 'InsufficientQuota', e.args[0][0])
        except Exception, e:
            raise InternalError(e)
        raise Created(dumps(rule_ids))

    def DELETE(self, rule_id):
        """
        Delete a new replication rule.

        HTTP Success:
            200 OK

        HTTP Error:
            401 Unauthorized
            404 Not Found
            500 Internal Error
        """

        header('Content-Type', 'application/octet-stream')
        auth_token = ctx.env.get('HTTP_X_RUCIO_AUTH_TOKEN')

        auth = validate_auth_token(auth_token)

        if auth is None:
            raise Unauthorized()
        try:
            delete_replication_rule(rule_id=rule_id, issuer=auth['account'])
        except AccessDenied, e:
            raise generate_http_error(401, 'AccessDenied', e.args[0][0])
        except RuleNotFound, e:
            raise generate_http_error(404, 'RuleNotFound', e.args[0][0])
        except Exception, e:
            raise InternalError(e)
        raise OK()


"""----------------------
   Web service startup
----------------------"""

app = application(urls, globals())
application = app.wsgifunc()
