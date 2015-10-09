#!/usr/bin/env python

# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""Test a Fast R-CNN network on an image database."""

import _init_paths
from fast_rcnn.test import test_net, apply_nms
from fast_rcnn.config import cfg, cfg_from_file, cfg_from_list, get_output_dir
from datasets.factory import get_imdb
import caffe
import argparse
import pprint
import time, os, sys
import sg_utils as sg_utils
import lib.sds.test_hypercolumns as sds_test

def parse_args():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(description='Test a Fast R-CNN network')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU id to use',
                        default=0, type=int)
    parser.add_argument('--def', dest='prototxt',
                        help='prototxt file defining the network',
                        default=None, type=str)
    parser.add_argument('--net', dest='caffemodel',
                        help='model to test',
                        default=None, type=str)
    parser.add_argument('--cfg', dest='cfg_file',
                        help='optional config file', default=None, type=str)
    parser.add_argument('--wait', dest='wait',
                        help='wait until net file exists',
                        default=True, type=bool)
    parser.add_argument('--imdb', dest='imdb_name',
                        help='dataset to test',
                        default='voc_2007_test', type=str)
    parser.add_argument('--comp', dest='comp_mode', help='competition mode',
                        action='store_true')
    parser.add_argument('--score_blob_name', default='cls_prob', type=str)
    parser.add_argument('--bbox_blob_name', default='bbox_pred', type=str)
    parser.add_argument('--set', dest='set_cfgs',
                        help='set config keys', default=None,
                        nargs=argparse.REMAINDER)
    
    parser.add_argument('--sds', default=0, type=int)
    parser.add_argument('--sds_sp_dir', default=None, type=str)
    parser.add_argument('--sds_detection_file', default=None, type=str)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()

    print('Called with args:')
    print(args)

    if args.cfg_file is not None:
        cfg_from_file(args.cfg_file)

    print('Using config:')
    pprint.pprint(cfg)

    while not os.path.exists(args.caffemodel) and args.wait:
        print('Waiting for {} to exist...'.format(args.caffemodel))
        time.sleep(10)

    caffe.set_mode_gpu()
    caffe.set_device(args.gpu_id)
    net = caffe.Net(args.prototxt, args.caffemodel, caffe.TEST)
    net.name = os.path.splitext(os.path.basename(args.caffemodel))[0]

    imdb = get_imdb(args.imdb_name)
    imdb.competition_mode(args.comp_mode)

    if args.sds > 0:
      output_dir = os.path.join(get_output_dir(imdb, net), 'segm' + cfg.TEST.DET_SALT)
      if not os.path.exists(output_dir):
        os.makedirs(output_dir)
      
      gt_roidb = imdb.gt_roidb();
      imdb._attach_instance_segmentation();

      # load detection boxes and do nms 
      with open(args.sds_detection_file, 'r'):
        dt = sg_utils.load_variables(args.sds_detection_file)['all_boxes']
      dt_nms = apply_nms(dt, 0.3)
      dt_nms = dt_nms[1:]
      sds_test.get_all_outputs(net, imdb, dt_nms, args.sds_sp_dir, thresh=0.4, out_dir = output_dir, 
        do_eval = True, eval_thresh = [0.5, 0.7])
    
    else:
      test_net(net, imdb, args.score_blob_name, args.bbox_blob_name)
