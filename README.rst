TPRT - The Postman Rings Twice
==============================

Introduction
------------

TPRT provides a policy server for postfix that implements a greylisting policy.
See http://www.postfix.org/SMTPD_POLICY_README.html for protocol details.

There are many greylisting policy implementations, some of which implement
other useful policies as well.  The motivation for writing another is
personal: I was using postgrey.pl and felt that I could write cleaner, more
maintainable code, and I was looking for a medium-sized project to write in
Python.  If you find it useful as well, great.

Why TPRT as a name?  During initial development this project was called
newpostgrey...  I felt this code deserved its own name, and thought the
current one was appropriate and amusing.


Features
--------

- Greylisting with a dbm or redis database backend

- Configurable minimum time to pass greylisting, hostname and text to pass to
  the postfix server, additional SMTP header, maximum age (time between uses) of
  greylist entries, maxiumum age of unused greylist entries, interval between
  database maintenance passes, and default network masks

- In memory whitelists (read from files or redis databases).  Whitelisting
  based on sender IP network, or recipient email (but not ANDed
  combinations of these, yet).  Optional support for regular expressions to
  match sender or recipient email.  Whitelists can be re-read while the
  server is running

- Horizontal scaling through support for remote (redis) databases for 
  greylisting and whitelists, and the ability to disable database maintenance
  on all but one instance

- Logging to stdout, file, or syslog, or logging can be disabled entirely

- Support for running as a non-root user and for chroot'ing the process


Configuration
-------------

The software reads one or more JSON-formatted configuration files on startup.
Technically the configuration file is optional, as all of the configuration
parameters have defaults, but these defaults are geared towards local testing
from the command-line.  Also, some but not all of the configuration options
have corresponding command-line arguments.  This is intentional: the
command-line arguments are intended primarily for controlling how the service
is run, not how it does its work.  See the file examples.config for options.


Whitelists
----------

Lists of criteria for allowing an email without greylisting can be provided,
either via a redis database or as files in JSON format (dbm is not currently
supported).  Multiple sources may be used.  Emails can be whitelisted
based on remote server network (ie. the network that the IP of the MTA talking
to the local MTA is on) or the recipient email address.
Regular expressions may be used to match the recipient or the sender email,
but this is disabled by default.  The whitelists may be regenerated from the
sources while the server is running by sending a SIGHUP to the server.  It's
probably a good idea to do additional screening on whitelist entries provided
by users even if regex entries are not allowed: it would be easy to render the
greylisting policy ineffective with a few well-chosen entries.

The file examples.whitelist has a complete list of entry types as they would
appear in a file.  There is a tool (wl_importer.py) that can be used to
import a file into a redis dataase.


Todo
----

- Make this repo a proper Python package
- The documentation is poor, in particular the examples need to be added
- Refactoring, see below
- Testing ... neither unit nor formal end-to-end tests are implemented
- The name of the program should be defined in one place, not three
- Take another pass at reducing the number of command-line options, while
  maintaining those critical to use with supervisor systems
- Add validation of the redis initialization parameters
- Reconsider the use of the 'daemon' module, the original homegrown daemon
  code was cleaner and just needed a few additional features
- Evaluate the "something's wrong" responses, as some of them should cause the
  socket to be closed (and re-opened?)
- Provide tools to ease migration from postgrey to tprt
- Find a better way to generate command-line arguments and configuration
  parameters from the same data
- Improve type support for directly-injected configuration (via
  config_helpers.directConfig): lists and dicts would be useful
- Add configuration support for encrypted (TLS) connections to redis
- Add an accessor for the database connection in database object classes


Refactoring targets
-------------------

- tprtRequestHandler is way too long, despite the amount of code already
  moved into separate functions
- Perhaps split server and service code into separate modules, and pass
  around a 'config' object rather than having it as a global variable
- config_helpers.set_parameter() is kind of dumb, rethink it

