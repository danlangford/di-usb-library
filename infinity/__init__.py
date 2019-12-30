from __future__ import absolute_import
from __future__ import print_function

import threading
from collections import defaultdict

import hid
from six.moves import map


class InfinityComms(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.device = self.init_base()
        self.finish = False
        self.pending_requests = {}
        self.message_number = 0
        self.observers = []

    def init_base(self):
        device = hid.Device(0x0e6f, 0x0129)
        device.nonblocking = False
        return device

    def run(self):
        while not self.finish:
            line = self.device.read(32, 3000)
            if not len(line):
                continue
            fields = [ord(c) for c in line]
            if fields[0] == 0xaa:
                length = fields[1]
                message_id = fields[2]
                if message_id in self.pending_requests:
                    deferred = self.pending_requests[message_id]
                    deferred.resolve(fields[3:length + 2])
                    del self.pending_requests[message_id]
                else:
                    self.unknown_message(line)
            elif fields[0] == 0xab:
                self.notify_observers()
            else:
                self.unknown_message(line)

    def add_observer(self, obj):
        self.observers.append(obj)

    def notify_observers(self):
        for obs in self.observers:
            obs.tags_updated()

    def unknown_message(self, fields):
        print(("UNKNOWN MESSAGE RECEIVED ", fields))

    def next_message_number(self):
        self.message_number = (self.message_number + 1) % 256
        return self.message_number

    def send_message(self, command, data=[]):
        message_id, message = self.construct_message(command, data)
        result = Deferred()
        self.pending_requests[message_id] = result
        print(("message" + str(message)))
        self.device.write(message)
        return Promise(result)

    def construct_message(self, command, data):
        message_id = self.next_message_number()
        command_body = [command, message_id] + data
        command_length = len(command_body)
        command_bytes = [0x00, 0xff, command_length] + command_body
        message = [0x00] * 33
        checksum = 0
        for (index, byte) in enumerate(command_bytes):
            message[index] = byte
            checksum = checksum + byte
        message[len(command_bytes)] = checksum & 0xff
        return message_id, "".join(map(chr, message))


class Deferred(object):
    def __init__(self):
        self.event = threading.Event()
        self.rejected = False
        self.result = None

    def resolve(self, value):
        self.rejected = False
        self.result = value
        self.event.set()

    def wait(self):
        while not self.event.is_set():
            self.event.wait(3)


class Promise(object):
    def __init__(self, deferred):
        self.deferred = deferred

    def then(self, success, failure=None):
        def task():
            try:
                self.deferred.wait()
                result = self.deferred.result
                success(result)
            except Exception as ex:
                if failure:
                    failure(ex)
                else:
                    print(ex.message)

        threading.Thread(target=task).start()
        return self

    def wait(self):
        self.deferred.wait()


class InfinityBase(object):
    def __init__(self):
        self.comms = InfinityComms()
        self.comms.add_observer(self)
        self.onTagsChanged = None

    def connect(self):
        self.comms.daemon = True
        self.comms.start()
        self.activate()

    def disconnect(self):
        self.comms.finish = True

    def activate(self):
        activate_message = [0x28, 0x63, 0x29, 0x20, 0x44,
                            0x69, 0x73, 0x6e, 0x65, 0x79,
                            0x20, 0x32, 0x30, 0x31, 0x33]
        self.comms.send_message(0x80, activate_message)

    def tags_updated(self):
        if self.onTagsChanged:
            self.onTagsChanged()

    def get_all_tags(self, then):
        def query_all_tags(idx):
            if len(idx) == 0:
                then(dict())
            number_to_get = [0] * len(idx)
            tag_by_platform = defaultdict(list)
            for (platform, tagIdx) in idx:
                def file_tag(platform):
                    def inner(tag):
                        tag_by_platform[platform].append(tag)
                        number_to_get.pop()
                        if len(number_to_get) == 0:
                            then(dict(tag_by_platform))

                    return inner

                self.get_tag(tagIdx, file_tag(platform))

        self.get_tag_idx(query_all_tags)

    def get_tag_idx(self, then):
        def parse_index(bytez):
            values = [((byte & 0xF0) >> 4, byte & 0x0F) for byte in bytez if byte != 0x09]
            then(values)

        self.comms.send_message(0xa1).then(parse_index)

    def get_tag(self, idx, then):
        self.comms.send_message(0xb4, [idx]).then(then)

    def set_color(self, platform, r, g, b):
        self.comms.send_message(0x90, [platform, r, g, b])

    def fade_color(self, platform, r, g, b):
        self.comms.send_message(0x92, [platform, 0x10, 0x02, r, g, b])

    def flash_color(self, platform, r, g, b):
        self.comms.send_message(0x93, [platform, 0x02, 0x02, 0x06, r, g, b])
