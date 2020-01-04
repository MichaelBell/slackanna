import cherrypy
import simplejson
import requests
import re

with open("token") as file:
  TOKEN=file.read().strip()

class Words:
    def __init__(self):
        self.diction = []
        self.sorted_diction = {}
        f = open('/usr/share/dict/american-english')
        for l in f:
            w = l.strip().upper()
            self.diction.append(w)
            sw = "".join(sorted(w))
            if sw in self.sorted_diction: self.sorted_diction[sw].append(w)
            else: self.sorted_diction[sw] = [w]

    def anagram(self, word):
        word = word.upper()
        sw = "".join(sorted(word))
        if sw not in self.sorted_diction: return ""
        d = self.sorted_diction[sw]
        result = ""
        for w in d:
            if w != word: result += "%s " % w
        return result

    def match(self, pattern):
        print pattern
        try:
            compiled_pattern = re.compile(pattern.upper())
        except:
            return "Bad pattern"
        result = ""
        for w in self.diction:
            if compiled_pattern.match(w):
                result += "%s " % w
        if result == "": return "No matches"
        return result

words = Words()
mention_text_pattern = re.compile('\W*<@U[A-Z0-9]*>')
anagram_text_pattern = re.compile('\W*<@U[A-Z0-9]*>(.*[Aa]nagram(s of)?)?\W*(\w+)')
pattern_text_pattern = re.compile('\W*<@U[A-Z0-9]*>.*([Mm]atch(ing)?)\s+(\S+)')

class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        return "Hello World!"

    def process_request(self, text):
        pattern_match = pattern_text_pattern.match(text)
        if pattern_match:
            word = pattern_match.group(3)
            if not word.startswith('^'): word = ".*" + word
            word = re.sub("<http://[^|]*\|(\S+)>", "\\1", word)
            return words.match(word)

        anagram_match = anagram_text_pattern.match(text)
        if anagram_match:
            word = anagram_match.group(3)
            anagrams = words.anagram(word)
            if anagrams != "": return anagrams
            else: return "No anagrams of " + word


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def mention(self):
        body = cherrypy.request.json
        if 'challenge' in body:
            return {'challenge':body['challenge']}
        print body
        if 'event' in body:
            event = body['event']
            if 'type' in event and event['type'] in (u'app_mention', u'message') and mention_text_pattern.match(event['text']):
                reqdata = {'token': TOKEN,
                        'channel': event['channel'],
                        'text': "I didn't understand you"}
                text = event['text']
                try:
                    reqdata['text'] = self.process_request(text)
                except (IndexError, ValueError, AttributeError): pass
                print reqdata
                print requests.post('https://api.slack.com/api/chat.postMessage', reqdata)
        return {}


cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081})
cherrypy.quickstart(HelloWorld())
