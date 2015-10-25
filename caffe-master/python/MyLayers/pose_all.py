import unittest
import tempfile
import os
import numpy

import caffe

class pose_all(caffe.Layer):
    """A layer that initialize messages for recurrent belief propagation"""

    def setup(self, bottom, top):
        self.nScene = 5
        self.nAction = 7
        self.nPeople = 14
        self.K_ = 0;
        self.bottom_batchsize = 0
        self.unitlen = 0
        self.output_num = 0
        self.bottom_batchsize = 0
        self.top_batchsize = 0
        self.top_output_num = 0
        self.top_shape = []
        self.label_stop = []
        self.count = 0
    
    def reshape(self, bottom, top):
        # have one input one output, initialize messages for each node in the graphical model
        bottom_shape = bottom[1].data.shape
        self.bottom_batchsize = bottom_shape[0]/self.nPeople   #-->numbers of frame in a batch
        labels=bottom[1].data
        label_stop = numpy.ones([self.bottom_batchsize])
        count = 0
        for i in range(0,self.bottom_batchsize):
            for j in range(0,self.nPeople):
                if labels[i*self.nPeople+j] == 0:
                    label_stop[i] = j
                    count += j
                    break

        self.count = count
        self.label_stop = label_stop
        self.top_batchsize = self.bottom_batchsize
        self.top_output_num = bottom[0].data.shape[1]
        top[0].reshape(self.top_batchsize, self.top_output_num)


    def forward(self, bottom, top):
        label_stop = self.nPeople*numpy.ones([self.bottom_batchsize])
        labels = bottom[1].data.copy()
        for i in range(0,self.bottom_batchsize):
            for j in range(0,self.nPeople):
                if labels[i*self.nPeople+j] == 0:
                    label_stop[i] = j
                    break
        self.label_stop = label_stop

        for f in range(0,self.bottom_batchsize):
            pose_f = bottom[0].data[f*self.nPeople:(f+1)*self.nPeople]
            pose_all_f=pose_f[:self.label_stop[f]]
            top[0].data[f] = pose_all_f.sum(axis = 0)/self.label_stop[f]
                 

    def backward(self, top, propagate_down, bottom):
        pass

def python_net_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write("""name: 'pythonnet' force_backward: true
        input: 'data' input_shape { dim: 10 dim: 9 dim: 8 }
        layer { type: 'Python' name: 'one' bottom: 'data' top: 'one'
          python_param { module: 'test_python_layer' layer: 'SimpleLayer' } }
        layer { type: 'Python' name: 'two' bottom: 'one' top: 'two'
          python_param { module: 'test_python_layer' layer: 'SimpleLayer' } }
        layer { type: 'Python' name: 'three' bottom: 'two' top: 'three'
          python_param { module: 'test_python_layer' layer: 'SimpleLayer' } }""")
        return f.name

class TestPythonLayer(unittest.TestCase):
    def setUp(self):
        net_file = python_net_file()
        self.net = caffe.Net(net_file, caffe.TRAIN)
        os.remove(net_file)

    def test_forward(self):
        x = 8
        self.net.blobs['data'].data[...] = x
        self.net.forward()
        for y in self.net.blobs['three'].data.flat:
            self.assertEqual(y, 10**3 * x)

    def test_backward(self):
        x = 7
        self.net.blobs['three'].diff[...] = x
        self.net.backward()
        for y in self.net.blobs['data'].diff.flat:
            self.assertEqual(y, 10**3 * x)

    def test_reshape(self):
        s = 4
        self.net.blobs['data'].reshape(s, s, s, s)
        self.net.forward()
        for blob in self.net.blobs.itervalues():
            for d in blob.data.shape:
                self.assertEqual(s, d)
