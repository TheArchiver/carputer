"""Utils for writing html debug files.

Mostly those methods used by convnet02.py
"""

import base64
import io
from shutil import copyfile
import os

import numpy as np
from PIL import Image, ImageDraw
import tensorflow as tf

from convnetshared1 import NNModel
from data_model import TrainingData

num_conv_debugs = 4

def argmax(l):
    max = -1000000000.0
    index = 0
    for i in l:
        if i > max:
            max = index
        index = index + 1
    return max


def write_html_image_tensor_gray(outfile, tensor, rgb, scale=1):
    dims = len(tensor.shape)
    h = tensor.shape[dims - 2]
    w = tensor.shape[dims - 1]
    d = 1
    if dims >= 3:
        d = tensor.shape[dims - 3]
    b = 1
    if dims >= 4:
        b = tensor.shape[dims - 4]
    if rgb == True:
        d = 1
        b = 1
        w = tensor.shape[dims - 3]
        h = tensor.shape[dims - 2]
        if dims >= 4:
            d = tensor.shape[dims - 4]
    outfile.write("<div style='border:2px;border-style:solid;border-color:#66a;margin-top:2px;padding:2px'>")
    tempImg = tensor.flatten()
    # range expand image to [0..255]
    min = np.amin(tempImg)
    max = np.amax(tempImg)
    tempImg = np.add(tempImg, -min)
    tempImg = np.multiply(tempImg, 255.0)
    tempImg = np.divide(tempImg, max - min)

    if rgb == True:
        b64 = Image.frombuffer('RGB', (w, h*d), tempImg.astype(np.int8), 'raw', 'RGB', 0, 1)
    else:
        b64 = Image.frombuffer('L', (w, h*b*d), tempImg.astype(np.int8), 'raw', 'L', 0, 1)
    # b64.save("testtest.png")
    b = io.BytesIO()
    b64.save(b, 'PNG')
    b64 = base64.b64encode(b.getvalue())
    outfile.write('<img style ="image-rendering:-moz-crisp-edges;image-rendering:pixelated" width="' + str(w*scale) + '" src="data:image/png;base64,')
    # outfile.write('<img style ="image-rendering:pixelated" src="data:image/png;base64,')
    outfile.write(b64)
    outfile.write('" alt="testImage.png"><br/>\n')
    outfile.write('min: ' + str(min) + '<br/>')
    outfile.write('max: ' + str(max) + '<br/>')
    outfile.write('</div>')


def write_html_image_tensor_gray_overlay(outfile, tensor, scale, layer_id, im_id, conv_max):
    dims = len(tensor.shape)
    h = tensor.shape[dims - 2]
    w = tensor.shape[dims - 1]
    d = 1
    if dims >= 3:
        d = tensor.shape[dims - 3]
    b = 1
    if dims >= 4:
        b = tensor.shape[dims - 4]
    # outfile.write('<div id="pixels' + str(layer_id) + '_' + str(im_id) + '" style="display:none;position:absolute;top:2px;left:2px;">')
    outfile.write('<div id="pixels' + str(layer_id) + '_' + str(im_id) + '" style="position:absolute;top:2px;left:132px;">')
    tempImg = tensor#.flatten()
    # range expand image to [0..255]
    min = 0.0#np.amin(tempImg)
    max = conv_max# np.amax(tempImg)
    tempImg = np.add(tempImg, -min)
    tempImg = np.multiply(tempImg, 16.0)
    tempImg = np.clip(tempImg, 0.0, 255.0)
    # tempImg = np.divide(tempImg, max - min)
    tempImg = tempImg.astype(np.int8)
    newImg = np.zeros((tensor.shape[0], tensor.shape[1], 4), dtype=np.int8)
    newImg[:,:,0] = 255
    newImg[:,:,1] = 0
    newImg[:,:,2] = 64
    newImg[:,:,3] = tempImg

    b64 = Image.frombuffer('RGBA', (w, h), newImg, 'raw', 'RGBA', 0, 1)
    # b64 = Image.frombuffer('RGBA', (w, h*b*d), tempImg, 'raw', 'L', 0, 1)
    # b64.save("testtest.png")
    b = io.BytesIO()
    b64.save(b, 'PNG')
    b64 = base64.b64encode(b.getvalue())
    outfile.write('<img style ="image-rendering:-moz-crisp-edges;image-rendering:pixelated" width="' + str(w*scale) + '" src="data:image/png;base64,')
    # outfile.write('<img style ="image-rendering:pixelated" src="data:image/png;base64,')
    outfile.write(b64)
    outfile.write('">\n')
    outfile.write("<div style='position:absolute;top:0px;left:0px;color:#8f8'>" + str(max) + "</div>")

    outfile.write('</div>')


def write_vertical_meter(outfile, x, total, col = 'rgb(255, 255, 0)'):
    outfile.write('<svg width = "8" height = "' + str(total*8) + '" style="background:#606060"><rect width = "7" height = "' + str(x*8)  + '" y = "' + str((total-x) * 8) + '" style = "fill:' + col + ';" /></svg>')

def write_steering_line(outfile, x, col = 'rgb(255, 255, 0)', line_width = 3):
    s = '<svg width="190" height="160" stroke-width="%s" style="position:absolute;top:0px;left:0px"><path d="M64 128 Q 64 84 %s 66" stroke="%s" fill="transparent"/></svg>' % (line_width, str(x + 64), col)
    outfile.write(s)

def encode_image_as_html(outfile, img, filetype='JPEG', attrib =''):
    # img.save("testtest.png")
    b = io.BytesIO()
    img.save(b, filetype, quality=50)
    img = base64.b64encode(b.getvalue())
    outfile.write('<img ' + attrib + ' src="data:image/png;base64,')
    outfile.write(img)
    outfile.write('">\n')

def draw_softmax_distribution(outfile, label, softmax, gt, draw_zero_point=False):
    soft_img = Image.new('RGBA', (128, 32), (0, 0, 0, 64))
    draw = ImageDraw.Draw(soft_img)
    soft_size = softmax.shape[0]
    scale = (soft_img.width / soft_size)
    # draw rectangle to mark 0-speed mapping
    if draw_zero_point:
        draw.rectangle([5 * scale, soft_img.height / 2, 5 * scale + scale - 2, soft_img.height], (16, 16, 32, 56))
    for i in range(soft_size):
        fill_color = (255, 255, 255, 255)
        if i == gt: fill_color = (0, 255, 0, 255)
        prob = softmax[i]
        draw.rectangle([i * scale, soft_img.height - round(prob * soft_img.height), i * scale + scale - 2, soft_img.height], fill_color)
    outfile.write('<div style="position:relative;padding-bottom:4px">')
    encode_image_as_html(outfile, soft_img, 'PNG', 'style="position:absolute"')
    outfile.write(label + '</div><br/>')

def write_html_image(outfile, result_steering, result_throttle, test_data, w, h, message, im_id, steering_softmax, throttle_softmax, steering_regress, throttle_regress):
    images = test_data.pic_array[im_id]
    answers = test_data.steer_onehot_array[im_id]
    answers_throttle = test_data.throttle_onehot_array[im_id]
    steering_gt = argmax(answers)
    throttle_gt = argmax(answers_throttle)

    # pulse_entropy = np.sum( np.multiply(pulse_softmax, np.log(np.reciprocal(pulse_softmax))) )

    # Fade color from green to yellow to red and make a table cell with that background color.
    # (40, 88, 136, 184, 232, 280)
    # (400,352,304, 256, 208, 160, 112, 64, 16)
    delta = abs(steering_gt - result_steering)
    shade = 'rgb(%s, %s, %s)' % (min(232, delta * 52 + 20), max(0, min(255-32, 448 - delta * 48)), min(80, delta * 80))
    #remap entropy to around [0..1] range.
    # ent01 = min(1.0, max(0.0, pulse_entropy * 0.5 - 0.1))
    # shade = 'rgb(%s, %s, %s)' % (min(255,int(ent01 * 255*2)), max(0,int((2.0-ent01*2.0) * 255)), 64)
    # in_set = im_id in max_sets[0]
    # if in_set:
    shade = 'rgb(255, 255, 255)'
    color = "style='background:%s;position:relative;padding:2px;border:2px solid black;white-space:nowrap;'" % (shade)
    padded_id = str(im_id).zfill(5)
    outfile.write('<td id="td' + padded_id + '" ' + color + '><span>')

    # Save out camera image as embedded .png and draw steering direction curves on the image.
    tempImg = np.copy(images)
    b64 = Image.frombuffer('RGB', (w, h), tempImg.astype(np.int8), 'raw', 'RGB', 0, 1)
    encode_image_as_html(outfile, b64)
    #outfile.write('<img src="track_extents_white.png"><svg height="128" width="128" style="position:absolute;top:2px;left:138px"><circle cx="' + str(results_lon * 128 / 15 + 7) + '" cy="' + str(results_lat * 128 / 15 + 7) + '" r="4" stroke="black" stroke-width="1" fill="red" /></svg>')
    #write_html_image_tensor_gray_overlay(outfile, latlon_softmax.reshape((15, 15))*255, 9, "", "", 1.0)
    #outfile.write('<svg height="128" width="128" style="position:absolute;top:2px;left:138px"><circle cx="' + str(gt_lon * 128 / 15 + 7) + '" cy="' + str(gt_lat * 128 / 15 + 7) + '" r="4" stroke="black" stroke-width="1" fill="yellow" /></svg>')
    write_steering_line(outfile, -steering_regress * 1, 'rgb(240, 55, 40)', 7)
    write_steering_line(outfile, -(steering_gt - 7) * 7, 'rgb(40, 255, 40)', 5)
    write_steering_line(outfile, -(result_steering - 7) * 7)
    # write_vertical_meter(outfile, throttle_gt, total, 'rgb(40, 255, 40)')
    # write_vertical_meter(outfile, throttle_net, total)
    outfile.write('</span>')

    # Draw *steering* softmax distribution to a png
    draw_softmax_distribution(outfile, 'Steer softmax', steering_softmax, steering_gt)

    # Draw *throttle* softmax distribution to a png
    draw_softmax_distribution(outfile, 'Throttle softmax', throttle_softmax, throttle_gt, True)

    # Draw *pulse* softmax distribution to a png
    # soft_img = Image.new('RGBA', (128, 32), (0, 0, 0, 64))
    # draw = ImageDraw.Draw(soft_img)
    # soft_size = pulse_softmax.shape[0]
    # scale = (soft_img.width / soft_size)
    # for i in range(soft_size):
    #     fill_color = (255, 255, 255, 255)
    #     # if i == throttle_gt: fill_color = (0, 255, 0, 255)
    #     prob = pulse_softmax[i]
    #     draw.rectangle(
    #         [i * scale, soft_img.height - round(prob * soft_img.height), i * scale + scale - 2, soft_img.height],
    #         fill_color)
    # outfile.write('<div style="position:relative;padding-bottom:4px">')
    # encode_image_as_html(outfile, soft_img, 'PNG', 'style="position:absolute"')
    # outfile.write('Odometer softmax</div><br/>')

    # Print out throttle, steering, and odometer values.
    outfile.write('T: ' + str(throttle_gt) + '&nbsp;&nbsp; NT: ' + str(result_throttle) + '<br/>')
    outfile.write('S: ' + str(steering_gt) + '&nbsp;&nbsp; NS: ' + str(result_steering) + '<br/>')
    outfile.write('regress: ' + str(int(steering_regress)) + ' ' + str(int(throttle_regress)) + '<br/>')
    # outfile.write('ent: ' + str(pulse_entropy))
    outfile.write('</td>')


def write_html(output_path, test_data, results_steering, results_throttle, graph, sess, steering_softmax_batch, throttle_softmax_batch, results_steering_regress, results_throttle_regress, net_model):
    # copyfile("track_extents_white.png", os.path.join(output_path, "track_extents_white.png"))
    image_count = len(results_steering)
    image_count = min(1000, image_count)
    outfile = open(os.path.join(output_path, "debug.html"), "w")
    outfile.write("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>title</title>
    <style type="text/css">
      body{
        font-family:monospace;
      }
      ul.listbutton li span{
        color: #475dba;
        float: left;
        display:inline-block;
        background-color:#ebebeb;
        border:1px solid #b3cbef;
        margin-right: 4px;
        padding:4px;
        text-align: center;
        line-height: 24px;
        text-decoration: none;
        cursor:pointer;
        user-select: none;
      }
      ul.listbutton li span:hover {
        text-decoration: none;
        color: #000000;
        background-color: #33B5E5;
      }
      ul.listbutton li span:active {
        text-decoration: none;
        color: #000000;
        background-color: #f3B5E5;
      }
    </style>
  </head>
  <body onload="myMove()">
    <div id="topdiv">
      <br/>
      <ul id="buttons" class="listbutton" style="list-style-type:none;padding:0;margin:0;">
        <li><span id="listbutton0" onclick="listButtonClick(-1)">None</span></li>
        """)

    for i in xrange(num_conv_debugs):
        outfile.write('<li><span id="listbutton' + str(i + 1) + '" onclick="listButtonClick(' + str(i) + ')">' + str(i) + '</span></li>')

    outfile.write("""
      </ul>
      <br style="clear:both" />
    </div>
    <br/>
    <table id="mainTable" onclick="tableClick()" style="border-collapse:collapse;background: #333;font-family: monospace;">
                  """)
    outfile.write('<tr>')

    # variables = graph.get_collection('htmlize')
    variables = graph.get_collection(tf.GraphKeys.GLOBAL_VARIABLES)

    name_to_var = {}
    for var in variables:
        if var.name:
            name_to_var[var.name] = var

    # Make a giant table of all images and info from the neural net.
    for i in xrange(image_count):
        if (i % 16) == 0:
            outfile.write('</tr>')
            outfile.write('<tr>')
        write_html_image(outfile, results_steering[i], results_throttle[i], test_data, net_model.width, net_model.height, "blank", i,
                         steering_softmax_batch[i], throttle_softmax_batch[i], results_steering_regress[i], results_throttle_regress[i])
    outfile.write('</tr>')
    outfile.write('</table><br/><br/>')

    outfile.write("<div style='position:relative'>")
    write_html_image(
        outfile, results_steering[0], results_throttle[0], test_data, net_model.width, net_model.height, "blank2", 0,
        steering_softmax_batch[0], throttle_softmax_batch[0], results_steering_regress[0], results_throttle_regress[0])
    outfile.write('</div>')
    # write_html_image_RGB(outfile, all_xs[0], width, height)
    # viz = sess.run(W)
    # write_html_image_RGB(outfile, viz, width, height)

    results = sess.run(name_to_var['shared_conv/W_conv1:0'])
    results = results.transpose(3,0,1,2) # different because RGB
    write_html_image_tensor_gray(outfile, results, True, 4)
    results = sess.run(name_to_var['shared_conv/W_conv2:0'])
    results = results.transpose(2,3,0,1)
    write_html_image_tensor_gray(outfile, results, False, 4)
    # results = sess.run(name_to_var['shared_cnn/W_fc1:0'])
    # results = results.transpose(1,0)
    # results = results.reshape((NNModel.fc1_num_outs, NNModel.l4_num_convs, NNModel.heightD32, NNModel.widthD32))
    # results = results.transpose(0, 2, 1, 3)
    # results = results.reshape((NNModel.fc1_num_outs, NNModel.heightD32, NNModel.l5_num_convs * NNModel.widthD32))
    # write_html_image_tensor_gray(outfile, results, False)
    # # write_html_histogram(outfile, results)
    # results = sess.run(name_to_var['W_fc2:0'])
    # write_html_image_tensor_gray(outfile, results, False)
    # results = sess.run(name_to_var['W_fc3:0'])
    # write_html_image_tensor_gray(outfile, results, False)

    # results = sess.run(net_model.h_pool5_flat, feed_dict=test_data.FeedDict(net_model))
    # write_html_image_tensor_gray(outfile, results, False)

    # results = sess.run(h_pool1, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # # results = results.transpose(0,3,1,2)
    # results = results.transpose(3,0,1,2)
    # write_html_image_tensor_gray(outfile, results, False, 2)
    # results = sess.run(h_pool2, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # # results = results.transpose(0,3,1,2)
    # results = results.transpose(3,0,1,2)
    # write_html_image_tensor_gray(outfile, results, False, 2)
    # results = sess.run(h_pool3, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # results = results.transpose(3,0,1,2)
    # write_html_image_tensor_gray(outfile, results, False, 2)
    # results = sess.run(h_pool4, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # results = results.transpose(3,0,1,2)
    # write_html_image_tensor_gray(outfile, results, False, 2)
    # results = sess.run(h_pool5, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # results = results.transpose(3,0,1,2)
    # write_html_image_tensor_gray(outfile, results, False, 2)
    # results = sess.run(y_conv, feed_dict={x: all_xs[0:1], y_: all_ys[0:1], keep_prob: 1.0})
    # write_html_image_tensor_gray(outfile, results, False, 8)
    outfile.write("""
    WRITTEN!!!!

  <script>
    var button = document.createElement("input");
    button.type = "button";
    button.value = "Animate";
    button.addEventListener ("click", tableClick);
    document.body.insertBefore(button, document.getElementById("mainTable"));

    var animating = false;
    var pos = 0;
    var elemCount = NUM_IMAGES;
    var timerID = 0;
    function pad(num, size) {
      var s = "000000000" + num;
      return s.substr(s.length-size);
    }
    function myMove() {
      if (timerID == 0) {
        timerID = setInterval(frame, 133);
      }
      function frame() {
        if (!animating) {
          return;
        }
        if (pos == elemCount * 4) {
          clearInterval(timerID);
          timerID = 0;
        } else {
          pos++;
          var modA = pos % elemCount
          var modB = (pos + 1) % elemCount
          //console.log(" " + pos + "   td" + pad(modA, 5) + "    " + "td" + pad(modB, 5));
          var elem = document.getElementById("td" + pad(modA, 5));
          elem.style.display = "none";
          elem = document.getElementById("td" + pad(modB, 5));
          elem.style.display = "table-cell";
        }
      }
    }
    function tableClick() {
      if (animating) {
        animating = !animating;
        clearInterval(timerID);
        timerID = 0;
        pos = 0;
        for (i = 0; i < elemCount; i++) {
          elem = document.getElementById("td" + pad(i, 5));
          elem.style.display = "table-cell";
        }
      } else {
        pos = 0;
        for (i = 0; i < elemCount; i++) {
          elem = document.getElementById("td" + pad(i, 5));
          elem.style.display = "none";
        }
        animating = !animating;
        myMove();
      }
    }
    function listButtonClick(index) {
      var ei;
      for (ei = 0; ei < elemCount; ei++) {
        var i;
        for (i = 0; i < num_conv_debugs; i++) {
          var elems = document.getElementById("pixels" + i + "_" + ei);
          elems.style.display = "none";
          if (i == index) elems.style.display = "block";
        }
      }
      for (i = -1; i < num_conv_debugs; i++) {
        var button = document.getElementById("listbutton" + (i + 1));
        if (i == index) {
          button.style.backgroundColor = "#2385b5";
        } else {
          button.style.backgroundColor = "";
        }
      }
    }
  </script>

  </body>
</html>
                  """.replace("NUM_IMAGES", str(image_count)).replace("num_conv_debugs", str(num_conv_debugs)))
    outfile.close()
