#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
#    Simple ETL for OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Zikzakmedia S.L. (<http://www.zikzakmedia.com>).
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

from db_config import oerp_xmlrpc_conf, tryton_db_conf, tryton_target_path, \
    DEBUG
import base64
import hashlib
import os
import psycopg2
import xmlrpclib


map_models = {
    'account.bank.statement': 'account.statement',
    'account.invoice': 'account.invoice',
    'l10n.es.aeat.mod347.report': 'aeat.347.report',
    'product.product': 'product.product',
    'purchase.order': 'purchase.purchase',
    'res.partner': 'party.party',
    'sale.order': 'sale.sale',
    }

def get_db_connection(config):
    return psycopg2.connect(
        database=config['dbname'],
        host=config['host'],
        port=config['port'],
        user=config['username'],
        password=config['password'])

def main():
    oerp_user = oerp_xmlrpc_conf['username']
    oerp_pwd = oerp_xmlrpc_conf['password']
    oerp_dbname = oerp_xmlrpc_conf['dbname']
    oerp_protocol = oerp_xmlrpc_conf['protocol']
    oerp_uri = oerp_xmlrpc_conf['uri']
    oerp_port = oerp_xmlrpc_conf['port']
#    allow_none = True
    oerp_uid_sock = xmlrpclib.ServerProxy('%s:%s/%s/common' % (oerp_uri,
            oerp_port, oerp_protocol))
    oerp_uid = oerp_uid_sock.login(oerp_dbname, oerp_user, oerp_pwd)

    oerp_sock = xmlrpclib.ServerProxy('%s:%s/%s/object' % (oerp_uri, oerp_port,
            oerp_protocol))
    oerp_attachment_ids = oerp_sock.execute(oerp_dbname, oerp_uid, oerp_pwd,
        'ir.attachment', 'search', [])
    if DEBUG:
        print oerp_attachment_ids

    tryton_db = get_db_connection(tryton_db_conf)
    tryton_cursor = tryton_db.cursor()
    tryton_cursor.execute(
        "SELECT "
            "* "
        "FROM "
            "migration.user_mapping"
        )
    map_user = dict(tryton_cursor.fetchall())

    tryton_cursor.execute(
        "SELECT "
            "* "
        "FROM "
            "migration.party_party_mapping"
        )
    map_party = dict(tryton_cursor.fetchall())

    attachments = oerp_sock.execute(oerp_dbname, oerp_uid, oerp_pwd,
        'ir.attachment', 'read', oerp_attachment_ids, [
            'id',
            'create_date',
            'write_date',
            'create_uid',
            'write_uid',
            'description',
            'file_type',  # file_type in OERP5
            'res_model',
            'res_id',
            'datas',
            'datas_fname',
            ])

    for attach in attachments:

        hash = hashlib.md5()
        hash.update(attach['datas_fname'])
        digest = hash.hexdigest()
        path = '%s%s/%s/%s' % (tryton_target_path, tryton_db_conf['dbname'],
            digest[:2], digest[2:4])
        if not os.path.exists(path):
            os.makedirs(path)

        with open('%s/%s' % (path, digest),'w') as file:
            file.write(base64.decodestring(attach['datas']))

        resource = False
        if attach['res_model'] in map_models:
            if attach['res_model'] == 'res.partner':
                resource = ('%s,%s' %
                    (map_models[attach['res_model']],
                        map_party[attach['res_id']]))
            else:
                resource = ('%s,%s' %
                    (map_models[attach['res_model']], attach['res_id']))
        if resource:
            create_date = ("'%s'" % attach['create_date']
                if attach['create_date'] else 'NULL')
            write_date = ("'%s'" % attach['write_date']
                if attach['write_date'] else 'NULL')
            create_uid = ("'%s'" % map_user[attach['create_uid'][0]]
                if attach['create_uid'] else '1')
            write_uid = ("'%s'" % map_user[attach['write_uid'][0]]
                if attach['write_uid'] else 'NULL')
            description = ("'%s'" % attach['description']
                if attach['description'] else 'NULL')
            type = (attach['file_type']
                if attach.get('file_type', False)
                and attach['file_type'] in ('data', 'link')
                else 'data')
            query = (
                "INSERT INTO ir_attachment ("
                    "id, "
                    "create_date, "
                    "write_date, "
                    "create_uid, "
                    "write_uid, "
                    "description, "
                    "type, "
                    "collision, "
                    "resource, "
                    "digest, "
                    "name"
                    ") "
                "VALUES ("
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "%s, "
                    "'%s', "
                    "%s, "
                    "'%s', "
                    "'%s', "
                    "'%s')"
                % (
                    attach['id'],
                    create_date,
                    write_date,
                    create_uid,
                    write_uid,
                    description,
                    type,
                    0,
                    resource,
                    digest,
                    attach['datas_fname'],
                    )
                )
            tryton_cursor.execute(query)

        if DEBUG:
            print (attach['id'], attach['datas_fname'])
    
#         if attach['datas']:
#             store_fname = '%s%s-%s' % (path, attach['id'],
#                 attach['datas_fname'])
#             f = open(store_fname, 'wb')
#             #s = base64.encodestring(attach['datas'] or '')
#             s = base64.decodestring(attach['datas'] or '')
#             f.write(s)
#             f.close()
#             value = {
#                 'store_fname': store_fname,
#             }
#             sock.execute(dbname, uid, pwd, 'ir.attachment', 'write',
#                 [attach['id']], value)
#             print '[ADDED]: ', attach_id
#         else:
#             print '[SKIPPED]: ', attach_id
#     
#         values = {
#             'storage_id': document_storage['id'],
#         }
#     
#         print document_directories
#         print values
#         for document_directory in document_directories:
#             sock.execute(dbname, uid, pwd, 'document.directory', 'write',
#                 [document_directory], values)
    tryton_db.commit()
    tryton_db.close()

    return True

if __name__ == '__main__':
    main()