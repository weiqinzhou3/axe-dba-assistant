# Validation Tool

`validate_result.py` provides reusable three-layer result validation for assistant output contracts.

Phase-01 uses it from `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py`. It checks generic fields, status values, source presence, and numeric consistency. Redis-specific risk rules stay inside the Redis RDB Skill package.
