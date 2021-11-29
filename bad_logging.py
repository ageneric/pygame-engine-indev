"""A method to write logs to a file, for debugging purposes."""

from time import time

print_logging = False

class Log:
    def __init__(self, log_directory, initial_message=None):
        self.log_directory = log_directory
        self.last_message = ''
        self.repeats = False

        with open(self.log_directory, 'w') as f:
            f.write(initial_message)
            self.last_message = initial_message

    def log(self, *args):
        message = '; '.join(map(str, args))
        if print_logging and not self.repeats:
            print(message)

        if message == self.last_message:
            if not self.repeats:
                with open(self.log_directory, 'a') as f:
                    f.write(' [... repeat]')
                self.repeats = True
        else:
            with open(self.log_directory, 'a') as f:
                f.write('\n' + str(message))
            self.last_message = message
            self.repeats = False


dlog = Log('_engine_log.txt', f'Start: at {time()}')  # debugging log
