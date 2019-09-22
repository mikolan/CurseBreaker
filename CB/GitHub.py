import io
import os
import re
import shutil
import zipfile
import requests
from . import retry, HEADERS


class GitHubAddon:
    @retry()
    def __init__(self, url):
        matches = re.search('https://github.com/(?P<owner>.*)/(?P<repo>.*)', url)
        if matches is None:
            raise RuntimeError
        owner = matches.group('owner')
        repo = matches.group('repo')

        self.payload = requests.get(f'https://api.github.com/repos/{owner}/{repo}/releases/latest',
                                    headers=HEADERS).json()
        self.name = repo
        self.downloadUrl = self.payload['zipball_url']
        self.currentVersion = self.payload['tag_name']
        self.archive = None
        self.directories = []

    def get_current_version(self):
        self.currentVersion = self.payload['tag_name']

    @retry()
    def get_addon(self):
        self.archive = zipfile.ZipFile(io.BytesIO(requests.get(self.downloadUrl, headers=HEADERS).content))
        self.githubfoldername, tocfilename = next(p for p in self.archive.namelist() if p.endswith('toc')).split('/')
        self.realfoldername = tocfilename.split('.')[0]
        for file in self.archive.namelist():
            file = file.replace(self.githubfoldername, self.realfoldername)
            if '/' not in os.path.dirname(file):
                self.directories.append(os.path.dirname(file))
        self.directories = list(set(self.directories))

    def install(self, path):
        self.get_addon()
        self.archive.extractall(path)
        shutil.move(f'{path}/{self.githubfoldername}', f'{path}/{self.realfoldername}')
