"""
Argument parsing and configuration functions to be used by programs
"""

# Logging is not used here because most functions will be run before logging
# is set up


import argparse
import json
import re


# defaults that should be overridden after import
program_version = '0.0.0'
default_config_file = '/etc/program.conf'
program_name = 'program'
program_description = 'Program'


# holds the collected program arguments to pass to argparse
# programs using this module should add to this
arg_list = []


class nestedAction(argparse.Action):
    """
    Custom argparse action that allows for sub-namespaces
    Uses '.' to separate levels by default
    """
    def __call__(self, parser, namespace, values, option_string=None,
      separator='.'):
        levels = list(self.dest.split(separator))
        dest = levels.pop()
        last_level = namespace
        for level in levels: 
            next_level = getattr(last_level, level, argparse.Namespace())
            setattr(last_level, level, next_level)
            last_level = next_level
        setattr(last_level, dest, values)


class directConfig(argparse.Action):
    """
    Custom argparse action that parses the argument value to place
    settings anywhere in the resulting (nested) namespace
    Format is <key>=<data>, where <key> is something like 'server.setting'
    and <data> is [:<type>:]value, <type> defaults to string
    Uses '.' to separate levels of the namespace by default
    """
    def __call__(self, parser, namespace, values, option_string=None,
      separator='.'):
        try:
            place,content = values.split('=')
            match = re.search('^:(.+):(.+)', content)
            # seems like there should be a standard way to do this
            if match:
                data_type = match.group(1)
                types = [ 'bool', 'int', 'float', 'complex', 'bytes' ]
                if data_type in types:
                    data = getattr(__builtins__, data_type)(match.group(2))
                else:
                    raise ValueError
            else:
                data = content
            levels = list(place.split(separator))
            dest = levels.pop()
            last_level = namespace
            for level in levels: 
                next_level = getattr(last_level, level, argparse.Namespace())
                setattr(last_level, level, next_level)
                last_level = next_level
            setattr(last_level, dest, data)
        except:
            # if one of the splits failed, we don't need the data
            pass


def collect_arguments(config):
    """
    Parse arguments and set global config
    This also handles 'respond and exit' arguments
    """
    def _recursive_vars(ns):
        """Apply vars() recursively to nested namespaces"""
        vars_this_level = vars(ns)
        for var in vars_this_level.keys():
            # big assumption about types here
            if type(vars_this_level[var]) == type(ns):
                vars_this_level[var] = _recursive_vars(vars_this_level[var])
        return vars_this_level

    arg_parser = argparse.ArgumentParser(prog=program_name,
        description=program_description,
        argument_default=argparse.SUPPRESS)
    for arg in arg_list:
        # fix up program version since arg_list is built at module-import time
        if arg[1]['action'] == 'version':
            arg[1]['version'] = "%%(prog)s version %s" % program_version
        arg_parser.add_argument(*arg[0], **arg[1])
    config['from_arguments'] = _recursive_vars(arg_parser.parse_args())


# arguments handled by collect_arguments()
# version string here is superceded by collect_arguments()
arg_list.append(
    [ [ '--version', '-v' ],
      { 'action' : 'version',
        'version' : 'PROGRAM version VERSION'
      } ]
)
# No better place for this
arg_list.append(
    [ [ '--inject', '-i' ],
      { 'metavar' : '<key>=<data>',
        'action' : directConfig,
        'help' : 'Inject configuration directly, see documentation'
      } ] 
)


def read_config(config):
    """
    Read in configuration files
    Files are expected to be in standard JSON format (see documentation)
    """
    files_to_read = ( config['from_arguments'].get('config_files') or
        [ default_config_file ] )
    data = {}
    for file in files_to_read:
        try:
            with open(file, mode='r') as f:
                data_from_file = json.load(f)
                # consider a dict, or list containing a single dict, valid
                if type(data_from_file) == dict:
                    data.update(data_from_file)
                elif type(data_from_file) == list:
                    if type(data_from_file[0]) == dict:
                        data.update(data_from_file[0])
                else:
                    raise json.JSONDecodeError
        except OSError as err:
            print("got OSError %s on %s" % (err.strerror, err.filename))
        except json.JSONDecodeError:
            print("got JSONDecodeError")
    config['from_files'] = data

# arguments handled by read_config
arg_list.append(
    [ [ '--configfile', '-c' ],
      { 'dest' : 'config_files',
        'metavar' : '<file>',
        'action' : 'append',
        'help' : ( 'Configuration file to read.  May be specified multiple '
                   'times, files will be read in the order specified' )
      } ] 
)


def set_parameter(config, param_section, param_name, param_default):
    """
    Set the value of a configuration parameter from arguments, configuration
    files, or a default, in that order
    """
    try:
        value_from_args = config['from_arguments'][param_section][param_name]
    except:
        value_from_args = None
    try:
        value_from_files = config['from_files'][param_section][param_name]
    except:
        value_from_files = None
    if value_from_args is not None:
        param_value = value_from_args
    elif value_from_files is not None:
        param_value = value_from_files
    else:
        param_value = param_default
    config[param_section][param_name] = param_value


