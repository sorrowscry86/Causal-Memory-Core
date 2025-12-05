@echo off
cd /d "D:\Development\Causal Memory Core"
python -m pytest tests\test_memory_core.py -k "test_query" -v
