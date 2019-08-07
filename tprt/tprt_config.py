"""
Argument parsing and configuration functions for tprt
Not really a standalone module, but separated out because of the length
of the argparse configuration lists
"""

# Arguments associated with a particular function are listed after the
# function by adding them to an array to be parsed by argparse in
# config_helpers.collect_arguments().  This keeps the two places where
# configuration entries are defined close to each other

# Logging is not used here because most functions will be run before logging
# is set up


import grp
import logging
import pwd
import socket

import config_helpers


# Settings used by config_helpers
config_helpers.program_name = 'tprt'
config_helpers.program_description = 'Greylisting Policy Daemon'
config_helpers.program_version = '0.9.3'


# defaults that could or should be changed by distribution maintainers
config_path_default = '/usr/local/etc/tprt/tprt.conf'
socket_path_default = '/var/run/tprt/socket'
pid_file_path_default = '/var/run/tprt/tprt.pid'
grey_db_default = 'gdbm:///var/db/tprt/greylistdb'
awl_db_default = 'gdbm:///var/db/tprt/autowldb'
wl_sources_default = [ 'file:///var/db/tprt/whitelist' ]

config_helpers.default_config_file = config_path_default

def initialize_config(config):
    """
    Prepare the configuration tree so that the later functions can be called
    """
    config_helpers.collect_arguments(config)
    config_helpers.read_config(config)


def configure_logging(config):
    """
    Turn arguments and config file contents into logging configuration
    Returns the completed logging configuration as a dict
    """
    def _transform_log_level():
        """transform the external log level into a logger logging level"""
        log_level_mapping = [ logging.NOTSET,
                              logging.WARNING,
                              logging.INFO,
                              logging.DEBUG ]
        config['log']['log_level'] = \
            log_level_mapping[int(config['log']['log_level'])]

    def _transform_syslog_dest():
        """Turn a string host:port combination into the needed entries"""
        if ':' in config['log']['log_syslog_dest']:
            hostname,port = config['log']['log_syslog_dest'].split(':')
            config['log']['log_syslog_dest'] = (hostname, int(port))

    config['log'] = {}
    parameters = [ ('log_type', 'stderr'),
                   ('log_level', 2),
                   ('log_file', ''),
                   ('log_facility', 'mail'),
                   ('log_syslog_dest', '/dev/log'),
                   ('config', {})
    ]
    for param in parameters:
        config_helpers.set_parameter(config, 'log', *param)
    _transform_log_level()
    _transform_syslog_dest()

# arguments handled by configure_logging
config_helpers.arg_list.append(
    [ [ '--log_type' ],
      { 'dest' : 'log.log_type',
        'action' : config_helpers.nestedAction,
        'choices' : [ 'stderr', 'file', 'syslog', 'from_config', 'none' ],
        'help' : 'Where log messages go, default is stderr'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--log_level', '-l' ],
      { 'type' : int,
        'choices' : range(0,4),
        'dest' : 'log.log_level',
        'action' : config_helpers.nestedAction,
        'help' : ( 'Logging Level: 0 is no logging, 1 is minimal, '
                   '2 is normal, 3 is debug' )
      } ] 
)
config_helpers.arg_list.append(
    [ [ '--log_file' ],
      { 'dest' : 'log.log_file',
        'action' : config_helpers.nestedAction,
        'metavar' : '<file>',
        'help' : 'The file to log to, for logging to file'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--log_facility' ],
      { 'dest' : 'log.log_facility',
        'action' : config_helpers.nestedAction,
        'metavar' : '<facility>',
        'help' : ( 'The syslog facility to log to.  Must be one of the '
                   'facility names supported by the Python syslog handler' )
      } ]
)
config_helpers.arg_list.append(
    [ [ '--log_syslog_dest' ],
      { 'dest' : 'log.log_syslog_dest',
        'action' : config_helpers.nestedAction,
        'metavar' : '<file>|<hostname>:<port>',
        'help' : 'The syslog instance to talk to, defaults to /dev/log'
      } ]
)


def configure_service(config):
    """
    Turn arguments and config file contents into service configuration
    Returns the completed service configuration as a dict
    """
    config['service'] = {}
    parameters = [ ('grey_hostname', socket.gethostname()),
                   ('grey_delay', 300),
                   ('ipv4_mask', 24),
                   ('ipv6_mask', 48),
                   ('grey_action', 'DEFER_IF_PERMIT'),
                   ('grey_text', 'Greylisted, please retry in {wait} seconds'),
                   ('grey_max_age', 3024000),
                   ('maintenance_interval', 3600),
                   ('hash_grey_db', True),
                   ('grey_retry_window', 172800),
                   ('grey_smtp_header',
                       "X-Greylist: delayed {delay} seconds at {hostname}; "
                       "{date}" ),
                   ('grey_db', grey_db_default),
                   ('grey_db_maintenance_disable', False),
                   ('awl_client_count', 0),
                   ('awl_db', awl_db_default),
                   ('awl_db_maintenance_disable', False),
                   ('wl_sources', wl_sources_default),
                   ('allow_wl_regex', False)
    ]
    for param in parameters:
        config_helpers.set_parameter(config, 'service', *param)

# arguments handled by configure_service
config_helpers.arg_list.append(
    [ [ '--hostname' ],
      { 'dest' : 'service.grey_hostname',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'The hostname to present in responses to the sender'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--delay' ],
      { 'dest' : 'service.grey_delay',
        'type' : int,
        'action' : config_helpers.nestedAction,
        'metavar' : '<seconds>',
        'help' : 'Greylisting delay in seconds'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--grey_db' ],
      { 'dest' : 'service.grey_db',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'URL for the greylisting db'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--awl_client_count' ],
      { 'dest' : 'service.awl_client_count',
        'type' : int,
        'metavar' : '<int>',
        'action' : config_helpers.nestedAction,
        'help' : ( 'Number of remote emails delivered before '
                   'auto-whitelisting, 0 means no auto-whitelist, default 0' )
      } ]
)
config_helpers.arg_list.append(
    [ [ '--awl_db' ],
      { 'dest' : 'service.awl_db',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'URL for the auto-whitelist db'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--wl_sources' ],
      { 'dest' : 'service.wl_sources',
        'type' : list,
        'action' : config_helpers.nestedAction,
        'metavar' : '<list_of_strings>',
        'help' : 'Comma-separated list of URLs to read whitelists from'
      } ]
)


def configure_server(config):
    """
    Turn arguments and config file contents into server configuration
    Returns the completed server configuration as a dict
    """
    def _transform_user_and_group():
        """
        User and group are provided as strings, the code needs uids and gids
        Also find the specified user's home directory here since getpwnam()
        provides it and it is needed as a default
        """
        if config['server']['daemonize']:
            entry = pwd.getpwnam(config['server']['user'])
            config['server']['uid'] = entry[2]
            config['server']['userdir'] = entry[5]
            config['server']['gid'] = grp.getgrnam(
                config['server']['group'])[2]

    config['server'] = {}
    parameters = [ ('socket_type', 'unix'),
                   ('socket_mode', '0660'),
                   ('socket_path', socket_path_default),
                   ('socket_listen_host', 'localhost'),
                   ('socket_listen_port', 10023),
                   ('listen_queue_size', 5),
                   ('reuse_socket', True),
                   ('daemonize', False),
                   ('chroot', False),
                   ('chroot_dir', ''),
                   ('user', 'postgrey'),
                   ('group', 'postgrey'),
                   ('pid_file_path', pid_file_path_default)
    ]
    for param in parameters:
        config_helpers.set_parameter(config, 'server', *param)
    _transform_user_and_group()

# arguments handled by configure_server
config_helpers.arg_list.append(
    [ [ '--socket_type' ],
      { 'dest' : 'server.socket_type',
        'choices' : { 'inet', 'unix' },
        'action' : config_helpers.nestedAction,
        'help' : 'Type of socket to create for communication with postfix'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--socket_mode' ],
      { 'dest' : 'server.socket_mode',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'Filesystem permissions to set on socket, in string form'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--socket_path' ],
      { 'dest' : 'server.socket_path',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'Path for unix socket'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--socket_listen_host' ],
      { 'dest' : 'server.socket_listen_host',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'Hostname (IP) for network (inet) socket, eg. "localhost"'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--socket_listen_port' ],
      { 'dest' : 'server.socket_listen_port',
        'action' : config_helpers.nestedAction,
        'type' : int,
        'metavar' : '<int>',
        'help' : 'Port for network (inet) socket, default 10023'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--daemonize' ],
      { 'dest' : 'server.daemonize',
        'type' : bool,
        'action' : config_helpers.nestedAction,
        'choices' : { 'True', 'False' },
        'help' : 'Run %(prog)s as daemon rather than in foreground'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--chroot' ],
      { 'dest' : 'server.chroot',
        'type' : bool,
        'action' : config_helpers.nestedAction,
        'choices' : { 'True', 'False' },
        'help' : 'Change process root directory on startup'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--chroot_dir' ],
      { 'dest' : 'server.chroot_dir',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : ( 'Directory to change process root directory to, defaults '
                   'to the home directory of the user the process runs as' )
      } ]
)
config_helpers.arg_list.append(
    [ [ '--user' ],
      { 'dest' : 'server.user',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'System user name to run as when daemonized'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--group' ],
      { 'dest' : 'server.group',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'System group name to run as when daemonized'
      } ]
)
config_helpers.arg_list.append(
    [ [ '--pid_file_path' ],
      { 'dest' : 'server.pid_file_path',
        'action' : config_helpers.nestedAction,
        'metavar' : '<string>',
        'help' : 'Filesystem path for daemon pid file'
      } ]
)

