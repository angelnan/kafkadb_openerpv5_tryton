#! /usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2011-2013 NaN Projectes de Programari Lliure, S.L.
# http://www.NaN-tic.com
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import sys

sys.path.append(os.path.abspath(os.getcwd()))
from KafkaDB import tools

config = tools.read_kettle_properties()
source_db = tools.get_source_connection(config)
target_db = tools.get_target_connection(config)
source_cursor = source_db.cursor()
target_cursor = target_db.cursor()
migration_filename = config.get('migration_config')
migration = tools.readConfigFile(migration_filename)
ir_path = os.path.join(config.get('transformation_path'), 'ir/')
model_mapping = tools.readConfigFile(ir_path + 'ir_model_mapping.cfg')
#field_mapping = tools.readConfigFile(ir_path + 'ir_field_mapping.cfg')
property_mapping = tools.readConfigFile(ir_path + 'ir_property_mapping.cfg')
models = {}
fields = {}

for target, source in model_mapping['models'].iteritems():
    if source:
        models[source] = target


def get_mapping_id(table, value_id):
    target_cursor.execute("SELECT target FROM migration." + table +
            " WHERE source=" + str(value_id))
    target_id = target_cursor.fetchone()
    if target_id:
        return target_id[0]
    return None


def get_field_id(model, field):
    target_cursor.execute(
            "SELECT f.id "
            "FROM  "
            "ir_model_field f,"
            "ir_model m "
            "WHERE "
            " f.model = m.id AND "
            " m.model='%s' AND"
            " f.name = '%s'" % (model, field))
    fields = target_cursor.fetchone()
    field = fields[0] if fields else None
    return field


def add_property(res_model, res_id, value_model, value_id, field, company):

    res = None
    value = None
    rid = res_id
    vid = value_id

    res_map = get_map_table(res_model)
    val_map = get_map_table(value_model)

    res_map_table = migration.get(res_map) and \
        migration[res_map].get('mapping')
    val_map_table = migration.get(val_map) and \
        migration[val_map].get('mapping')

    if res_map_table and (res_map_table != 'None'):
        rid = get_mapping_id(res_map_table, res_id)
    if val_map_table:
        vid = get_mapping_id(val_map_table, value_id)

    if res_model:
        res = res_model + "," + str(rid)
    if vid:
        value = value_model + "," + str(vid)
    if field:
        target_cursor.execute(
            'INSERT INTO ir_property(res, value, field, company)'
            ' VALUES(%s,%s,%s,%s)', (res, value, field, company))


def get_map_table(model):
    if model:
        return model.replace('.', '_')
    return model


def create_property(target_model, source_model, property, sfield, rel_model):
    table_sm = get_map_table(source_model)
    query = "select id, %s from %s" % (sfield, table_sm)
    source_cursor.execute(query)
    company = 1
    for row in source_cursor.fetchall():
        res_id, value_id = row
        if value_id is None:
            continue
        field = get_field_id(target_model, property)
        add_property(target_model, res_id, rel_model, value_id, field, company)


def migrate_property(target_model, source_model, target, source):
    query = ("select ip.res_id, ip.name, ip.value, ip.company_id from "
        "ir_property as ip, "
        "ir_model_fields as imf, "
        "ir_model as im  "
        "where imf.model_id = im.id and "
        "   ip.fields_id = imf.id and "
        "   ip.name='%s' "
        "   and ip.value is not null and "
        " im.model = '%s'" % (source, source_model))

    source_cursor.execute(query)
    for row in source_cursor.fetchall():
        res, name, value, company = row
        res_model = False
        res_id = None
        value_model = False
        value_id = None

        if res:
            res_model, res_id = res.split(',')
        if value:
            value_model, value_id = value.split(',')

        target_model_res = models.get(res_model)
        target_model_val = models.get(value_model)
        field = get_field_id(target_model, target)

        add_property(target_model_res, res_id, target_model_val,
            value_id, field, company)


if __name__ == '__main__':

    for section in property_mapping:
        module, target_model = section.split('/')
        pm = property_mapping[section]
        model_source = pm.pop('source')
        convert = eval(pm.pop('convert'))
        prop = {}
        for ptarget, psource in pm.iteritems():
            tp, model = tuple(psource.split(','))

            if tp in convert:
                create_property(target_model, model_source,
                    ptarget, tp, model)
            else:
                migrate_property(target_model, model_source, ptarget, tp)

    target_db.commit()
    target_db.close()
    source_db.close()
