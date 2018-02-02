#!/usr/bin/env python
# encoding=utf-8
"""
Jenkins Job Builder do not work on Jenkins2 due to Jenkins2's enhanced security feature
This is just a temp fix script that would work with Jenkins2 Enterprise 2.
"""
from __future__ import print_function
import argparse
import os
import sys
import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

import requests
import yaml

# pylint: disable=C0301,R0912

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
        """split all path"""
        parent, _ = os.path.split(path)
        if parent:
            yield parent
            for _path_ in split(parent):
                yield _path_
    yield os.path.join(url, 'job', '/job/'.join(path.split('/')), 'config.xml')
    for _path_ in split(path):
        yield os.path.join(url, 'job', '/job/'.join(_path_.split('/')), 'config.xml')
    yield os.path.join(url, 'config.xml')


def find_jenkins_job_path(yaml_file):
    """find jenkins job path from YAML file
    currently looking for job['name'] field

    :param yaml_file: the content of yaml file
    :type yaml_file: str

    :return generator
    """

    data = yaml.load(open(yaml_file))
    for line in data:
        if 'job' not in line:
            continue
        if 'name' not in line['job']:
            continue
        yield line['job']['name']

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

def split_xml(xml_data):
    """if YAML has more than one job defined.
    the stdout redirect hack will get all html together
    need to split it apart

    :param xml_data: xml content
    :type xml_data: str

    :return generator
    """
    xml_header = '<?xml version="1.0" encoding="utf-8"?>\n'
    if sys.version_info.major == 3:
        xml_data = xml_data.decode()
    for xml in xml_data.split(xml_header):
        if xml:
            yield xml_header+xml


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


def parse():
    """command line arguments parse
    """
    parser = argparse.ArgumentParser(description='call jenkins-jobs to interpret YMAM to XML then push to Jenkins')
    parser.add_argument('-u', '--update', help='update(ovewrite) job if already exist',
                        action='store_true', default=False)
    parser.add_argument('-c', '--create', help='create job if not exist. exit if already exist',
                        action='store_true', default=False)
    parser.add_argument('--conf', help='use this configuration file instead of default')
    parser.add_argument('filename', help='filename of the YAML file', type=str)
    args = parser.parse_args()
    if not args.update and not args.create:
        raise SystemExit(parser.print_help())
    if args.update and args.create:
        raise SystemExit("update or create, not both")
    try:
        with open(args.filename) as _:
            pass
    except Exception as error:
        raise SystemExit("can not open file {}\nerror:\n\t{}".format(args.filename, error))
    return args


def main():
    """cli entry point
    """
    args = parse()
    job_xml, configuration = from_jenkins_job(args.filename, args.conf)
    job_xml = list(split_xml(job_xml))
    job_urls = {}
    for job_path in find_jenkins_job_path(args.filename):
        job_urls[job_path] = list(build_jenkins_url(configuration['url'], job_path))
    jenkins = Jenkins2Jobs(configuration['user'], configuration['password'])
    print("\n")


    xml_counter = 0
    for urls in job_urls.values():
        job_url = urls.pop(0)
        # need to figure out if path (folder) exist or not. root->leaf is the most easiest way.
        folder_xml = jenkins_folder_xml()
        while urls:
            url = urls.pop()
            try:
                jenkins.query_job(url)
            except requests.exceptions.HTTPError:
                print("try to create folder:\n\t{}".format(os.path.split(url)[0]))
                # folder do not exist, try to create it
                try:
                    jenkins.create_job(update_url_2_create_url(url), folder_xml)
                    print("successful created the folder")
                except requests.exceptions.HTTPError as error:
                    # error create folder
                    print("error create folder.\nErrors:\n\t{}".format(error))
        try:
            jenkins.query_job(job_url)
            # job already exist. update if arg.update is True
            if args.update:
                # update (overwrite) the job
                """
                if args.update:
                    for urls in job_urls.values():
                        url = urls[0]
                        try:
                            jenkins.query_job(url)
                        except requests.exceptions.HTTPError as error:
                            raise SystemExit("can not update job.\nErrors:\n\t{}".format(error))
                    try:
                        jenkins.create_job(url, job_xml)
                    except requests.exceptions.HTTPError as error:
                        raise SystemExit("error create job.\nErrors:\n\t{}".format(error))
                    print("successful updated the job")
                """
                try:
                    print("try to update job:\n\t{}".format(os.path.split(url)[0]))
                    jenkins.create_job(job_url, job_xml[xml_counter])
                    print("successful updated the job")
                except requests.exceptions.HTTPError as error:
                    print("error update the job.\nErrors:\n\t{}".format(error))
            else:
                print("job already exit, update is set to {}. Skip this job.\n\t{}".format(args.update, job_url))
        except requests.exceptions.HTTPError:
            # job do not exit, create new job
            try:
                print("try to create job:\n\t{}".format(os.path.split(url)[0]))
                jenkins.create_job(update_url_2_create_url(job_url), job_xml[xml_counter])
                print("successful created the job")
            except requests.exceptions.HTTPError as error:
                print("error create job.\nErrors:\n\t{}".format(error))
                print(job_xml[xml_counter])
        xml_counter += 1


if __name__ == '__main__':
    main()
