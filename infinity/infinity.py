import threading
from collections import defaultdict
import hid
import tagids
import tagurls
import os
import yaml
import pafy
import vlc


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
                    deferred.resolve(fields[3:length+2])
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
            obs.tagsUpdated()

    def unknown_message(self, fields):
        print("UNKNOWN MESSAGE RECEIVED ", fields)

    def next_message_number(self):
        self.message_number = (self.message_number + 1) % 256
        return self.message_number

    def send_message(self, command, data=[]):
        message_id, message = self.construct_message(command, data)
        result = Deferred()
        self.pending_requests[message_id] = result
        print("message"+str(message))
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
        return (message_id, "".join(map(chr,message)))


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
        activate_message = [0x28,0x63,0x29,0x20,0x44,
                            0x69,0x73,0x6e,0x65,0x79,
                            0x20,0x32,0x30,0x31,0x33]
        self.comms.send_message(0x80, activate_message)

    def tagsUpdated(self):
        if self.onTagsChanged:
            self.onTagsChanged()

    def getAllTags(self, then):
        def queryAllTags(idx):
            if len(idx) == 0:
                then(dict())
            number_to_get = [0] * len(idx)
            tag_by_platform = defaultdict(list)
            for (platform, tagIdx) in idx:
                def fileTag(platform):
                    def inner(tag):
                        tag_by_platform[platform].append(tag)
                        number_to_get.pop()
                        if len(number_to_get) == 0:
                            then(dict(tag_by_platform))
                    return inner
                self.getTag(tagIdx, fileTag(platform))
        self.getTagIdx(queryAllTags)

    def getTagIdx(self, then):
        def parseIndex(bytes):
            values = [ ((byte & 0xF0) >> 4, byte & 0x0F ) for byte in bytes if byte != 0x09]
            then(values)
        self.comms.send_message(0xa1).then(parseIndex)

    def getTag(self, idx, then):
        self.comms.send_message(0xb4, [idx]).then(then)

    def setColor(self, platform, r, g, b):
        self.comms.send_message(0x90, [platform, r, g, b])

    def fadeColor(self, platform, r, g, b):
        self.comms.send_message(0x92, [platform, 0x10, 0x02, r, g, b])

    def flashColor(self, platform, r, g, b):
        self.comms.send_message(0x93, [platform, 0x02, 0x02, 0x06, r, g, b])


if __name__ == '__main__':

    import time
    types = {'1': "Figure", '2': "Play Set", '3': "Game Disc", '4':"Power Disc, Ability", '5': "Power Disc, Toy", '6': "Power Disc, Customization"}
    current_tags = set([])
    data = yaml.load(file('data.yaml', 'r'), Loader=yaml.FullLoader)
    Instance = vlc.Instance()
    player = Instance.media_player_new()

    print("hello")
    base = InfinityBase()

    def future_print(s):
        print(s)

    def tags_changed():
        print("tags changed")
        base.getAllTags(handle_tags)

    def handle_tags(positions):
        global current_tags
        global data
        global Instance
        global player

        data = yaml.load(file('data.yaml', 'r'), Loader=yaml.FullLoader)

        base.flashColor(1, 200, 200, 200)

        #print(positions)
        all_tags = set('_'.join(map(str,tag)) for tags in positions.values() for tag in tags)
        #print("current_tags", current_tags)
        print("all_tags", all_tags)
        for t in all_tags:
            if not any(t == x['id'] for x in data['tags']):
                desc = raw_input("Describe that:")
                type = types[raw_input(str(types))]
                data['tags'].append(dict({'id': t, 'desc': desc, 'type':type}))
                yaml.dump(data, file('data.yaml', 'w'))

        new_tags = all_tags - current_tags
        print("new_tags",new_tags)
        current_tags = all_tags
        for new in new_tags:
        #     os.system("open \""+tagurls.LISTING[tagids.LISTING[new]]+"\"")
            player.stop()
            x = next(item for item in data['tags'] if new == item['id'])
            url = pafy.new(x['yt']).getbest().url
            Media = Instance.media_new(url)
            Media.get_mrl()
            player.set_media(Media)
            player.play()
            player.set_fullscreen(True)


    base.onTagsChanged = tags_changed
    #base.onTagsChanged = futurePrint

    base.connect()
    print("connected")

    base.getAllTags(future_print)

    print("colors")
    base.setColor(1, 0, 0, 0)
    base.setColor(2, 0, 0, 0)
    base.setColor(3, 0, 0, 0)

    base.fadeColor(1, 200, 0, 0)
    base.fadeColor(2, 0, 200, 0)
    base.fadeColor(3, 0, 0, 200)

    time.sleep(1)

    base.flashColor(1, 0, 0, 0)
    base.flashColor(2, 0, 0, 0)
    base.flashColor(3, 0, 0, 0)

    print("Try adding and removing figures and discs to/from the base. CTRL-C to quit")
    while True:
        pass

