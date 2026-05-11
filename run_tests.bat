@echo off
cd /d C:\Users\donald\Repositories\dta-crag
python -m pytest tests/test_corpus.py tests/test_prompts.py tests/test_memory.py tests/test_nodes.py -v -p no:langsmith > test_results5.txt 2>&1
