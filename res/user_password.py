
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

##############################################################################
# Convert password users to sha1
##############################################################################

import psycopg2
import hashlib

config = {}

def get_target_connection(config):
    return psycopg2.connect(
        database = config['target'],
        host = config['target_host'],
        port = config['target_port'],
        user = config['target_user'],
        password = config['target_password'])


if __name__ == '__main__':

    salt = 'kafkadb'

    with open('kettle.properties') as f:
        for line in f:
            tokens = line.split('=')
            config[tokens[0].strip()] = "=".join([x.strip() for x in tokens[1:]])

    target_db = get_target_connection(config)
    #~ target_db.set_session(deferrable=True)
    targetCR = target_db.cursor()

    targetCR.execute('SELECT login, password from res_user where id > 2')          
    for user in targetCR.fetchall():
        login = user[0]
        password = user[1]

        if not password:
            continue

        password = password+salt
        pswd = hashlib.sha1(password).hexdigest()
        targetCR.execute("UPDATE res_user SET password = '%(password)s', salt = '%(salt)s' WHERE login = '%(login)s';" % {
                'password': pswd,
                'salt': salt,
                'login': login,
            })
        target_db.commit()
        print "Updated password user %s" % login

    target_db.close()
