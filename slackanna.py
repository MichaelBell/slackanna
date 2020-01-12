import requests
import re

import cherrypy
import grpc

import wordfind_pb2
import wordfind_pb2_grpc

with open("token") as file:
  TOKEN=file.read().strip()

class WordStub:
    def anagram(self, word):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = wordfind_pb2_grpc.WordFindStub(channel)
            anagrams = stub.GetAnagrams(wordfind_pb2.Word(word=word))
            return " ".join([w.word for w in anagrams])

    def match(self, pattern):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = wordfind_pb2_grpc.WordFindStub(channel)
            anagrams = stub.GetMatchingWords(wordfind_pb2.Pattern(pattern=pattern))
            return " ".join([w.word for w in anagrams])

words = WordStub()
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
        print(body)
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
                print(reqdata)
                print(requests.post('https://api.slack.com/api/chat.postMessage', reqdata))
        return {}

if __name__ == "__main__":
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8081})
    cherrypy.quickstart(HelloWorld())
