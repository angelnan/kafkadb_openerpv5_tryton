#!/usr/bin/python
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

import os,sys


sys.path.append('/home/angel/projectes/kafkadb/')

from KafkaDB import tools


config = tools.read_kettle_properties()
source_db = tools.get_source_connection(config)
target_db = tools.get_target_connection(config)

source_cursor = source_db.cursor()
target_cursor = target_db.cursor()

migration_filename = os.path.join(config['kafka_db'], 'migration.cfg')
migration = tools.readConfigFile(migration_filename)


model_mapping = tools.readConfigFile('ir_model_mapping.cfg')
field_mapping = tools.readConfigFile('ir_field_mapping.cfg')
property_mapping = tools.readConfigFile('ir_property_mapping.cfg')

model = {}
properties = {}
fields ={}

for target,source in model_mapping['models'].iteritems():
    if source:
        model[source]=target

for target,source in property_mapping['property'].iteritems():
    if source:
        properties[source]=target

for m,fields_dict in field_mapping.iteritems():
    fields[m]={}
    for target_field,source_field in fields_dict.iteritems():
        fields[m][source_field]=target_field
    
def get_mapping_id(table,value_id):
    target_cursor.execute("SELECT target FROM migration." + table +
            " WHERE source="+str(value_id))
    print target_cursor.query
    return target_cursor.fetchone()[0]

def get_field_id(model, field):
    target_cursor.execute( 
            "SELECT f.id "
            "FROM  "
            "ir_model_field f,"
            "ir_model m "
            "WHERE "
            " f.model = m.id AND "
            " m.model=%s AND"
            " f.name=%s",(model, field))
    print target_cursor.query
    return target_cursor.fetchone()[0]

def get_target_field(model, field):
    return fields.get(model) and \
            fields[model].get(field)



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

    if res_map_table:
        rid=get_mapping_id(res_map_table,res_id)
    if val_map_table:
        vid= get_mapping_id(val_map_table,value_id)

    if res_model:
        res = res_model+","+str(rid)
    if vid:
        value = value_model+","+str(vid)
    
    tfield = get_target_field(res_model, field)
    if not tfield:
        print "FIELD %s not mapping yet"%field

    field = get_field_id(res_model,tfield)

    target_cursor.execute(
            'INSERT INTO ir_property(res,value,field,company)'
            ' VALUES(%s,%s,%s,%s)',(res, value, field, company)) 
    print target_cursor.query

def get_map_table(model):
    if model:
        return model.replace('.','_')
    return model



source_cursor.execute("SELECT res_id,name,value,company_id FROM ir_property")
for row in source_cursor.fetchall():
    res,name,value,company = row
    
    if not properties.get(name):
        print "Property %s Not Mapped yet"%name
        continue

    res_model = False
    res_id = None
    value_model = False
    value_id = None

    if res:
        res_model,res_id = res.split(',')
    if value:
        value_model,value_id = value.split(',')

    res_map = get_map_table(res_model)
    val_map = get_map_table(value_model)

    if not model.get(value_model) or not model.get(res_model) or \
           not migration.get(res_map) or \
           not migration.get(val_map):
        print "Models not mapped yet , check %s,%s"%(value_model,res_model)
        continue


    print "--------------------------------------------"
    print res_model,res_id, value_model,value_id, name
    add_property(res_model,res_id, value_model,value_id, name, company) 

    
target_db.commit()
target_db.close()
source_db.close()





