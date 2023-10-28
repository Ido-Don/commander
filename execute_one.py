import argparse

from device_executer import execute_script


def get_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--commands-file",
                            help="the file path for commands, default is 'commands.txt' under the current working "
                                 "directory",
                            default="commands.txt")
    arg_parser.add_argument("-o", "--output-file",
                            help="the file path for the commands output",
                            default="output.txt")
    arg_parser.add_argument("-d", "--device-file",
                            help="the connection parameters for the device (in json format)",
                            required=True)

    arg_parser.add_argument("-p", "--permission-level",
                            help="execute the commands in which permission level - user, enable or configure terminal",
                            default="enable", type=str)
    arguments = arg_parser.parse_args()
    command_file_path = arguments.commands_file
    output_file_path = arguments.output_file
    device_file_path = arguments.device_file
    permission_level = arguments.permission_level
    return command_file_path, device_file_path, output_file_path, permission_level


def main():
    command_file_path, device_file_path, output_file_path, permission_level = get_arguments()
    execute_script(command_file_path, device_file_path, output_file_path, permission_level)


if __name__ == '__main__':
    main()
