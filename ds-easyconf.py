#!/usr/libexec/platform-python

# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2021 Marco Favero.
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---
#
# PYTHON_ARGCOMPLETE_OK

import os
import re
import sys
import getopt
import yaml
import distutils.spawn
import textwrap
import subprocess
import operator


def load_yaml(file, part):
    with open(file, 'r') as ymlfile:
        try:
            config_parameters = yaml.load(ymlfile, Loader=yaml.SafeLoader)[part]
        except KeyError:
            if part == 'INSTANCES':
                config_parameters = {}
            if part == 'FALSE_ERRORS':
                config_parameters = []
    return config_parameters


def uniqueize(string):
    return re.sub("\-\d+$", '', string, 1)


def compose_command(elements, myformat, cli, ldapserver='localhost',
                    previous_directive='', previous_previous_directive='', commands=[]):
    initial_cli = cli
    if not previous_directive and not previous_previous_directive:
        # We are at the first run. We clear the list of results, because it
        # survives among the calls, it  they don't initialize commands
        # explicitly.
        commands.clear()
    for directive in elements:
        if directive in ('DM', 'pwd', 'uri', 'ldapmodify'):
            continue
        if isinstance(elements[directive], dict):
            # repl-agmt management
            if previous_previous_directive == 'repl-agmt' and ldapserver != directive:
                continue
            if previous_previous_directive != 'repl-agmt':
                cli += "\0{}".format(uniqueize(directive))
            #
            compose_command(elements[directive], myformat, cli, ldapserver,
                            directive, previous_directive)
        elif isinstance(elements[directive], list):
            ''' Key with list values '''
            cli += "\0{}".format(uniqueize(directive))
            for attributes in elements[directive]:
                if isinstance(attributes, dict):
                    for attribute, value in attributes.items():
                        cli += applyFormat(uniqueize(previous_directive),
                                           uniqueize(directive), myformat,
                                           attribute, value, ldapserver)
                else:
                    cli += "\0--{}".format(attributes)
            # print(cli)
            commands.append(cli)
        else:
            if elements[directive] is None:
                ''' Key without value '''
                cli += "\0{}".format(uniqueize(directive))
            if elements[directive] is not None:
                ''' Key with single value '''
                cli += applyFormat(uniqueize(previous_directive), uniqueize(directive),
                                   myformat, uniqueize(directive), elements[directive])
            # print(cli)
            commands.append(cli)
        cli = initial_cli
    return commands


def applyFormat(parent, directive, myformat, attr, value, host='localhost'):
    '''
    parent is the parent directive conf.
    directive is the immediate key of conf.
    myformat is the dict format describing the
      parent/directive format to apply.
    attribute is the attribute name.
    value is the attribute value.
    host is the server hostname to configure.

    The arguments separator is the null char (\0).
    It will be useful to separate each argument into
    an array suitable for subprocess without shell.
    '''

    if attr == 'replica-id':
        if host not in value.keys() or not isinstance(value, dict):
            print("\n{}The config section <{}> doesn't match the host <{}>.\nPlease, fix this error.{}".
                  format(bcolors.FAIL, value,host, bcolors.ENDC))
            sys.exit(255)
        value = value[host]
    if parent in myformat and directive in myformat[parent]:
        return myformat[parent][directive].format(attr, value)
    else:
        '''A default format '''
        return "\0--{}={}".format(attr, value)


def wrapper(color, text):
    text = textwrap.fill(text,replace_whitespace=False,
                         break_long_words=False, break_on_hyphens=False)
    text = textwrap.indent(text, "\t")
    return "{}{}{}".format(color, text, '\033[0m')


def printout(subres,colors, noerrors):
    ret = False
    error = False
    warning = False
    msg = "[ {}KO{} ]".format(colors.FAIL, colors.ENDC)
    if subres.returncode != 0:
        error = True
        for noerr in noerrors:
            if re.search(noerr, subres.stdout):
                ret = True
                error = False
                warning = True
                break
    else:
        msg = "[ {}OK{} ]".format(colors.OKGREEN, colors.ENDC)
        ret = True
    print(msg, end=' ')
    print(wrapper(colors.NOTICE, ' '.join(subres.args)))
    if subres.returncode != 0:
        if error:
            print(wrapper(bcolors.FAIL,'ERROR executing this action'))
        if subres.stdout:
            print(wrapper(bcolors.BOLD, subres.stdout))
        if subres.stderr:
            print(wrapper(bcolors.FAIL,subres.stderr))
        print()
        return ret, error, warning
    print(wrapper(bcolors.OKCYAN, subres.stdout), end="\n\n")
    return ret, error, warning


def execute_commands(commands, colors, noerrors=[]):
    ''' Iterate over array of commands to execute '''
    errors = 0
    warnings = 0
    for command in commands:
        arg=command.split("\0")
        type= arg[0]
        result = subprocess.run(arg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        success, returned_error, returned_warn = printout(result, colors, noerrors)
        if not success:
            if returned_error:
                errors += 1
        if returned_warn:
            warnings += 1
    if errors or warnings:
        print(wrapper(colors.FAIL,"PAY ATTENTION: {} errors and {} warnings detected during the configuration of instance <{}> using <{}>, see above.".format(errors, warnings, instance, type)), end="\n\n")
    return errors, warnings

class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKCYAN = '\033[96m'
  OKGREEN = '\033[92m'
  NOTICE = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


# get argv
argv = sys.argv[1:]
installInst = []
dirserver = None
config_file = 'ds-easyconf.yaml'
usage = 'Usage: {} -h <dirsrvhostname> [-c <conf>] [-i <instance> [-i <instance2>] ...] [--help]'.format(sys.argv[0])
try:
    opts, args = getopt.getopt(argv,"h:i:c:",["help"])
except getopt.GetoptError:
    print (usage)
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        dirserver = arg
    elif opt == '-i':
        installInst.append(arg)
    elif opt == '-c':
        config_file = arg
    elif opt == '--help':
        print (usage)
        sys.exit(0)
    else:
        print (usage)
        sys.exit(2)

if args:
    print('Unhadled arguments!')
    print (usage)
    sys.exit(2)

if dirserver is None:
    print('Missing server parameter (-h).')
    print (usage)
    sys.exit(2)

# get the config from FHS conform dir
CONFIG = os.path.join(os.path.dirname("/etc/ds-easyconf/"), config_file)
if not os.path.isfile(CONFIG):
    # developing stage
    CONFIG = os.path.join(os.path.dirname(__file__), config_file)

if not os.path.isfile(CONFIG):
    # Try to copy dist file in first config file
    distconf = os.path.join(os.path.dirname(CONFIG), "{}.dist".format(config_file))
    if os.path.isfile(distconf):
        print("First run? I don't find <{}>, but <{}.dist> exists. I try to rename it.".format(config_file, config_file))
        os.rename(distconf, os.path.join(os.path.dirname(distconf), config_file))

if os.path.isfile(CONFIG):
    INSTANCES = load_yaml(CONFIG, "INSTANCES")
    false_errors = load_yaml(CONFIG, "FALSE_ERRORS")
else:
    print ("I can't find the config file <{}>.\n".format(config_file))
    sys.exit(2)
skipped_instances = set()
dirpath = os.path.dirname(CONFIG)
if not dirpath:
    dirpath = '.'

# command specific constructor
dsformat={
    'config': {
        'replace': "\0{}={}",
        'add': "\0{}={}",
        'delete': "\0{}={}"
    },
}


dsconfInit = distutils.spawn.find_executable('dsconf')
ldapmodifyInit = distutils.spawn.find_executable('ldapmodify')
if dsconfInit is None:
    print("{}dsconf command not found.{}".format(bcolors.FAIL,bcolors.ENDC))
    sys.exit(1)
if ldapmodifyInit is None:
    print("{}ldapmodify command not found.{}".format(bcolors.FAIL,bcolors.ENDC))
    sys.exit(1)

exit = 0
configured_instances = []
for instance in INSTANCES:
    ldapmod_commands = []
    dsconf_commands = []
    if installInst:
        if instance not in installInst:
            print ("{}Skipping instance <{}> as per command line arguments.{}".format(bcolors.NOTICE, instance, bcolors.ENDC))
            continue
    if dirserver  not in INSTANCES[instance]['uri'].keys():
        print ("{}<{}> is not a server allowed in this instance. Skipped.{}".format(bcolors.FAIL,dirserver, bcolors.ENDC))
        skipped_instances.add(instance)
        continue
    print ("{}Configuring instance {} on {}{}".format(bcolors.HEADER, instance,dirserver, bcolors.ENDC))
    dirserver_port = INSTANCES[instance]['uri'][dirserver]
    bindDN = INSTANCES[instance]['DM']
    bindPWD = INSTANCES[instance]['pwd']
    URI = 'ldap://{}:{}'.format(dirserver,dirserver_port)
    dsconf = "{}\0-D\0{}\0-w\0{}\0{}".format(dsconfInit, bindDN, bindPWD, URI)
    ldapmodify = "{}\0-D\0{}\0-w\0{}\0-p\0{}\0-vvv\0-h\0{}".format(ldapmodifyInit, bindDN, bindPWD, dirserver_port, dirserver)
    # parse config
    #  dsconf commands
    dsconf_commands = compose_command(INSTANCES[instance], dsformat, dsconf, dirserver)
    # ldapmodify commands
    if 'ldapmodify' in INSTANCES[instance]:
        if isinstance(INSTANCES[instance]['ldapmodify'], list):
            for attribute in INSTANCES[instance]['ldapmodify']:
                if isinstance(attribute, dict):
                    for param, value in attribute.items():
                        param = uniqueize(param)
                        if param == 'f':
                            if not os.path.isabs(value):
                                value =  "{}/{}".format(dirpath,value)
                        ldapmod_commands.append("{}\0-{}\0{}".format(ldapmodify, param, value))
    # Execute commands
    #  dsconf commands
    errors, warnings = execute_commands(dsconf_commands, bcolors, false_errors)
    #  ldamodify commands
    errors, warnings = tuple(map(operator.add, (errors, warnings), execute_commands(ldapmod_commands, bcolors, false_errors)))
    print("{}End of work on {}{}".format(bcolors.BOLD, instance, bcolors.ENDC), end="\n\n")
    exit += errors
    configured_instances.append({'name': instance, 'errors': errors, 'warnings': warnings})
    del dsconf_commands
    del ldapmod_commands

if configured_instances:
    print("\nWe have configured the following instances:")
    for instance in configured_instances:
        print("\t{}\tErrors: {}\tWarnings: {}".format(instance['name'], instance['errors'], instance['warnings']))
print ("\n{} instances configured.".format(len(configured_instances)))

if exit == 0:
    print("\n{}Process ended with success!{}\n".format(bcolors.BOLD, bcolors.ENDC))
else:
    print("\n{}Process ended with {} errors{}\n".format(bcolors.BOLD, exit, bcolors.ENDC))
sys.exit(exit)
