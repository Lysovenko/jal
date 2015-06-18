#!/bin/bash
xgettext --language=Python -cNOTE -o jml.pot ../../*.py
msguniq  jml.pot -u -o jml.pot
for i in *.po
do
    msgmerge -U "$i" jml.pot
    fnam="../locale/${i%.po}/LC_MESSAGES/jml.mo"
    if [ "$i" -nt "$fnam" ] 
    then
	echo $fnam
	rm -f "$fnam"
	msgfmt "$i" -o "$fnam"
    fi
done


