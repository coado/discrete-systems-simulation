pdf: slides02.md
	pandoc -t beamer slides02.md -o slides02.pdf \
	-V theme=Antibes \
	--metadata-file=config-slides.yaml \
	--metadata date="`date +'%d %B %Y'`" \
	--slide-level=2 \
	--citeproc \
	--csl=bib/acm-sig-proceedings-long-author-list.csl \
	--bibliography=bib/milestone01.bib \
