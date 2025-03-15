.PHONY: ci_init_sql

ci_init_sql:
	psql -p 5432 -U postgres -d postgres -a -W -f init.sql
