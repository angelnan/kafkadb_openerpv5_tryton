
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

import hashlib
import string
import random
import os
import sys

sys.path.append(os.path.abspath(os.getcwd()))
from KafkaDB import tools

config = tools.read_kettle_properties()
source_db = tools.get_source_connection(config)
target_db = tools.get_target_connection(config)

if __name__ == '__main__':

    targetCR = target_db.cursor()

    targetCR.execute("SELECT id, password_hash from res_user where "
        "login not like 'user_cron%' and login != 'root'")
    users = targetCR.fetchall()
    for uid, password in users:
        if not password or '$' in password:
            continue
        salt = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        password += salt
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        password = hashlib.sha1(password).hexdigest()
        password_hash = '$'.join(['sha1', password, salt])
        targetCR.execute("UPDATE res_user SET password_hash=%s WHERE id=%s",
            (password_hash, uid))
    target_db.commit()
    target_db.close()
