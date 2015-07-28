import os
import re
import webbrowser
import sublime
import sublime_plugin
import threading

ST3 = int(sublime.version()) > 3000

if ST3:
    from . import git_info
    from . import git_info_async
else:
    import git_info
    import git_info_async

# Backwards compatibility
try:
    import commands as cmd
except:
    import subprocess as cmd


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

class GitInfo():
    def __init__(self, user, repo, branch, remote_path, remote_name):
        self.user = user
        self.repo = repo
        self.branch = branch
        self.remote_path = remote_path
        self.remote_name = remote_name

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

class GitlinkCommand(sublime_plugin.TextCommand):
    def copy_to_clipboard(self, git_info):
        user = git_info.user
        repo = git_info.repo
        branch = git_info.branch
        remote_path = git_info.remote_path
        remote_name = git_info.remote_name
        remote = REMOTE_CONFIG[remote_name]

        # Build the URL
        if remote_name != 'codebasehq':
            url = remote['url'].format(user, repo, branch, remote_path, self.filename)
        else:
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

