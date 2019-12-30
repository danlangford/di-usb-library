from infinity import InfinityBase
import yaml
import pafy
import vlc
from six.moves import input


if __name__ == '__main__':

    import time

    types = {'1': "Figure", '2': "Play Set", '3': "Game Disc", '4': "Power Disc, Ability", '5': "Power Disc, Toy",
             '6': "Power Disc, Customization"}
    current_tags = set([])
    data = yaml.load(open('../data.yaml', 'r'), Loader=yaml.FullLoader)
    vlc_instance = vlc.Instance("--aout=alsa")
    player = vlc_instance.media_player_new()

    print("hello")
    base = InfinityBase()


    def future_print(s):
        print(s)


    def tags_changed():
        print("tags changed")
        base.get_all_tags(handle_tags)


    def handle_tags(positions):
        global current_tags
        global data
        global vlc_instance
        global player

        data = yaml.load(open('../data.yaml', 'r'), Loader=yaml.FullLoader)

        base.flash_color(1, 200, 200, 200)

        # print(positions)
        all_tags = set('_'.join(map(str, tag)) for tags in positions.values() for tag in tags)
        # print("current_tags", current_tags)
        print(("all_tags", all_tags))
        for t in all_tags:
            if not any(t == x['id'] for x in data['tags']):
                desc = input("Describe that:")
                mytype = types[input(str(types))]
                data['tags'].append(dict({'id': t, 'desc': desc, 'type': mytype}))
                yaml.dump(data, open('../data.yaml', 'w'))

        new_tags = all_tags - current_tags
        print(("new_tags", new_tags))
        current_tags = all_tags
        for new in new_tags:
            x = next(item for item in data['tags'] if new == item['id'])
            url = pafy.new(x['yt']).getbest().url
            player.set_media(vlc_instance.media_new(url))
            player.play()
            # player.set_fullscreen(True)


    base.onTagsChanged = tags_changed
    # base.onTagsChanged = futurePrint

    base.connect()
    print("connected")

    base.get_all_tags(future_print)

    print("colors")
    base.set_color(1, 0, 0, 0)
    base.set_color(2, 0, 0, 0)
    base.set_color(3, 0, 0, 0)

    base.fade_color(1, 200, 0, 0)
    base.fade_color(2, 0, 200, 0)
    base.fade_color(3, 0, 0, 200)

    time.sleep(1)

    base.flash_color(1, 0, 0, 0)
    base.flash_color(2, 0, 0, 0)
    base.flash_color(3, 0, 0, 0)

    print("Try adding and removing figures and discs to/from the base. CTRL-C to quit")
    while True:
        pass
