from david8.core.fn_generator import SeparatedArgsFnFactory as _SeparatedArgsFnFactory

# https://clickhouse.com/docs/sql-reference/functions/string-functions#concatWithSeparator
concat_with_separator = _SeparatedArgsFnFactory(name='concatWithSeparator', separator=', ')
