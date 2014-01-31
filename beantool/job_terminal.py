import re
#import readline

from collections import OrderedDict
from pprint import pprint

from beanstalkc import DEFAULT_PRIORITY

_command_map = OrderedDict()
_command_map['stats'] = ('command_stats', (), 'Display job information')
_command_map['delete'] = ('command_delete', (), 'Delete job')
_command_map['release'] = ('command_release', 
                           ('priority', 'delay'),
                           'Release job back to queue')

_command_map['bury'] = ('command_bury', 
                        ('priority',), 
                        'Bury job')

_command_map['touch'] = ('command_touch', (), 'Re-lease job')
_command_map['body'] = ('command_body', (), 'Show job data')
_command_map['help'] = ('command_help', (), 'Display help')
_command_map['quit'] = ('command_quit', (), 'Quit')

# Set-up command-completion.

#def complete(text, state):
#    print("COMPLETING")
#
#    for command in _command_map.keys:
#        if command.startswith(text):
#            if not state:
#                return command
#            else:
#                state -= 1
#
#readline.parse_and_bind('tab: complete')
#readline.set_completer(complete)


class JobTerminal(object):
    def __init__(self, beanstalk, job):
        self.__b = beanstalk
        self.__j = job
        self.__is_looping = True
        self.__is_deleted = False

    def __display_help(self):
        print('')
        print("# Commands:")
        print("#")

        for command, command_info in _command_map.iteritems():
            (handler, params, description) = command_info
            if len(params) > 0:
                param_phrase =  '[' + '] ['.join(params) + ']'
            else:
                param_phrase = ''

            print("# %10s %-20s %s" % 
                  (command, param_phrase, description))

        print('')

    def __display_error(self, message):
        print("ERROR: %s\n" % (message))

    def run_loop(self):
        print('Job Terminal')
        print('============')
        print('')
        print("Job with ID (%d) has been reserved. You may manipulate it, "
              "here." % 
              (self.__j.jid))

        self.__display_help()

        while self.__is_looping is True:
            try:
                raw = raw_input('-> ').strip()
                if raw == '' or raw[0] == '#':
                    continue

                matched = re.match('([a-z]+)(.*)', raw)
                if matched is None:
                    self.__display_error("Command-line doesn't look right.")
                    continue

                (command, params) = matched.group(1, 2)

                if command not in _command_map:
                    self.__display_error("Command not valid: %s" % (command))

                params = params.strip()
                if params != '':
                    params = re.split(' +', params)
                else:
                    params = []

                handler_name = _command_map[command][0]

                try:
                    getattr(self, handler_name)(*params)
                except Exception as e:
                    self.__display_error('[' + e.__class__.__name__ + '] ' + str(e))
                    raise
            except KeyboardInterrupt:
                print('')
                self.__is_looping = False

        if self.__is_deleted is True:
            print("Job terminal stopped.")
        else:
            print("Job terminal stopped. Job will be released back to the queue.")

    def command_stats(self):
        s = self.__j.stats()

        pprint(s)
        print('')

    def command_delete(self):
        self.__j.delete()

        self.__is_looping = False
        self.__is_deleted = True

        print("Job deleted.")

    def command_release(self, priority=None, delay=0):
        if priority is not None:
            priority = int(priority)
        
        if delay is not None:
            delay = int(delay)

        self.__j.release(priority, delay)

        self.__is_looping = False
        print("Job released.")

    def command_bury(self, priority=None):
        if priority is not None:
            priority = int(priority)

        self.__j.bury(priority)

        self.__is_looping = False
        print("Job buried.")

    def command_touch(self):
        self.__j.touch()

        print("Job touched.\n")

    def command_body(self):
        print(self.__j.body)
        print('')

    def command_help(self):
        self.__display_help()

    def command_quit(self):
        self.__is_looping = False