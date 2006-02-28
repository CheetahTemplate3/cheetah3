#!/bin/bash
cheetah compile _SiteTemplate.tmpl
pages="index credits contribute download examples learn praise whouses"
for pageId in $pages; do
   echo $pageId
   env pageId=$pageId python _SiteTemplate.py --env > ${pageId}.html
done
