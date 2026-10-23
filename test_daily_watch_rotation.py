"""Run with python -B test_daily_watch_rotation.py; no database writes."""
import ast
from pathlib import Path

# Isolate the pure calculation without importing MongoDB or Discord dependencies.
tree = ast.parse(Path(__file__).with_name('db_methods').joinpath('general.py').read_text())
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'daily_watch_state')
scope = {}
exec(compile(ast.Module(body=[node], type_ignores=[]), 'general.py', 'exec'), scope)
state = scope['daily_watch_state']
interval = 43200
assert state(99, None, 0, 100 * interval + 1, interval, 101) == (99, 100 * interval)
assert state(99, 0, 0, interval - 1, interval, 101) == (99, 0)
assert state(99, 0, 0, interval, interval, 101) == (100, interval)
assert state(99, 0, 0, 3 * interval, interval, 101) == (1, 3 * interval)
assert state(1, 3 * interval, 0, 3 * interval + 1, interval, 101) == (1, 3 * interval)
assert state(99, 0, 0, 102 * interval, interval, 101) == (100, 102 * interval)
print('Daily watch migration, boundaries, catch-up and repeat checks passed')
