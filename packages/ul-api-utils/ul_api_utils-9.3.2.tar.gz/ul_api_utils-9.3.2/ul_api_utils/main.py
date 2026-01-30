import os
import sys

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ul_api_utils.commands.cmd_worker_start import CmdWorkerStart
from ul_py_tool.commands.cmd import Cmd
from ul_api_utils.commands.cmd_enc_keys import CmdEncKeys
from ul_api_utils.commands.cmd_gen_new_api_user import CmdGenerateNewApiUser
from ul_api_utils.commands.cmd_gen_api_user_token import CmdGenerateApiUserToken
from ul_api_utils.commands.cmd_generate_api_docs import CmdGenApiFunctionDocumentation

from ul_api_utils.commands.cmd_start import CmdStart


def main() -> None:
    Cmd.main({
        'start': CmdStart,
        'enc_keys': CmdEncKeys,
        'start_worker': CmdWorkerStart,
        'gen_new_api_user': CmdGenerateNewApiUser,
        'gen_api_user_token': CmdGenerateApiUserToken,
        'gen_api_docs': CmdGenApiFunctionDocumentation,
    })


if __name__ == '__main__':
    main()
