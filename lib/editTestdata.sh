#!/bin/bash
#set -x
#used to find and replace the http urls in the $2(test_data.py)  file using the data specified in $1(env_specific_data)
while read line
do 
    s1=$(echo $line | cut -f1 -d ' ')
    s2=$(echo $line | cut -f2 -d ' ')
    s1=$(sed -e  s#'/'#'\\/'#g  <<< "$s1"| sed s#'\.'#'\\\.'#g)
    s2=$(sed -e  s#'/'#'\\/'#g  <<< "$s2"| sed s#'\.'#'\\\.'#g)
    sed -i s#"$s1"#$s2#g $2
done < $1
