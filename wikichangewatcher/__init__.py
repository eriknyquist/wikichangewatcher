__author__ = "Erik Nyquist"
__license__ = "Apache 2.0"
__maintainer__ = "Erik Nyquist"
__version__ = "1.0.0"
__email__ = "eknyquist@gmail.com"

from wikichangewatcher.wikichangewatcher import FieldFilter, FilterCollection, IpV4Filter, IpV6Filter, WikiChangeWatcher, MatchType
from wikichangewatcher.wikichangewatcher import FieldRegexSearchFilter, UsernameRegexSearchFilter, PageUrlRegexSearchFilter

import logging
logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(module)s:%(lineno)s]: %(message)s")

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.info(f"wikichangewatcher {__version__}")
