#!/usr/bin/env python
"""
entry point of the script
this script exist because jenkins-job-builder no longer works with
Jenkins Enterprise 2.
"""
from __future__ import print_function
import argparse
import os
import requests
import jenkins2_jobs

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
    args = parse()
    job_xml, configuration = jenkins2_jobs.from_jenkins_job(args.filename, args.conf)
    job_path = jenkins2_jobs.find_jenkins_job_path(args.filename)
    urls = list(jenkins2_jobs.build_jenkins_url(configuration['url'], job_path))
    jenkins = jenkins2_jobs.Jenkins2Jobs(configuration['user'], configuration['password'])
    print("\n")
    if args.update:
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
    elif args.create:
        job_url = urls.pop(0)
        try:
            jenkins.query_job(job_url)
            raise SystemExit("job already exist on server. exit.\n\t{}".format(job_url))
        except requests.exceptions.HTTPError:
            pass
        # need to figure out if path (folder) exist or not. root->leaf is easy.
        folder_xml = jenkins2_jobs.jenkins_folder_xml()
        while urls:
            url = urls.pop()
            try:
                jenkins.query_job(url)
            except requests.exceptions.HTTPError:
                print("try to create folder:\n\t{}".format(os.path.split(url)[0]))
                # folder do not exist, try to create it
                try:
                    jenkins.create_job(jenkins2_jobs.update_url_2_create_url(url), folder_xml)
                    print("successful created the folder")
                except requests.exceptions.HTTPError as error:
                    # error create folder
                    raise SystemExit("error create folder.\nErrors:\n\t{}".format(error))
        # with path exist, create job
        try:
            print("try to create job:\n\t{}".format(os.path.split(url)[0]))
            jenkins.create_job(jenkins2_jobs.update_url_2_create_url(job_url), job_xml)
            print("successful created the job")
        except requests.exceptions.HTTPError as error:
            raise SystemExit("error create job.\nErrors:\n\t{}".format(error))
    else:
        raise NotImplementedError


if __name__ == '__main__':
    main()
