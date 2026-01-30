#! /usr/bin/env python3

################################################################################
""" Docker interface for Thingy

    Copyright (C) 2017 John Skilleter

    Note that this:
        * Only implements functions required by docker-purge
        * Only has basic error checking, in that it raises DockerError
          for any error returned by the external docker command.
"""
################################################################################

import subprocess

################################################################################

class DockerError(Exception):
    """ Exception for dockery things """

    pass

################################################################################

def instances(all=False):
    """ Return a list of all current Docker instances """

    cmd = ['docker', 'ps', '-q']

    if all:
        cmd.append('-a')

    instances_list = []
    try:
        process = subprocess.run(cmd, capture_output=True, check=True, text=True)

        for result in process.stdout.splitlines():
            if result:
                instances_list.append(result)

    except subprocess.CalledProcessError as exc:
        raise DockerError(exc)

    return instances_list

################################################################################

def stop(instance, force=False):
    """ Stop the specified Docker instance """

    cmd = ['docker', 'stop']

    if force:
        cmd.append('--force')

    cmd.append(instance)

    try:
        subprocess.run(cmd, check=True, capture_output=False)

    except subprocess.CalledProcessError as exc:
        raise DockerError(exc)

################################################################################

def rm(instance, force=False):
    """ Remove the specified instance """

    cmd = ['docker', 'rm']

    if force:
        cmd.append('--force')

    cmd.append(instance)

    try:
        subprocess.run(cmd, check=True, capture_output=False)

    except subprocess.CalledProcessError as exc:
        raise DockerError(exc)

################################################################################

def images():
    """ Return a list of all current Docker images """

    try:
        process = subprocess.run(['docker', 'images', '-q'], capture_output=True, check=True, text=True)

        for result in process.stdout.splitlines():
            if result:
                yield result

    except subprocess.CalledProcessError as exc:
        raise DockerError(exc)

################################################################################

def rmi(image, force=False):
    """ Remove the specified image """

    cmd = ['docker', 'rmi']
    if force:
        cmd.append('--force')

    cmd.append(image)

    try:
        subprocess.run(cmd, capture_output=False, check=True)
    except subprocess.CalledProcessError as exc:
        raise DockerError(exc)
