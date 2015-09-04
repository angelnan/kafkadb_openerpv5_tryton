#! /usr/bin/env python
# -*- encoding: utf-8 -*-

###############################################################################
#
#    Simple ETL for OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>).
#    All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

DEBUG = True

"""
OpenERP Webservice Connection
"""
oerp_xmlrpc_conf = {
    'username': 'admin',
    'password': 'admin',
    'dbname': 'oerp5_oarlan2',
    #xmlrpc
    'protocol': 'xmlrpc',
    'uri': 'http://localhost',
    'port': 8069,
    #pyro
#    'protocol': 'pyro',
#    'uri': 'localhost',
#    'port': 8071,
    }

"""
TrytonDB PostgreSQL Connection
"""
tryton_db_conf = {
    'username': 'aneolf',
    'password': 'ForcaBarca',
    'dbname': 'try32_oarlan2',
    'host': 'localhost',
    'port': 5432,
    }

tryton_target_path = '/var/lib/trytond/'