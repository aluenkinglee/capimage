#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import stdout
from os import path
import argparse
from PIL import Image
import glob
import math

def check_image_with_pil(path):
	try:
		Image.open(path)
	except IOError:
		return False
	return True

def update_progress(progress):
    stdout.write('\r[{0}] {1}%'.format('#'*(progress/2), progress))
    stdout.flush()

def cap_image(source_image, capinsets, isretina=False):
	horizontal_fill_width = 1
	vertical_fill_height = 1
	top_inset = capinsets[0]
	left_inset = capinsets[1]
	bottom_inset = capinsets[2]
	right_inset = capinsets[3]

	if isretina:
		horizontal_fill_width *= 2
		vertical_fill_height *= 2
		top_inset *= 2
		left_inset *= 2
		bottom_inset *= 2
		right_inset *= 2

	source_image_width = source_image.size[0]
	source_image_height = source_image.size[1];
	
	target_image_width = left_inset + right_inset + horizontal_fill_width
	target_image_height = top_inset + bottom_inset + vertical_fill_height
	
	target_image = Image.new("RGBA", (target_image_width, target_image_height),None)

	top_left_image = source_image.crop((0, 0, left_inset, top_inset))
	top_middle_image = source_image.crop((left_inset, 
								0, 
								left_inset + horizontal_fill_width, 
								top_inset))
	top_right_image = source_image.crop((source_image_width - right_inset,
								0,
								source_image_width,
								top_inset))
	middle_left_image = source_image.crop((0, 
								top_inset, 
								left_inset, 
								top_inset + vertical_fill_height))
	middle_middle_image = source_image.crop((left_inset, 
									top_inset, 
									left_inset + horizontal_fill_width, 
									top_inset + vertical_fill_height))
	middle_right_image = source_image.crop((source_image_width - right_inset,
								top_inset,
								source_image_width,
								top_inset + vertical_fill_height))
	bottom_left_image = source_image.crop((0,
								source_image_height - bottom_inset,
								left_inset,
								source_image_height))
	bottom_middle_image = source_image.crop((left_inset,
									source_image_height - bottom_inset,
									left_inset + horizontal_fill_width,
									source_image_height))
	bottom_right_image = source_image.crop((source_image_width - right_inset,
									source_image_height - bottom_inset,
									source_image_width,
									source_image_height))
	
	
	target_image.paste(top_left_image, (0, 0))
	target_image.paste(top_middle_image, (left_inset,0))
	target_image.paste(top_right_image, (left_inset + horizontal_fill_width,0))
	target_image.paste(middle_left_image, (0, top_inset))
	target_image.paste(middle_middle_image, (left_inset, top_inset))
	target_image.paste(middle_right_image, (left_inset + horizontal_fill_width, top_inset))
	target_image.paste(bottom_left_image, (0, top_inset + vertical_fill_height))
	target_image.paste(bottom_middle_image, (left_inset, top_inset + vertical_fill_height))
	target_image.paste(bottom_right_image, (left_inset + horizontal_fill_width, top_inset + vertical_fill_height))
	
	return target_image





def detect_image(image, isretina=False):
	dataList = list(image.getdata())
	source_image_width = image.size[0]
	source_image_height = image.size[1];
	
	rowlist = []; #rowlist保存了每一行的像素点
	for i in xrange(source_image_height):
		rowlist.append([])

	columnlist = [] #columnlist保存了每一列的像素点
	for i in xrange(source_image_width):
		columnlist.append([])

	#填充rowlist和columnlist，使用整除和余数来构造list索引
	for i in xrange(len(dataList)):
		data = dataList[i]
		rowlist[i / source_image_width].append(data)
		columnlist[i % source_image_width].append(data)
	
	repeatedrow_intervals = [] #repeatedrow_intervals记录搜索像素值相同的行的范围集合
	max_repeatedrow_interval = [0, 0] #记录repeatedrow_intervals中
	for i in xrange(source_image_height - 1):
		if rowlist[i]==rowlist[i + 1]:
			rowpair = [i, i + 1]
			if len(repeatedrow_intervals) > 0 and repeatedrow_intervals[-1][1] == rowpair[0]:
				repeatedrow_intervals[-1][1] = rowpair[1]
			else:
				repeatedrow_intervals.append(rowpair)

			if max_repeatedrow_interval[1] - max_repeatedrow_interval[0] < repeatedrow_intervals[-1][1] - repeatedrow_intervals[-1][0]:
				max_repeatedrow_interval = repeatedrow_intervals[-1];

	repeatedcol_intervals = []
	max_repeatedcol_interval = [0,0]
	for i in xrange(source_image_width - 1):
		if columnlist[i] == columnlist[i + 1]:
			colpair = [i, i + 1]
			if len(repeatedcol_intervals) > 0 and repeatedcol_intervals[-1][1] == colpair[0]:
				repeatedcol_intervals[-1][1] = colpair[1]
			else:
				repeatedcol_intervals.append(colpair)

			if max_repeatedcol_interval[1] - max_repeatedcol_interval[0] < repeatedcol_intervals[-1][1] - repeatedcol_intervals[-1][0]:
				max_repeatedcol_interval = repeatedcol_intervals[-1]

	capinsets = (max_repeatedrow_interval[0],
							max_repeatedcol_interval[0],
							source_image_height - 1 - max_repeatedrow_interval[1],
							source_image_width - 1 - max_repeatedcol_interval[1])
	if isretina:
			capinsets = tuple(int(math.ceil(capinset/2.0)) for capinset in capinsets)

	detection_info = {
	'repeatedrow_intervals' : repeatedrow_intervals,
	'max_repeatedrow_interval' : max_repeatedrow_interval,
	'repeatedcol_intervals' : repeatedcol_intervals,
	'max_repeatedcol_interval' : max_repeatedcol_interval,
	'suggested_capinsets' : capinsets
	}

	return detection_info



parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="subparser_name")
parser_image_detect = subparsers.add_parser("detect")
parser_image_detect.add_argument('source_file',nargs='+')
parser_image_gen = subparsers.add_parser("gen")
parser_image_gen.add_argument('-c','--capinsets',dest='capinsets', nargs = 4,type = int,metavar=('top', 'left', 'bottom', 'right'))
parser_image_gen.add_argument('-t','--target-directory',dest='target_directory',help='target_directory')
parser_image_gen.add_argument('source_file',nargs='+')
args=parser.parse_args()

subparser_name = args.subparser_name
for filepath in args.source_file:
	filepath = path.expanduser(filepath)
	for f in glob.iglob(filepath):
		if check_image_with_pil(f):
			is_retina_image = False
			if '@2x.' in f:
				is_retina_image = True

			image = Image.open(f)
			
			if subparser_name == 'detect':
				print "******************************************"
				print "Detection For Image: '%s' Begin..." % (f)
				print "Image Size:%sx%s"%(image.size[0],image.size[1])
				detection_info = detect_image(image,is_retina_image)
				print "Repeated rows intervals:%s" % (detection_info['repeatedrow_intervals'],)
				print "Max row interval:%s" % (detection_info['max_repeatedrow_interval'],)
				print "Repeated columns intervals:%s" % (detection_info['repeatedcol_intervals'],)
				print "Max column interval:%s" % (detection_info['max_repeatedcol_interval'],)
				print "Suggested Cap Insets:%s" % (detection_info['suggested_capinsets'],)
			
			if subparser_name == 'gen':
				args_dic = vars(args)
				if 'capinsets' in args_dic and args_dic['capinsets'] is not None:
					capinsets = tuple(i for i in args.capinsets)
				else:
					detection_info = detect_image(image,is_retina_image)
					capinsets = detection_info['suggested_capinsets']

				if 'target_directory' in args_dic and args_dic['target_directory'] is not None:
					target_directory = args.target_directory
				else:
					target_directory = '.'

				print capinsets

				target_image = cap_image(image, capinsets,is_retina_image)
				filename = path.split(f)[1]
				if is_retina_image:
					sep = '@2x.'
				else:
					sep = '.'
				
				filenameseps = filename.rsplit(sep,1)


				capstring = '-'.join("%d"%i for i in capinsets)
				newfilename = '%s-%s%s%s'%(filenameseps[0],capstring,sep,filenameseps[1])
				target_file_path = path.join(target_directory,newfilename)
				target_image.save(target_file_path,image.format)


		else:
			print "******************************************"
			print "'%s' is not a valid image !" %(f)

