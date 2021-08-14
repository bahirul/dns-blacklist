import sys
import os
import shutil

build_paths = [
    os.path.join(sys.path[0], 'build/bind/'),
    os.path.join(sys.path[0], 'build/hosts/'),
    os.path.join(sys.path[0], 'build/pihole/'),
    os.path.join(sys.path[0], 'build/dnsmasq/'),
    os.path.join(sys.path[0], 'build/pdns/'),
]

tmp_paths = [
    os.path.join(sys.path[0], 'tmp/blacklist/'),
    os.path.join(sys.path[0], 'tmp/whitelist/'),
]

def cleanPaths(paths):
    for build in paths:
        build_dir_list = os.listdir(build)
        for file in build_dir_list:
            full_path = build + file
            try:
                if os.path.isfile(full_path) or os.path.isdir(full_path):
                    if file != '.gitignore':
                        os.unlink(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except Exception as e:
                raise SystemError('failed to delete %s. reason: %s' % (full_path, e))

## FLUSH
print('clean build dir ...')
cleanPaths(paths=build_paths)
print('clean tmp dir ...')
cleanPaths(paths=tmp_paths)