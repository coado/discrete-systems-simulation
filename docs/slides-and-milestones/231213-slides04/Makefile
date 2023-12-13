pdf: slides04.md
	pandoc -t beamer slides04.md -o slides04.pdf \
	-V theme=Antibes \
	--metadata-file=config-slides.yaml \
	--metadata date="`date +'%d %B %Y'`" \
	--slide-level=2 \
	--citeproc \
	--csl=bib/acm-sig-proceedings-long-author-list.csl \
	--bibliography=bib/milestone01.bib \
