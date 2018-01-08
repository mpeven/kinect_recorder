import os, glob
import tarfile
from nacl.public import PrivateKey, PublicKey, Box

# Directories
base = os.path.dirname(os.path.realpath(__file__))
untar_dir = os.path.join(base, "tmp_untar")
data_dir  = os.path.join(base, "data")

# Files
rambo_key = os.path.join(base, "keys", "rambo_key")

# Make directory to untar files into
if not os.path.isdir(untar_dir):
    os.mkdir(untar_dir)

# Get all tarfiles
all_tars = sorted(glob.glob(data_dir + '/*'))

for tar_file_name in all_tars:
    # Get file names
    file_prefix = os.path.basename(tar_file_name).replace('.tar', '')
    client_key  = os.path.join(untar_dir, file_prefix + '_client_key.pub')
    rgb_file    = os.path.join(untar_dir, file_prefix + '_rgb_vid.avi')
    depth_file  = os.path.join(untar_dir, file_prefix + '_depth_vid.avi')


    # Untar file
    tar = tarfile.open(tar_file_name).extractall(path="tmp_untar")

    # Get keys to decryt
    with open(client_key, 'rb') as f:
        client_public_key = PublicKey(f.read())
    with open(rambo_key, 'rb') as f:
        rambo_private_key = PrivateKey(f.read())

    # Get videos
    with open(rgb_file, 'rb') as f:
        rgb_vid_encrypted = f.read()
    with open(depth_file, 'rb') as f:
        depth_vid_encrypted = f.read()

    # Decrypt videos
    rambo_box = Box(rambo_private_key, client_public_key)
    rgb_vid   = rambo_box.decrypt(rgb_vid_encrypted)
    depth_vid = rambo_box.decrypt(depth_vid_encrypted)
    with open(rgb_file, 'wb') as f:
        f.write(rgb_vid)
    with open(depth_file, 'wb') as f:
        f.write(depth_vid)
