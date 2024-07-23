#!/bin/bash
esearch -db pubmed -query "systematic review[sb]" | efetch -format uid > ids.txt