# You must change PYTHONSRC to the path of your Python source distributon.
# OR just create a symlink that matches this path.
PYTHONSRC=/usr/local/src/Python-source
DOCNAME=users_guide
MKHOWTO=$(PYTHONSRC)/Doc/tools/mkhowto
MAIN_TEX_FILE= users_guide.tex

all: ps pdf html htmlMultiPage text

almost-all: ps html htmlMultiPage text

pdf:
	$(MKHOWTO) --pdf $(MAIN_TEX_FILE)
	mv $(DOCNAME).pdf ../

ps:
	$(MKHOWTO) --ps $(MAIN_TEX_FILE)
	mv $(DOCNAME).ps ../
html:
	-rm -rf $(DOCNAME)
	$(MKHOWTO) --html --split 1 --iconserver . $(MAIN_TEX_FILE)
	-rm -rf ../$(DOCNAME)_html
	mv $(DOCNAME) ../$(DOCNAME)_html

htmlMultiPage:
	-rm -rf $(DOCNAME)
	$(MKHOWTO) --html --iconserver . $(MAIN_TEX_FILE)
	-rm -rf ../$(DOCNAME)_html_multipage
	mv $(DOCNAME) ../$(DOCNAME)_html_multipage

text:
	$(MKHOWTO) --text $(MAIN_TEX_FILE)
	mv $(DOCNAME).txt ../

clean:
	-rm -rf $(DOCNAME)
	-rm -f *.aux *.l2h *~ *.log *.ind *.bkm *.how *.toc
	-rm -rf ../html

