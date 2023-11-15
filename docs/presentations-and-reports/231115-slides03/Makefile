pdf: slides03.md
	pandoc -t beamer slides03.md -o slides03.pdf \
	--metadata date="`date +'%d %B %Y'`" \
	--metadata-file=config-slides.yaml \
	--slide-level=2 \
	--citeproc \
	--csl=bib/acm-sig-proceedings-long-author-list.csl \
	--bibliography=bib/milestone01.bib \
	-N
