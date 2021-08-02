import numpy as np
import h5py;
import threading
import datetime
import trackpy as tp
import time

from pynta import Q_

from zmq.backend import device
from pynta.model.cameras.dummy_camera import Camera;

from multiprocessing import Process, Queue
import queue 

def start_free_run(camera, frame_processor):
        """ Starts continuous acquisition from the camera, but it is not being saved. This method is the workhorse
        of the program. While this method runs on its own thread, it will broadcast the images to be consumed by other
        methods. In this way it is possible to continuously save to hard drive, track particles, etc.
        """

        #self.logger.info('Starting a free run acquisition')
        first = True
        i = 0  # Used to keep track of the number of frames
        #self.camera.configure(self.config['camera'])
        #self._stop_free_run.clear()
        #t0 = time.time()
        #self.free_run_running = True
        #self.logger.debug('First frame of a free_run')
        camera.set_acquisition_mode(camera.MODE_CONTINUOUS)
        camera.trigger_camera()  # Triggers the camera only once
        start = time.time()
        while True: #not self._stop_free_run.is_set():
            try:
                data = camera.read_camera()
                if not data:
                    print("no new frames, shouldn't happen as read_camera blocks?")
                    continue
                #self.logger.debug('Got {} new frames'.format(len(data)))
                #print("got {} new frames".format(len(data)))
                if i % 100 == 0:
                    end = time.time()
                    print("frametime {}".format((end-start)/100))
                    start=end
                for img in data:
                    i += 1
                    frame_processor(img)
                if i == 20000:
                    break    
                    
            except KeyboardInterrupt:
                break
                #self.publisher.publish('free_run', [time.time(), img])
            #self.fps = round(i / (time.time() - t0))
            #self.temp_image = img
        #self.free_run_running = False
        #self.camera.stopAcq()
    

class DataPipeline:
    def __init__(self, callables_list = []) -> None:
        self.callables_list = callables_list
    
    def append_node(self, callable):
        self.callables_list.append(callable)
    
    def apply(self, data):
        for c in self.callables_list:
            # print("applying {} to {}".format(c, data))
            data = c(data)
            if data is None:
                return None
        return data
    
    def __call__(self, data):
        self.apply(data)

class ImageBuffer:
    def __init__(self, buffer = None) -> None:
        self.buffer = buffer
    def __call__(self, image):
        if self.buffer is None:
            # print("setting buffer as it was empty")
            self.buffer = np.copy(image)
        else:
            np.copyto(self.buffer, image, casting='no')
        return image

class Track:
    def __init__(self, diameter = 11) -> None:
        self.diameter = diameter
    def __call__(self, image):
        return tp.locate(image, self.diameter)

class SaveImageToHDF5:
    def __init__(self, aqcuisition_grp, stride = 1):
        #self.dataset_writer = dataset_writer
        self.stride = stride-1
        self.counter = 0
        self.dataset_writer = aqcuisition_grp["Image"]#.create_dataset("Image", shape=(0,)+device.get_size(), dtype=device.data_type, maxshape=(None,)+device.get_size(), chunks=(1,)+device.get_size(), compression='gzip')
        self.dataset_writer.attrs["stride"] = stride
        self.dataset_writer.attrs["creation"]  = str(datetime.datetime.utcnow())
    def __call__(self, image):
        if self.counter == 0:
            # print("writting image to file..")
            #self.dataset_writer.send(image)
            dsize = self.dataset_writer.shape
            self.dataset_writer.resize((dsize[0]+1,) + dsize[1:])
            self.dataset_writer[-1,:] = image
        # else:
        #     print("Skipping image writting..")
        self.counter = self.counter + 1 if self.counter < self.stride else 0
        return image

class Batch:
    def __init__(self, number) -> None:
        self.number = number
        self.buffer = None
        self.index = 0
    def __call__(self, data):
        if self.buffer is None:
            self.buffer = np.zeros((self.number,)+data.shape, data.dtype)
        self.buffer[self.index,:] = data
        self.index += 1
        if self.index >= self.number:
            self.index = 0
            return self.buffer
        else:
            return None

class ComputeAndSaveTracksToHDF5:
    def __init__(self, aqcuisition_grp, diameter = 11):
        #self.dataset_writer = dataset_writer
        self.batching = 1024
        self.write_index = 0
        self.frame = 0
        self.diameter = diameter

        self.grp = aqcuisition_grp.create_group("Tracks")
        self.grp.attrs["diameter"] = self.diameter
        self.grp.attrs["creation"]  = str(datetime.datetime.utcnow())

        #self.locations_dataset = aqcuisition_grp.create_dataset("locations", shape=(8,self.batching), dtype=np.float32, maxshape=(8,None), chunks=(8, self.batching), compression='gzip')
        self.x_dataset = self.grp.create_dataset("x", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.y_dataset = self.grp.create_dataset("y", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.frame_dataset = self.grp.create_dataset("frames", shape=(self.batching,), dtype=np.uint64, maxshape=(None,), chunks=(self.batching,), compression='gzip')
        
    def __call__(self, image):
        locations = tp.locate(image.astype(np.uint8), self.diameter, engine = 'numba', characterize=True)
        row_count = len(locations.index)
        #print("found {} particles on frame {}".format(row_count, self.frame))
        #todo: handle row_count > 
        old_size = self.x_dataset.shape[0]
        #print("old size is {}".format(old_size))
        while row_count + self.write_index > old_size:
            self.x_dataset.resize((old_size+self.batching,))
            self.y_dataset.resize((old_size+self.batching,))
            self.frame_dataset.resize((old_size+self.batching,))
            old_size += self.batching
        #print("trying to write x={}".format(locations["x"]))
        #print(locations["x"].shape)
        self.x_dataset[self.write_index:self.write_index+row_count] = locations["x"]
        self.y_dataset[self.write_index:self.write_index+row_count] = locations["y"]
        self.frame_dataset[self.write_index:self.write_index+row_count] = np.ones(row_count ,dtype= np.uint64)*self.frame
        self.write_index += row_count
        self.frame += 1
        return locations

def track_from_q(in_queue, out_queue, diameter):
    while True:
        data = in_queue.get()
        if data is None:
            print("data was none, exiting")
            #in_queue.task_done()
            return
        else:
            #print("fetching frame") 
            df = tp.locate(data, diameter, characterize=True)
            out_queue.put(df)
            #in_queue.task_done()

class ComputeAndSaveTracksToHDF5_WithMP:
    def __init__(self, aqcuisition_grp, diameter = 11):
        #self.dataset_writer = dataset_writer
        self.batching = 1024
        self.write_index = 0
        self.frame = 0
        self.diameter = diameter

        self.grp = aqcuisition_grp.create_group("Tracks")
        self.grp.attrs["diameter"] = self.diameter
        self.grp.attrs["creation"]  = str(datetime.datetime.utcnow())

        #self.locations_dataset = aqcuisition_grp.create_dataset("locations", shape=(8,self.batching), dtype=np.float32, maxshape=(8,None), chunks=(8, self.batching), compression='gzip')
        self.x_dataset = self.grp.create_dataset("x", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.y_dataset = self.grp.create_dataset("y", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.frame_dataset = self.grp.create_dataset("frames", shape=(self.batching,), dtype=np.uint64, maxshape=(None,), chunks=(self.batching,), compression='gzip')
        self.in_queues = []
        self.out_queues = []
        self.processes = []
        self.queued_frames =0
        self.np = 12
        for i in range(0, self.np):
            in_queue = Queue()
            out_queue = Queue()
            self.in_queues.append(in_queue)
            self.out_queues.append(out_queue)
            p = Process(target=track_from_q, args=(in_queue,out_queue,self.diameter), daemon=True);
            p.daemon = True
            p.start()
            self.processes.append(p)
        self.write_p = 0
        self.read_p = 0
    
    def __del__(self) -> None:
        for q in self.in_queues:
            q.put(None)
        print("flshing...")
        while self.frame < self.queued_frames:
            self.handle_next(True)
        for p in self.processes:
            p.terminate()
        for p in self.processes:
            #p.terminate()
            print("joining...")
            p.join()
    
    def __call__(self, image):
        self.in_queues[self.write_p].put(image)
        self.queued_frames += 1
        self.write_p = self.write_p + 1 if self.write_p < self.np-1 else 0
        return self.handle_next()

    def handle_next(self, wait = False):
        try:
            locations = self.out_queues[self.read_p].get(wait)
        except queue.Empty:
            #print("not ready yet")
            return None
        self.read_p = self.read_p + 1 if self.read_p < self.np-1 else 0
        #print("tracked frame {}".format(self.frame))
        row_count = len(locations.index)
        #print("found {} particles on frame {}".format(row_count, self.frame))
        #todo: handle row_count > 
        old_size = self.x_dataset.shape[0]
        #print("old size is {}".format(old_size))
        while row_count + self.write_index > old_size:
            self.x_dataset.resize((old_size+self.batching,))
            self.y_dataset.resize((old_size+self.batching,))
            self.frame_dataset.resize((old_size+self.batching,))
            old_size += self.batching
        #print("trying to write x={}".format(locations["x"]))
        #print(locations["x"].shape)
        self.x_dataset[self.write_index:self.write_index+row_count] = locations["x"]
        self.y_dataset[self.write_index:self.write_index+row_count] = locations["y"]
        self.frame_dataset[self.write_index:self.write_index+row_count] = np.ones(row_count ,dtype= np.uint64)*self.frame
        self.write_index += row_count
        self.frame += 1
        return locations

class ComputeAndSaveTracksToHDF5Batched:
    def __init__(self, aqcuisition_grp, diameter = 11):
        #self.dataset_writer = dataset_writer
        self.batching = 1024
        self.write_index = 0
        self.frame = 0
        self.diameter = diameter

        self.grp = aqcuisition_grp.create_group("Tracks")
        self.grp.attrs["diameter"] = self.diameter
        self.grp.attrs["creation"]  = str(datetime.datetime.utcnow())

        #self.locations_dataset = aqcuisition_grp.create_dataset("locations", shape=(8,self.batching), dtype=np.float32, maxshape=(8,None), chunks=(8, self.batching), compression='gzip')
        self.x_dataset = self.grp.create_dataset("x", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.y_dataset = self.grp.create_dataset("y", shape=(self.batching,), dtype=np.float32, maxshape=(None,), chunks=(self.batching,))
        self.frame_dataset = self.grp.create_dataset("frames", shape=(self.batching,), dtype=np.uint64, maxshape=(None,), chunks=(self.batching,), compression='gzip')
        
    def __call__(self, image):
        locations = tp.batch(image, self.diameter, processes='auto', characterize=False)
        row_count = len(locations.index)
        #print(locations)
        #print("found {} particles on frame {}".format(row_count, self.frame))
        #todo: handle row_count > 
        old_size = self.x_dataset.shape[0]
        #print("old size is {}".format(old_size))
        while row_count + self.write_index > old_size:
            self.x_dataset.resize((old_size+self.batching,))
            self.y_dataset.resize((old_size+self.batching,))
            self.frame_dataset.resize((old_size+self.batching,))
            old_size += self.batching
        #print("trying to write x={}".format(locations["x"]))
        #print(locations["x"].shape)
        self.x_dataset[self.write_index:self.write_index+row_count] = locations["x"]
        self.y_dataset[self.write_index:self.write_index+row_count] = locations["y"]
        self.frame_dataset[self.write_index:self.write_index+row_count] = locations["frame"]+self.frame
        self.write_index += row_count
        self.frame += image.shape[0]
        return locations

class FileWrangler:
    def __init__(self, filename) -> None:
        self.file = h5py.File(filename if filename.endswith('.hdf5') else filename + '.hdf5','w',  libver='latest')         
        self.file.attrs["creation"] = str(datetime.datetime.utcnow())
    
    def start_new_aquisition(self, device):
        print("starting aq of {}".format(device))
        device_grp = self.file.require_group(str(device))
        aquisition_nr = len(device_grp.keys())
        grp = device_grp.create_group("Acquisition_{}".format(aquisition_nr))
        grp.create_dataset("Image", shape=(0,)+device.get_size(), dtype=device.data_type, maxshape=(None,)+device.get_size(), chunks=(1,)+device.get_size(), compression='gzip')
        return grp

if __name__ == '__main__':
    f = FileWrangler("test2")
    cam = Camera(0)
    print(cam.get_exposure())
    cam.set_exposure(Q_('0.01s'))
    print(cam.get_exposure())
    aqcuisition = f.start_new_aquisition(cam)
    tp.quiet()
    #batched trackpy, too slow only 30fps ish
    #pipeline = DataPipeline([Batch(32), ComputeAndSaveTracksToHDF5Batched(aqcuisition)])
    #only save images (fast enough) ~1000 fps
    #pipeline = DataPipeline([SaveImageToHDF5(aqcuisition)])
    #unbatched trackpy, about 200fps
    #good news: cpu bound
    pipeline = DataPipeline([SaveImageToHDF5(aqcuisition), ComputeAndSaveTracksToHDF5_WithMP(aqcuisition)])
    start_free_run(cam, pipeline)
    print("done!")
    del pipeline #why?
    print("really done")

# file[name].resize(new_size)
# file[name][idx] = data


# queue