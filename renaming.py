#!/usr/bin/env python
import os, sys

people = { 
	"Initial Lastname":"Firstname Lastname", 
	}

input = sys.stdin
output = sys.stdout

if len(sys.argv) > 1:
	input = open(sys.argv[1])

for s in input.xreadlines():
	if s.find("author"):
		for k, v in people.iteritems():
			if s.find(k):
				s = s.replace(k, v)
	output.write(s)
	
