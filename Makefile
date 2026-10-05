PY ?= python

.PHONY: all data test clean help
help:
	@echo "make data   - télécharge les jeux publics (si data/raw est vide)"
	@echo "make all    - pipeline complet : manifest, bronze, silver, dq, gold, ml, analysis, dashboard, docs"
	@echo "make test   - tests unitaires et tests d'entrepôt"
	@echo "make clean  - supprime l'entrepôt et les rapports générés"

data:
	$(PY) scripts/fetch_data.py

all:
	$(PY) -m banklens.pipeline

test:
	$(PY) -m unittest discover -s tests -v

clean:
	rm -f warehouse/banklens.db reports/results/*.csv reports/answers.json reports/ANSWERS.md reports/pipeline.log
