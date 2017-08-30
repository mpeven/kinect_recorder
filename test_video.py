import cv2, av, glob, subprocess, compare_depth_images

depth = False

# Make video
image_list = sorted(glob.glob('{}_imgs/*'.format('depth' if depth else 'rgb')))
pix_fmt = 'gray16' if depth else 'yuv420p'
frame_fmt = 'gray16' if depth else 'bgr24'
codec = 'ffv1' if depth else 'libx264'
vid = av.open('test.avi', mode='w')
vid_stream = vid.add_stream(codec, 24)
vid_stream.pix_fmt = pix_fmt
img0 = cv2.imread(image_list[0])
height, width, _ = img0.shape
vid_stream.height = height
vid_stream.width = width
for i in image_list:
    image = cv2.imread(i, -1)
    frame = av.VideoFrame(width, height, frame_fmt)
    frame.planes[0].update(image)
    packet = vid_stream.encode(frame)
    if packet:
        vid.mux(packet)
vid.close()


if depth:
    # Uncompress video to images
    cmd = 'avconv -i test.avi -f image2 -pix_fmt gray16 depth_imgs_uncompressed/frame%06d.png'
    out = subprocess.getoutput(cmd)
    print(out)
    print('\n\n\n')

    # Compare
    for x in range(20):
        f1 = image_list[x]
        f2 = sorted(glob.glob('depth_imgs/*'))[x]
        compare_depth_images.compare_images(f1, f2)

else:
    # Uncompress video to images
    cmd = 'avconv -i test.avi rgb_imgs_uncompressed/frame%06d.png'
    out = subprocess.getoutput(cmd)
    print(out)
    print('\n\n\n')

    # Compare

