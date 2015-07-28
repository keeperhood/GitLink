import os
import re
import webbrowser
import sublime
import sublime_plugin
import threading

class GitInfoAsync(threading.Thread):
    def __init__(self, path, callback):
        self.callback = callback
        self.path = path
        threading.Thread.__init__(self)

    def get_git_binary_path(self):
        settings = sublime.load_settings('GitLink.sublime-settings')
        return settings.get("git_path")

    def prepare_git_command(self, command):
        git_path = self.get_git_binary_path()
        return "{git_path}/git {command}".format(**locals())

    def get_git_info(self):
        # Find the repo
        git_config_path = cmd.getoutput(self.prepare_git_command("remote show origin"))

        p = re.compile(r"(.+@)*([\w\d\.]+):(.*)")
        parts = p.findall(git_config_path)
        site_name = parts[0][1]  # github.com or bitbucket.org, whatever

        remote_name = 'github'
        if 'bitbucket' in site_name:
            remote_name = 'bitbucket'
        if 'codebasehq.com' in site_name:
            remote_name = 'codebasehq'

        git_config = parts[0][2]

        # Get username and repository
        if remote_name != 'codebasehq':
            user, repo = git_config.replace(".git", "").split("/")
        else:
           user, project, repo = git_config.replace(".git", "").split("/")

        # Find top level repo in current dir structure
        folder = cmd.getoutput(self.prepare_git_command("rev-parse --show-toplevel"))
        basename = os.path.basename(folder)
        remote_path = self.path.split(basename, 1)[1]

        # Find the current branch
        branch = cmd.getoutput(self.prepare_git_command("rev-parse --abbrev-ref HEAD"))

        return GitInfo(user, repo, branch, remote_path, remote_name)

    def run(self):
        git_info = self.get_git_info()
        self.callback(git_info)