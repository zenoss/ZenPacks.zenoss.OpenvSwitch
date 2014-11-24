##############################################################################
#
# GPLv2
#
# You should have received a copy of the GNU General Public License
# along with this ZenPack. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import re

from Products.AdvancedQuery import And, Eq
from ZODB.transact import transact

from Products.Zuul.interfaces import ICatalogTool

from Products.ZenUtils.guid.interfaces import IGlobalIdentifier
from collections import deque
import dateutil
import datetime
import functools
import importlib
import pytz
import time

from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError, TimeoutError
from twisted.internet.task import deferLater

import logging
LOG = logging.getLogger('zen.OpenvSwitch.utils')


def zenpack_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def zenpack_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def add_local_lib_path():
    '''
    Helper to add the ZenPack's lib directory to sys.path.
    '''
    import site

    # The novaclient library does some elaborate things to figure out
    # what version of itself is installed. These seem to not work in
    # our environment for some reason, so we override that and have
    # it report a dummy version that nobody will look at anyway.
    #
    # So, if you're wondering why novaclient.__version__ is 1.2.3.4.5,
    # this is why.
    os.environ['PBR_VERSION'] = '1.2.3.4.5'

    site.addsitedir(os.path.join(os.path.dirname(__file__), '.'))
    site.addsitedir(os.path.join(os.path.dirname(__file__), 'lib'))

add_local_lib_path()

