import time
import sys
import argparse

from wikichangewatcher import (
    WikiChangeWatcher, FilterCollection, IpV4Filter, IpV6Filter,
    FieldRegexSearchFilter, UsernameRegexSearchFilter, MatchType, __version__
)

VERSION = "1.0.0"

DESCRIPTION = """
Real-time monitoring of global Wikipedia page edits, with flexible filtering
features.
"""

EPILOG = """
NOTE: if run without arguments, then all anonymous edits (any IPv4 or IPv6
address) will be shown.

EXAMPLES:

Show only edits made by one of two specific IP addresses:

    wikiwatch -a 89.44.33.22 -a 2001:0db8:85a3:0000:0000:8a2e:0370:7334

Show only edits made by IPv4 addresses in the range 88.44.0-33.0-22:

    wikiwatch -a 88.44.0-33.0-22

Show only edits made by IPv4 addresses in the range 232.22.0-255.0-255:

    wikiwatch -a 232.22.*.*

Show only edits made by usernames that contain the word "Bot" or "bot":

    wikiwatch -f user "[Bb]ot"\n
"""

def _main():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
                                     formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=80))

    parser.add_argument('-a', '--address', action='append', default=None, help=('Adds an IPv4 or Ipv6 address range to '
                        'look for. Any anonymous edits made by IPv4 addresses in this range will be displayed. '
                        'Each dot-separated field (for IPv4 addresses) or colon-separated field (for IPv6 addresses) '
                        'may be optionally replaced with with an asterisk (which acts as a wildcard, matching any '
                        'value), or a range of values. For example, the address range "*.22.33.0-55" would match all '
                        'IPv4 addresses in the range 0.22.33.0 through 255.22.33.50. This option can be used multiple '
                        'times to add multiple IP address filters.'))
    parser.add_argument('-u', '--username-regex', action='append', default=None, help=('Adds a username regex to look '
                        'for. Any edits made by logged-in users with a username that matches this regular expression '
                        'will be displayed. This option can be used multiple times to add multiple username filters.'))
    parser.add_argument('-f', '--field', action='append', nargs=2, metavar=('FIELD_NAME', 'VALUE_RGX'), default=None,
                        help=('Adds a regex to look for in a specific named field in the JSON event provided by the '
                        'wikimedia recent changes stream (described here '
                        'https://www.mediawiki.org/wiki/Manual:RCFeed). Any edit events which have a value matching '
                        'the VALUE_RGX regular expression stored in the FIELD_NAME field will be displayed. This '
                        'option can be used multiple times to add multiple named field filters.'))
    parser.add_argument('-s', '--format-string', action='store', default="{user} edited {title_url}", help=('Define a '
                        'custom format string to control how filtered results are displayed. Format tokens may be used '
                        'to display data from any named field in the JSON event described at '
                        'https://www.mediawiki.org/wiki/Manual:RCFeed. Format tokens must be in the form '
                        '"{field_name}", where "field_name" is the name of any field from the JSON event. This option '
                        'can only be used once (Default: "%(default)s").'))
    parser.add_argument('--version', action='store_true', default=False, help='Show version and exit.')
    args = parser.parse_args()

    if args.version:
        print(f"wikiwatch version {VERSION} (using wikichangewatcher-{__version__})")
        return 0

    # Callback function to run whenever an event matching our filters is seen
    def match_handler(json_data):
        """
        json_data is a JSON-encoded event from the WikiMedia "recent changes" event stream,
        as described here: https://www.mediawiki.org/wiki/Manual:RCFeed
        """
        try:
            msg = args.format_string.format(**json_data)
        except KeyError:
            pass
        else:
            print(msg)


    filters = []
    if (args.address is None) and (args.username_regex is None) and (args.field is None):
        print("No options provided, monitoring all anonymous edits by default")
        filters.extend([IpV4Filter(), IpV6Filter()])
    else:
        if args.address is not None:
            for addr in args.address:
                fltr = None

                try:
                    fltr = IpV4Filter(addr)
                except ValueError:
                    try:
                        fltr = IpV6Filter(addr)
                    except ValueError:
                        print(f"Error: invalid Ipv4 or Ipv6 address: {addr}")
                        return -1

                filters.append(fltr)

        if args.username_regex is not None:
            for rgx in args.username_regex:
                filters.append(UsernameRegexSearchFilter(rgx))

        if args.field is not None:
            for field_name, value_regex in args.field:
                filters.append(FieldRegexSearchFilter(field_name, value_regex))

    print(f"Using filters: {filters}")
    collection = FilterCollection(*filters).set_match_type(MatchType.ANY).on_match(match_handler)
    wc = WikiChangeWatcher(collection)
    wc.run()

    # Watch for page edits forever until KeyboardInterrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        wc.stop()

    return 0

def main():
    sys.exit(_main())

if __name__ == "__main__":
    main()
