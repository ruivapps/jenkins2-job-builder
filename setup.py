import setuptools

_version_ = '1.4'

setuptools.setup(
    name="jenkins2-job-builder",
    version=_version_,
    author='Rui Li',
    author_email='rui.li.spam@gmail.com',
    description="temporary solution to push jobs to Jenkins2 due to jenkins-job-builder currently is brokwn on Jenkins2",
    long_description=open('README.rst').read(),
    license="MIT License",
    url="https://github.com/ruivapps/jenkins2-job-builder",
    download_url='https://github.com/ruivapps/jenkins2-job-builder/tarball/{}'.format(_version_),
    packages=["jenkins2_job_builder"],
    package_dir={'jenkins2_job_builder': 'jenkins2_job_builder'},
    package_data={'jenkins2_job_builder': ['*.py']},
    install_requires=['requests', 'jenkins-job-builder', 'PyYAML'],
    classifiers=[
        "Environment :: Console",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        'console_scripts': ['jenkins2-jobs=jenkins2_job_builder.jenkins2_jobs:main']},
)
