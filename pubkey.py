#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import argparse
import commands
import threading
import sys
import os
from subprocess import Popen, PIPE
from functools import partial
import time

__author__ = "yuki2006 <yagfair@gmail.com>"
__status__ = "production"
__version__ = "1.0"
__date__ = "12 Dec 2015"

SSH_COPY_ID = "ssh-copy-id"
# ref http://raimon49.github.io/2015/08/07/python-puts-color-sequence-with-functools.html

def print_colored(code, text, is_bold=False):
    if is_bold:
        code = '1;%s' % code

    sys.stderr.write('\033[%sm%s\033[0m' % (code, text))


print_green = partial(print_colored, '32')


class ShellThread(threading.Thread):
    """
    コマンド実行し、stdout,stderr,wait 監視用クラス
    """

    class ForStdErr(threading.Thread):
        """
        stderr監視用クラス
        """

        def __init__(self, parent):
            super(ShellThread.ForStdErr, self).__init__()
            self.parent = parent

        def run(self):
            """
            起動したプロセスの標準エラー出力が切れるまでループします。
            """
            while 1:
                c = self.parent.p.stderr.read(1)
                if not c:
                    break
                sys.stderr.write(c)
                sys.stderr.flush()

    class StdPipe(threading.Thread):
        """
        標準入力接続用クラス
        """

        def __init__(self, parent):
            super(ShellThread.StdPipe, self).__init__()
            self.parent = parent

        def run(self):
            """
             pythonプロセスと起動したプロセスの標準入力をつなぎます。
             """

            while self.parent.p.returncode is None:
                # non blockingの標準入力を使用
                # blockingだと標準入力をつかんだままになる
                bytes = sys.stdin.read(1)
                if len(bytes) > 0:
                    self.parent.p.stdin.write(str(bytes) + "\n")
                    self.parent.p.stdin.flush()
                time.sleep(1)

    def __init__(self, cmd):
        super(ShellThread, self).__init__()
        self.p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False, close_fds=True)
        self.std_err_thread = self.ForStdErr(self)
        self.std_pipe = self.StdPipe(self)

        self.std_err_thread.start()
        self.std_pipe.start()

    def run(self):
        """
        起動したプロセスの標準出力が切れるまでループします。
        """

        while 1:
            c = self.p.stdout.read(1)
            if not c:
                return
            sys.stdout.write(c)
            sys.stdout.flush()

    def process_loop(self):
        """
        プロセスが終了するまでループします。
        """
        self.p.wait()
        self.std_err_thread.join(1)
        self.std_pipe.join(1)

        if self.p.returncode != 0:
            # プロセスが実行エラー
            exit(self.p.returncode)


def run_remote_command(cmd):
    """
    コマンド実行用の関数です
    :param cmd: 実行するコマンド
    :return: 実行のステータスコード
    """
    print_green(cmd + "\n")

    status, txt = commands.getstatusoutput(cmd)
    sys.stderr.write(txt)
    return status


def check_builtin_ssh_copy_id():
    # ssh_copy_idのコマンドが存在するならそちらを呼び出す。
    sts, _ = commands.getstatusoutput("type %s" % SSH_COPY_ID)
    return sts / 256 == 0


def my_ssh_copy_id_cmd(SSH_KEY_PATH, public_key_name, server):
    sub_cmd = \
        ["chmod 600 ~/.ssh/authorized_keys",
         "chmod 700 ~/.ssh/",
         "chmod 755 ~/"]

    cmd = "cat %s| ssh %s \"mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && " % \
          (SSH_KEY_PATH + public_key_name, server) + " && ".join(sub_cmd) + "\""
    return cmd


def core(server, SSH_KEY_PATH, private_key_name, public_key_name, args):
    """
        メインの処理関数です。
    :param server: 対象のWebサーバー
    :param SSH_KEY_PATH: ローカルのSSHディレクトリパス
    :param private_key_name: プライベートキーのファイル名
    :param public_key_name: 公開鍵ファイル名
    :param args: argparse のオブジェクト
    :return:
    """
    if args.keygen:

        cmd = ["ssh-keygen", "-t", "rsa", "-f", SSH_KEY_PATH + private_key_name]

        if args.N is not None:
            cmd.append("-N")
            cmd.append(args.N)
        print_green(" ".join(cmd) + "\n")
        shell = ShellThread(cmd)
        shell.start()
        # ssh-keygenのプロセスが終了するまでループ
        shell.process_loop()
        # Thread終了
        shell.join()

    if not args.LocalOnly:
        # cmd = "scp  %s:~/.ssh/" % (SSH_KEY_PATH + public_key_name, server)
        # run_remote_command(cmd)
        if check_builtin_ssh_copy_id():
            sts = run_remote_command("%s -i %s %s" % (SSH_COPY_ID, SSH_KEY_PATH + public_key_name, server))
        else:
            cmd = my_ssh_copy_id_cmd(SSH_KEY_PATH, public_key_name, server)
            sts = run_remote_command(cmd)
        if sts != 0:
            exit(sts)

    if args.config:
        config_data = gen_config_data(SSH_KEY_PATH + private_key_name, args.alias, server)

        file = SSH_KEY_PATH + "config"
        fp = open(file, "a+")
        fp.write(config_data)
        fp.close()
        print_green("saved %s\n" % file)
        sys.stderr.write(config_data)


def gen_config_data(identity_file, alias, server):
    user, target_server = server.split("@")

    if len(alias) == 0:
        alias = target_server

    config_data = "Host %s\n" % alias
    config_data += "\thostname %s\n" % target_server
    config_data += "\tUser %s\n" % user
    config_data += "\tIdentityFile %s\n" % identity_file
    config_data += "\n"
    return config_data


def get_key_path(ssh_key_path, private):
    if "/" in private:
        splits = private.split("/")
        ssh_key_path = "/".join(splits[:-1]) + "/"
        private_key_name = splits[-1]
    else:
        private_key_name = private  # "id_rsa.pub"

    public_key_name = private_key_name + ".pub"

    return ssh_key_path, private_key_name, public_key_name


if __name__ == '__main__':
    desc = 'ver %s 面倒なコマンドを自動で実行してくれる公開鍵認証するツールです。' % __version__
    ssh_key_path = os.environ['HOME'] + "/.ssh/"

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('server', metavar='server', type=str,
                        help='user@server')
    parser.add_argument('-l', "--LocalOnly", action='store_true', default=False,
                        help="オプションをつけると、サーバー上の操作を行いません。")

    parser.add_argument('-p', "--private", metavar='PrivateKeyPath', default=ssh_key_path + "id_rsa", type=str,
                        help="private key のパスです [default " + ssh_key_path + "id_rsa" + "]")

    parser.add_argument("-k", "--keygen", action='store_true', default=False, help="keygenで鍵を生成します")

    parser.add_argument('-c', "--config", action='store_true', default=False,
                        help=".ssh/config にHost情報を書き込みます")

    parser.add_argument('-a', "--alias", type=str, default="",
                        help="-cオプションをつけた時のみ有効, configファイルの Host欄をこの指定にします")

    parser.add_argument('-N', metavar='PassPhrase', type=str,
                        help="パスフレーズを指定します。空文字も可能です。(-k オプション時に有効です）")

    args = parser.parse_args()

    server = args.server  # taro@abc.com

    ssh_key_path, private_key_name, public_key_name = get_key_path(ssh_key_path, args.private)

    sys.stderr.write("server = " + server + "\n")
    sys.stderr.write("private_key = " + ssh_key_path + private_key_name + "\n")
    sys.stderr.write("public_key = " + ssh_key_path + public_key_name + "\n")
    sys.stderr.write("keygen = " + str(args.keygen) + "\n")
    sys.stderr.write("only local = " + str(args.LocalOnly) + "\n")
    sys.stderr.write("config = " + str(args.config) + "\n")

    core(server, ssh_key_path, private_key_name, public_key_name, args)
