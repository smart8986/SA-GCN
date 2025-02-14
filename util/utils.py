# Original Version: Taehoon Kim (http://carpedm20.github.io)
#   + Source: https://github.com/carpedm20/DCGAN-tensorflow/blob/e30539fb5e20d5a0fed40935853da97e9e55eee8/utils.py
#   + License: MIT

"""
Some codes from https://github.com/Newmu/dcgan_code
"""
from __future__ import division
import math
import os
import subprocess
import json
import random
import pprint
import scipy.misc
import numpy as np
from time import gmtime, strftime
import util.viz as viz
import util.data_utils as data_utils
import pdb

IMG_WIDTH = 320
IMG_HEIGHT = 240

pp = pprint.PrettyPrinter()


def get_stddev(x, k_h, k_w): return 1/math.sqrt(k_w*k_h*x.get_shape()[-1])


def video(sequence, tmp_dir, video_dir, name, data_mean_2d, data_std_2d, dim_to_ignore_2d, verbose=0, unnorm=True):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt
    if unnorm:
        sequence = data_utils.unNormalizeData(
            sequence, data_mean_2d, data_std_2d, dim_to_ignore_2d)
    else:
        sequence = data_utils.fillData(
            sequence, data_mean_2d, data_std_2d, dim_to_ignore_2d)

    gs1 = gridspec.GridSpec(1, 1)
    plt.axis('off')
    for t in range(sequence.shape[0]):
        # draw for sequence[t]
        plt.clf()

        ax2 = plt.subplot(gs1[0])
        p2d = sequence[t, :]
        viz.show2Dpose(p2d, ax2)
        ax2.invert_yaxis()
        if not os.path.exists(tmp_dir):
            os.system('mkdir -p "{}"'.format(tmp_dir))
        plt.savefig(os.path.join(tmp_dir, '%04d.jpg' % (t)))

    if not os.path.exists(video_dir):
        os.system('mkdir -p "{}"'.format(video_dir))
    np.save(os.path.join(video_dir, name), sequence)

    if verbose:
        os.system('ffmpeg -framerate 16 -y -i "' + os.path.join(tmp_dir,
                                                                "%04d.jpg") + '" "' + os.path.join(video_dir, name + '.mp4"'))
    else:
        subprocess.call(['ffmpeg', '-framerate', '16', '-y', '-i', os.path.join(tmp_dir, "%04d.jpg"),
                         os.path.join(video_dir, name + '.mp4')], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

    os.system('rm '+os.path.join(tmp_dir, '*'))


def video_real(sequence, video_dir, name):
    if np.max(sequence) <= 1.01:
        outputdata = sequence * 255
    outputdata = outputdata.astype(np.uint8)
    file_path = os.path.join(video_dir, '{}.mp4'.format(name))
    skvideo.io.vwrite(file_path, outputdata, inputdict={'-r': '16'})


def draw_pose(pose, pose_dir, name, data_mean_2d, data_std_2d, dim_to_ignore_2d, verbose=0, unnorm=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt

    pose = np.expand_dims(pose, axis=0)

    if unnorm:
        pose = data_utils.fillData(
            pose, data_mean_2d, data_std_2d, dim_to_ignore_2d)
    else:
        pose = data_utils.unNormalizeData(
            pose, data_mean_2d, data_std_2d, dim_to_ignore_2d)

    # plt.figure()
    gs1 = gridspec.GridSpec(1, 1)
    plt.axis('off')
    for t in range(pose.shape[0]):
        # draw for sequence[t]
        plt.clf()

        ax2 = plt.subplot(gs1[0])
        p2d = pose[t, :]
        viz.show2Dpose(p2d, ax2)
        ax2.invert_yaxis()
        if not os.path.exists(pose_dir):
            os.system('mkdir -p "{}"'.format(pose_dir))
        plt.savefig(os.path.join(pose_dir, name),
                    bbox_inches='tight', transparent=True, pad_inches=0)


def get_image(image_path, image_size, is_crop=True):
    return transform(imread(image_path), image_size, is_crop)


def save_images(images, size, image_path):
    return imsave(inverse_transform(images), size, image_path)


def imread(path):
    return scipy.misc.imread(path).astype(np.float)


def merge_images(images, size):
    return inverse_transform(images)


def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    img = np.zeros((int(h * size[0]), int(w * size[1]), 3))
    for idx, image in enumerate(images):
        i = idx % size[1]
        j = idx // size[1]
        img[j*h:j*h+h, i*w:i*w+w, :] = image

    return img


def imsave(images, size, path):
    return scipy.misc.imsave(path, merge(images, size))


def center_crop(x, crop_h, crop_w=None, resize_w=64):
    if crop_w is None:
        crop_w = crop_h
    h, w = x.shape[:2]
    j = int(round((h - crop_h)/2.))
    i = int(round((w - crop_w)/2.))
    return scipy.misc.imresize(x[j:j+crop_h, i:i+crop_w],
                               [resize_w, resize_w])


def transform(image, npx=64, is_crop=True):
    # npx : # of pixels width/height of image
    if is_crop:
        cropped_image = center_crop(image, npx)
    else:
        cropped_image = image
    return np.array(cropped_image)/127.5 - 1.


def inverse_transform(images):
    return (images+1.)/2.


def to_json(output_path, *layers):
    with open(output_path, "w") as layer_f:
        lines = ""
        for w, b, bn in layers:
            layer_idx = w.name.split('/')[0].split('h')[1]

            B = b.eval()

            if "lin/" in w.name:
                W = w.eval()
                depth = W.shape[1]
            else:
                W = np.rollaxis(w.eval(), 2, 0)
                depth = W.shape[0]

            biases = {"sy": 1, "sx": 1, "depth": depth,
                      "w": ['%.2f' % elem for elem in list(B)]}
            if bn != None:
                gamma = bn.gamma.eval()
                beta = bn.beta.eval()

                gamma = {"sy": 1, "sx": 1, "depth": depth, "w": [
                    '%.2f' % elem for elem in list(gamma)]}
                beta = {"sy": 1, "sx": 1, "depth": depth, "w": [
                    '%.2f' % elem for elem in list(beta)]}
            else:
                gamma = {"sy": 1, "sx": 1, "depth": 0, "w": []}
                beta = {"sy": 1, "sx": 1, "depth": 0, "w": []}

            if "lin/" in w.name:
                fs = []
                for w in W.T:
                    fs.append({"sy": 1, "sx": 1, "depth": W.shape[0], "w": [
                              '%.2f' % elem for elem in list(w)]})

                lines += """
                    var layer_%s = {
                        "layer_type": "fc",
                        "sy": 1, "sx": 1,
                        "out_sx": 1, "out_sy": 1,
                        "stride": 1, "pad": 0,
                        "out_depth": %s, "in_depth": %s,
                        "biases": %s,
                        "gamma": %s,
                        "beta": %s,
                        "filters": %s
                    };""" % (layer_idx.split('_')[0], W.shape[1], W.shape[0], biases, gamma, beta, fs)
            else:
                fs = []
                for w_ in W:
                    fs.append({"sy": 5, "sx": 5, "depth": W.shape[3], "w": [
                              '%.2f' % elem for elem in list(w_.flatten())]})

                lines += """
                    var layer_%s = {
                        "layer_type": "deconv",
                        "sy": 5, "sx": 5,
                        "out_sx": %s, "out_sy": %s,
                        "stride": 2, "pad": 1,
                        "out_depth": %s, "in_depth": %s,
                        "biases": %s,
                        "gamma": %s,
                        "beta": %s,
                        "filters": %s
                    };""" % (layer_idx, 2**(int(layer_idx)+2), 2**(int(layer_idx)+2),
                             W.shape[0], W.shape[3], biases, gamma, beta, fs)
        layer_f.write(" ".join(lines.replace("'", "").split()))


def make_gif(images, fname, duration=2, true_image=False):
    import moviepy.editor as mpy

    def make_frame(t):
        try:
            x = images[int(len(images)/duration*t)]
        except:
            x = images[-1]

        if true_image:
            return x.astype(np.uint8)
        else:
            return ((x+1)/2*255).astype(np.uint8)

    clip = mpy.VideoClip(make_frame, duration=duration)
    clip.write_gif(fname, fps=len(images) / duration)


def visualize(sess, dcgan, config, option):
    if option == 0:
        z_sample = np.random.uniform(-0.5, 0.5,
                                     size=(config.batch_size, dcgan.z_dim))
        samples = sess.run(dcgan.sampler, feed_dict={dcgan.z: z_sample})
        save_images(samples, [8, 8], './samples/test_%s.png' %
                    strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    elif option == 1:
        values = np.arange(0, 1, 1./config.batch_size)
        for idx in xrange(100):
            print(" [*] %d" % idx)
            z_sample = np.zeros([config.batch_size, dcgan.z_dim])
            for kdx, z in enumerate(z_sample):
                z[idx] = values[kdx]

            samples = sess.run(dcgan.sampler, feed_dict={dcgan.z: z_sample})
            save_images(samples, [8, 8],
                        './samples/test_arange_%s.png' % (idx))
    elif option == 2:
        values = np.arange(0, 1, 1./config.batch_size)
        for idx in [random.randint(0, 99) for _ in xrange(100)]:
            print(" [*] %d" % idx)
            z = np.random.uniform(-0.2, 0.2, size=(dcgan.z_dim))
            z_sample = np.tile(z, (config.batch_size, 1))
            #z_sample = np.zeros([config.batch_size, dcgan.z_dim])
            for kdx, z in enumerate(z_sample):
                z[idx] = values[kdx]

            samples = sess.run(dcgan.sampler, feed_dict={dcgan.z: z_sample})
            make_gif(samples, './samples/test_gif_%s.gif' % (idx))
    elif option == 3:
        values = np.arange(0, 1, 1./config.batch_size)
        for idx in xrange(100):
            print(" [*] %d" % idx)
            z_sample = np.zeros([config.batch_size, dcgan.z_dim])
            for kdx, z in enumerate(z_sample):
                z[idx] = values[kdx]

            samples = sess.run(dcgan.sampler, feed_dict={dcgan.z: z_sample})
            make_gif(samples, './samples/test_gif_%s.gif' % (idx))
    elif option == 4:
        image_set = []
        values = np.arange(0, 1, 1./config.batch_size)

        for idx in xrange(100):
            print(" [*] %d" % idx)
            z_sample = np.zeros([config.batch_size, dcgan.z_dim])
            for kdx, z in enumerate(z_sample):
                z[idx] = values[kdx]

            image_set.append(
                sess.run(dcgan.sampler, feed_dict={dcgan.z: z_sample}))
            make_gif(image_set[-1], './samples/test_gif_%s.gif' % (idx))

        new_image_set = [merge(np.array([images[idx] for images in image_set]), [10, 10])
                         for idx in range(64) + range(63, -1, -1)]
        make_gif(new_image_set, './samples/test_gif_merged.gif', duration=8)
