DOCNAME=users_guide
PYTHONSRC=python
MKHOWTO=$(PYTHONSRC)/Doc/tools/mkhowto
MAIN_TEX_FILE= users_guide.tex

all: pdf ps html text

pdf:
	$(MKHOWTO) --pdf $(MAIN_TEX_FILE)
	mv $(DOCNAME).pdf ../

ps:
	$(MKHOWTO) --ps $(MAIN_TEX_FILE)
	mv $(DOCNAME).ps ../
html:
	-rm -rf $(DOCNAME)
	$(MKHOWTO) --html --split 1 --iconserver . $(MAIN_TEX_FILE)
	-rm -R ../$(DOCNAME)_html
	mv $(DOCNAME) ../$(DOCNAME)_html

text:
	$(MKHOWTO) --text $(MAIN_TEX_FILE)
	mv $(DOCNAME).txt ../

clean:
	-rm -rf $(DOCNAME)
	-rm *.aux *.l2h *~
	-rm -rf ../html

