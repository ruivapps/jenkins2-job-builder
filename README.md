# Jinkins2-job-builder

Due to current jenkins-job-builder is broken under Jenkins2.

This is temporary solution allows people to push job to Jenkins from CLI.

This tool still require install of jenkins-job-build to parse YAML file. 


--conf CONF will directly pass to jenkins-jobs tool. for Jenkins-jobs, please see documentation on how to configure it. 

~~~
usage: jenkins2-job [-h] [-u] [-c] [--conf CONF] filename

call jenkins-jobs to interpret YMAM to XML then push to Jenkins

positional arguments:
  filename      filename of the YAML file

optional arguments:
  -h, --help    show this help message and exit
  -u, --update  update(ovewrite) job if already exist
  -c, --create  create job if not exist. exit if already exist
  --conf CONF   use this configuration file instead of default
  ~~~
  
  Tested on python 2.7.14 and 3.6.4 on OSX only.