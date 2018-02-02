#!/usr/bin/env python
# encoding=utf-8
"""
Jenkins Job Builder do not work on Jenkins2 due to Jenkins2's enhanced security feature
This is just a temp fix script that would work with Jenkins2 (at least in my environment)
"""
import sys
import os
import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import requests
import yaml

@contextlib.contextmanager
def stdout_redirect():
    """this is hacking, but it's the most easiest way to
    get XML without even need to read any source code
    """

    stdout = sys.stdout
    my_stdout = StringIO()
    sys.stdout = my_stdout
    yield my_stdout
    sys.stdout = stdout
    my_stdout.close()


def from_jenkins_job(yaml_file, config=None):
    """calling jenkins-job to get things we need
    use jenkins-job to parse YAML into XML for Jenkins
    also read jenkins-job configuration (jenkins url, user, password)

    :param yaml_file: filename of YAML file that Jenkins-Job can parse into XML
    :type yaml_file: str
    :returns str, str
    """
    if config:
        args = ['--conf', config, 'test', yaml_file]
    else:
        args = ['test', yaml_file]
    with stdout_redirect() as my_stdout:
        from jenkins_jobs.cli import entry
        jenkins_job = entry.JenkinsJobs(args)
        jenkins_job.execute()
        configuration = jenkins_job.jjb_config.jenkins.copy()
        job_xml = my_stdout.getvalue()
    return job_xml, configuration


def jenkins_folder_xml():
    """XML used to create folder on Jenkins.
    for now just hardcode the XML.

    :return str
    """

    return """<?xml version="1.0" encoding="utf-8"?>
        <com.cloudbees.hudson.plugins.folder.Folder plugin="cloudbees-folder">
        <actions/>
        <icon class="com.cloudbees.hudson.plugins.folder.icons.StockFolderIcon"/>
        <views/>
        <viewsTabBar class="hudson.views.DefaultViewsTabBar"/>
        <primaryView>All</primaryView>
        <healthMetrics/>
        <actions/>
        <description>created by Jenkins2-job</description>
        <keepDependencies>false</keepDependencies>
        <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
        <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
        <concurrentBuild>false</concurrentBuild>
        <canRoam>true</canRoam>
        <properties/>
        <scm class="hudson.scm.NullSCM"/>
        <publishers/>
        <buildWrappers/>
        </com.cloudbees.hudson.plugins.folder.Folder>
        """

def build_jenkins_url(url, path):
    """Jenkins path are named: {name}/job/config.xml or {name}/job/{name}/config.xml
    Need it to figure out if project folder already exist

    :param url: URL for Jenkins server
    :param path: path of the job

    :type url: str
    :type path: str

    :return generator
    """

    def split(path):
        parent, base = os.path.split(path)
        if parent:
            yield parent
            for p in split(parent):
                yield p
    yield os.path.join(url, 'job', '/job/'.join(path.split('/')),'config.xml')
    for p in split(path):
        yield os.path.join(url, 'job', '/job/'.join(p.split('/')), 'config.xml')
    yield os.path.join(url, 'config.xml')


def find_jenkins_job_path(yaml_file):
    """find jenkins job path from YAML file
    currently looking for job['name'] field

    :param yaml_file: the content of yaml file
    :type yaml_file: str

    :return str
    """

    data = yaml.load(open(yaml_file))
    for line in data:
        if not 'job' in line:
            continue
        if not 'name' in line['job']:
            continue
        return line['job']['name']

def update_url_2_create_url(url):
    """convert url used for update to
    url used for create
    update:
        HTTP(S)://HOSTNAME/path/job/{Item_Name}/config.xml
    create:
        HTTP(S)://HOSTNAME/path/createItem?name={Item_Name}

    :param url: HTTP URL
    :type url: str

    :return str
    """

    for _ in range(2):
        url, name = os.path.split(url)
    return os.path.join(os.path.split(url)[0], 'createItem?name={}'.format(name))

class Jenkins2Jobs(object):
    """Help(hack) to get jobs to Jenkins
    """
    def __init__(self, username, password):
        """prepare the HTTP(s) connection by create requests.Session()
        suggest to use API key for password.
        you can find API key:
            by visit URL "/me/configure" from browser on your Jenkins instance after login

        :param username: username
        :param password: Jenkins password or API KEY

        :return None
        """

        self.session = requests.Session()
        self.session.auth = (username, password)
        self._username_ = username
        self._password_ = password
        self._response_ = None

    def query_job(self, url):
        """HTTP GET url and return query result content back
        raise error: requests.exceptions.HTTPError
        the raw requests.response object will save on self._response_
        return status_code, response.text

        :param url: jenkins url for HTTP GET
        :type url: str

        :return int, str
        """

        self._response_ = None
        response = self.session.get(url)
        self._response_ = response
        response.raise_for_status()
        return response.status_code, response.text

    def create_job(self, url, xml):
        """HTTP POST url with xml as body
        this post will create new job on Jenkins
        raise error: requests.exceptions.HTTPError
        the raw requests.response object will save on self._response_
        return status_code, response.text

        create job:
            HTTP(S)://HOSTNAME/path/createItem?name={Item_Name}
        update job:
            HTTP(S)://HOSTNAME/path/job/{Item_Name}/config.xml

        Since Jenkins use POST for both create and update, so this method is also used for both

        :param url: jenkins url for HTTP POST
        :param xml: XML post to Jenkins

        :return int, str

        """

        self._response_ = None
        response = self.session.post(url, data=xml, headers={'Content-Type': 'text/xml'})
        self._response_ = response
        response.raise_for_status()
        return response.status_code, response.text
