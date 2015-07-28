import os
import re
import webbrowser
import sublime
import sublime_plugin
import threading

from .git_info import GitInfo
from .git_info_async import GitInfoAsync

REMOTE_CONFIG = {
    'github': {
        'url': 'https://github.com/{0}/{1}/blob/{2}{3}/{4}',
        'line_param': '#L'
    },
    'bitbucket': {
        'url': 'https://bitbucket.org/{0}/{1}/src/{2}{3}/{4}',
        'line_param': '#cl-'
    },
    'codebasehq': {
        'url': 'https://{0}.codebasehq.com/projects/{1}/repositories/{2}/blob/{3}{4}/{5}',
        'line_param': '#L'
    }
}

class GitlinkCommand(sublime_plugin.TextCommand):
    def copy_to_clipboard(self, git_info):
        user = git_info.user
        repo = git_info.repo
        branch = git_info.branch
        remote_path = git_info.remote_path
        remote_name = git_info.remote_name
        commit = git_info.commit
        remote = REMOTE_CONFIG[remote_name]

        # Build the URL
        if remote_name == 'github':
            url = remote['url'].format(user, repo, branch, remote_path, self.filename)
        elif remote_name == 'bitbucket':
            url = remote['url'].format(user, repo, commit, remote_path, self.filename)
        elif remote_name == 'codebasehq':
            url = remote['url'].format(user, project, repo, branch, remote_path, self.filename)

        if(self.line):
            row = self.view.rowcol(self.view.sel()[0].begin())[0] + 1
            url += "{0}{1}".format(remote['line_param'], row)

        if(self.web):
            webbrowser.open_new_tab(url)
        else:
            os.system("echo '%s' | pbcopy" % url)
            sublime.status_message('GIT url has been copied to clipboard')

    def run(self, edit, **args):
        # Current file path & filename
        self.path, self.filename = os.path.split(self.view.file_name())
        self.line = args['line']
        self.web = args['web']

        # Switch to cwd of file
        os.chdir(self.path + "/")

        thread = GitInfoAsync(self.path, self.copy_to_clipboard)
        thread.start()

