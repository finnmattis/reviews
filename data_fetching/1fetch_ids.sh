#!/bin/bash
esearch -db pubmed -query "systematic review[pt]" | efetch -format uid > ids.txt