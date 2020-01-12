from concurrent import futures
import logging
import re

import grpc

import wordfind_pb2
import wordfind_pb2_grpc

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
        result = []
        for w in d:
            if w != word: result.append(w)
        return result

    def match(self, pattern):
        try:
            compiled_pattern = re.compile(pattern.upper())
        except:
            return ["Bad pattern"]
        result = []
        for w in self.diction:
            if compiled_pattern.match(w):
                result.append(w)
        return result

class WordFindServicer(wordfind_pb2_grpc.WordFindServicer):
    def __init__(self):
        self.words = Words()

    def GetAnagrams(self, request, context):
        anagrams = self.words.anagram(request.word)
        for w in anagrams:
            yield wordfind_pb2.Word(word=w)

    def GetMatchingWords(self, request, context):
        words = self.words.match(request.pattern)
        for w in words:
            yield wordfind_pb2.Word(word=w)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    wordfind_pb2_grpc.add_WordFindServicer_to_server(WordFindServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
