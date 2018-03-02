#!/usr/bin/env python

import sys
import xml.etree.ElementTree as ET
import responses
import pytest
import requests
import jenkins2_jobs
from jenkins_jobs.errors import JenkinsJobsException

JOB_YAML = 'JenkinsJob.yaml'
JOB_ERROR_YAML = 'JenkinsJobError.yaml'
JOB_PATH = 'test/folder/test1/myjob'
USER = 'user1'
PASSWORD = 'password1'
JENKINS = 'http://jenkins.com'

class Test_Ask_Help_From_Jenkins_Job:
    def test_ask_jenkins_job(self):
        #FIXME: didn't mock configuration file
        job_xml, _ = jenkins2_jobs.from_jenkins_job(JOB_YAML)
        root = ET.fromstring(job_xml[0].output())
        assert root.tag == 'flow-definition'
        assert root.attrib == {'plugin': 'workflow-job'}

    def test_raise_error(self):
        with pytest.raises(JenkinsJobsException):
            jenkins2_jobs.from_jenkins_job(JOB_ERROR_YAML)


def test_jenkins_folder_xml():
    job_xml = jenkins2_jobs.jenkins_folder_xml()
    root = ET.fromstring(job_xml)
    assert root.tag == 'com.cloudbees.hudson.plugins.folder.Folder'
    assert root.attrib == {'plugin': 'cloudbees-folder'}

class TestURL:
    def test_build_jenkins_url(self):
        urls = ['http://jenkins.com/job/test/job/folder/job/test1/job/myjob/config.xml',
                'http://jenkins.com/job/test/job/folder/job/test1/config.xml',
                'http://jenkins.com/job/test/job/folder/config.xml',
                'http://jenkins.com/job/test/config.xml',
                'http://jenkins.com/config.xml']
        for url in jenkins2_jobs.build_jenkins_url('http://jenkins.com', JOB_PATH):
            assert url == urls.pop(0)

    def test_update_2_create_url(self):
        update_url = 'http://jenkins.com/Python/job/test/job/jenkins2_jobs/config.xml'
        create_url = 'http://jenkins.com/Python/job/test/createItem?name=jenkins2_jobs'
        assert jenkins2_jobs.update_url_2_create_url(update_url) == create_url

def test_find_jenkins_job_path():
    path = list(jenkins2_jobs.find_jenkins_job_path(JOB_YAML))
    assert path[0] == JOB_PATH

class TestJenkins2Job:
    def test_init(self):
        jenkins2jobs = jenkins2_jobs.Jenkins2Jobs(USER, PASSWORD)
        assert isinstance(jenkins2jobs.session, requests.sessions.Session)
        assert jenkins2jobs.session.auth == (USER, PASSWORD)

    @responses.activate
    def test_query_job(self):
        message = 'hello from server'
        responses.add(responses.GET, '{}/job.xml'.format(JENKINS), body=message)
        jenkins2jobs = jenkins2_jobs.Jenkins2Jobs(USER, PASSWORD)
        status_code, result = jenkins2jobs.query_job('{}/job.xml'.format(JENKINS))
        assert status_code == 200
        assert result == message

    @responses.activate
    def test_error_query_job(self):
        message = 'page not found'
        responses.add(responses.GET, '{}/job.xml'.format(JENKINS), status=404, body=message)
        jenkins2jobs = jenkins2_jobs.Jenkins2Jobs(USER, PASSWORD)
        with pytest.raises(requests.exceptions.HTTPError):
            jenkins2jobs.query_job('{}/job.xml'.format(JENKINS))
        assert jenkins2jobs._response_.status_code == 404
        assert jenkins2jobs._response_.text == message

    @responses.activate
    def test_create_job(self):
        message = 'page updated'
        responses.add(responses.POST, '{}/job.xml'.format(JENKINS), body=message)
        jenkins2jobs = jenkins2_jobs.Jenkins2Jobs(USER, PASSWORD)
        status_code, result = jenkins2jobs.create_job('{}/job.xml'.format(JENKINS), "<XML>")
        assert status_code == 200
        assert result == message

    @responses.activate
    def test_error_create_job(self):
        message = 'page updated'
        responses.add(responses.POST, '{}/job.xml'.format(JENKINS), status=404, body=message)
        jenkins2jobs = jenkins2_jobs.Jenkins2Jobs(USER, PASSWORD)
        with pytest.raises(requests.exceptions.HTTPError):
            jenkins2jobs.create_job('{}/job.xml'.format(JENKINS), "<XML>")
        assert jenkins2jobs._response_.status_code == 404
        assert jenkins2jobs._response_.text == message

