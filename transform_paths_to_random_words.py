#!/usr/bin/env python3
#
# generate a new corpus from the set of paths on your filesystem
#
# usage is something like
#
#   sudo find / -type f | ./transform_paths_to_random_words.py | gzip -c -9 > paths.data.gz

import functools
import random
import re
import sys

wordlist = [wline.strip() for wline in open('bigwordlist.txt', 'rb')]
# add a few very non-utf8 sequences to make sure those can work too
wordlist.extend([
    b'\0\0\0\0\0\0\0\0',
    b'\xff\xff\xff\xff\xffabc\0\r',
])

hexchars_re = re.compile(rb'[^\x00-\x7f]')


class PushbackableIterator:
    def __init__(self, underiter):
        self.underiter = underiter
        self.pushback_stack = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.pushback_stack:
            return self.pushback_stack.pop(-1)
        return next(self.underiter)

    def pushback(self, item):
        self.pushback_stack.append(item)


def convert_to_hex_escape(re_match):
    return b'\\x%02x' % ord(re_match.group(0))


def encode(outpath):
    p = outpath.replace(b'\\', b'\\\\').replace(b'\n', b'\\n').replace(b'\r', b'\\r').replace(b'\t', b'\\t')
    return hexchars_re.sub(convert_to_hex_escape, p)


def writer(outf, outpath):
    outpath_enc = encode(outpath)
    outf.write(b'\t%s\t%d\n' % (outpath_enc, len(outpath)))


def prepare(line):
    return line.lstrip(b'/').rstrip(b'\n')
    

def choose_word():
    return random.choice(wordlist)


def transform(pfx, xform, paths, out):
    usedhere = set()
    for path in paths:
        if not path.startswith(pfx):
            paths.pushback(path)
            return
        remainder = path[len(pfx):]
        parts = remainder.split(b'/', 1)
        while True:
            newver = choose_word()
            if newver not in usedhere:
                break
        usedhere.add(newver)
        if len(parts) > 1:
            paths.pushback(path)
            transform(pfx + parts[0] + b'/', xform + newver + b'/', paths, out)
        else:
            out(xform + newver)


def main(inf, outf):
    transform(b'', b'', PushbackableIterator(map(prepare, inf)), functools.partial(writer, outf))


if __name__ == "__main__":
    try:
        main(sys.stdin.buffer, sys.stdout.buffer)
    except BrokenPipeError:
        pass
