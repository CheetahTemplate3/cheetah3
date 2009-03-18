RST = rst2html.py --stylesheet=default.css --link-stylesheet  --initial-header-level=2

#%.html: %.txt
#	${RST} $< $@

all:
	#${RST} --warnings=/dev/null index.txt index.html
	${RST} 01_introduction.txt 01_introduction.html
	${RST} 02_glossary.txt 02_glossary.html
	${RST} 03_gettingStarted.txt 03_gettingStarted.html
	${RST} 04_howItWorks.txt 04_howItWorks.html
	${RST} 04_howItWorks.txt 04_howItWorks.html
	${RST} 13a_precompiledTemplateModules.txt 13a_precompiledTemplateModules.html


# vim: sw=8 ts=8 noexpandtab ai
