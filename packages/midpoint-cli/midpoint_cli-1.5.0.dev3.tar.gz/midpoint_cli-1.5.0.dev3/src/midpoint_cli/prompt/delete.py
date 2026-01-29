import shlex
from argparse import ArgumentParser, RawTextHelpFormatter

from midpoint_cli.client import MidpointObjectTypes
from midpoint_cli.client.objects import MidpointTypeNotFound
from midpoint_cli.prompt.base import PromptBase
from midpoint_cli.prompt.console import print_error

delete_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter, prog='delete', description='Delete a server object.', epilog=''
)
delete_parser.add_argument('objectclass', help='Type of the object to delete (Java Type).')
delete_parser.add_argument('oid', help='Object ID.')


class DeleteClientPrompt(PromptBase):
    def do_rm(self, inp):
        self.do_delete(inp)

    def do_del(self, inp):
        self.do_delete(inp)

    def do_delete(self, inp):
        try:
            delete_args = shlex.split(inp)
            ns = delete_parser.parse_args(delete_args)

            # Resolve the type string to a MidpointObjectType
            midpoint_type = MidpointObjectTypes.find_by_name(ns.objectclass)
            self.client.delete(midpoint_type, ns.oid)

        except MidpointTypeNotFound as e:
            print_error(str(e))
        except AttributeError as e:
            print_error(str(e))
        except SystemExit:
            pass

    def help_delete(self):
        delete_parser.print_help()

    def help_rm(self):
        delete_parser.print_help()

    def help_del(self):
        delete_parser.print_help()
