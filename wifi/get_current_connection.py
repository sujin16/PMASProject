# win32wifi - Windows Native Wifi Api Python library.
# Copyright (C) 2016 - Shaked Gitelman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Shaked Gitelman   (almondg)   <shaked.dev@gmail.com>
#

import pprint
import sys
import socket
sys.path.append('../')

from win32wifi.Win32Wifi import getWirelessInterfaces
from win32wifi.Win32Wifi import queryInterface
import code

if __name__ == "__main__":
    myHostName = socket.gethostname()
    myIP =socket.gethostbyname(myHostName)
    print("Name of the localhost is {0}".format(myHostName))
    print("IP address of the localhost is {0} " +format(myIP))

    ifaces = getWirelessInterfaces()
    pp = pprint.PrettyPrinter(indent=4)
    for iface in ifaces:
        guid = iface.guid
        res = queryInterface(iface, "current_connection")  # wlan_intf_opcode_current_connection
        pp.pprint(res[1])
        