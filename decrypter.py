import os, glob
import tarfile
from nacl.public import PrivateKey, PublicKey, Box

untar_dir = "tmp_untar"

# Get all tarfiles
all_tars = sorted(glob.glob('data/*'))

for tar_file_name in all_tars:
    file_prefix = os.path.basename(tar_file_name).replace('_.tar', '')

    # Untar file
    tar = tarfile.open(tar_file_name).extractall(path="tmp_untar")

    # Get keys to decryt
    with open('tmp_untar/' + file_prefix + '_client_key.pub', 'rb') as f:
        client_public_key = PublicKey(f.read())
    with open('keys/rambo_key', 'rb') as f:
        rambo_private_key = PrivateKey(f.read())

    # Get videos
    with open('tmp_untar/' + file_prefix + '_rgb_vid.avi', 'rb') as f:
        rgb_vid_encrypted = f.read()
    with open('tmp_untar/' + file_prefix + '_depth_vid.avi', 'rb') as f:
        depth_vid_encrypted = f.read()

    # Decrypt videos
    rambo_box = Box(rambo_private_key, client_public_key)
    rgb_vid = rambo_box.decrypt(rgb_vid_encrypted)
    depth_vid = rambo_box.decrypt(depth_vid_encrypted)
    with open('tmp_untar/' + file_prefix + '_rgb_vid.avi', 'wb') as f:
        f.write(rgb_vid)
    with open('tmp_untar/' + file_prefix + '_depth_vid.avi', 'wb') as f:
        f.write(depth_vid)
