#
#/////////////////////////////////////////////////////////////////////////
#
# Apply a patch to the SQL statement that caused the error notification
#    from the ODBC system.
#        
#/////////////////////////////////////////////////////////////////////////
#
import sys
pkg = sys.modules[__package__]

from datetime import datetime, date
import re

#Symbol that represents the start of a name
START_CHAR = '['
ESC_START_CHAR = re.escape(START_CHAR)

#End of name symbol
END_CHAR = ']'
ESC_END_CHAR = re.escape(END_CHAR)

NAME_PATTERN = rf'(?:{ESC_START_CHAR}[^{ESC_END_CHAR}]+{ESC_END_CHAR}|\S+)'
JOIN_TYPES = r"INNER|LEFT\s+OUTER|RIGHT\s+OUTER"
#
#//////////////////////////////////
#[SQLPatch ID]:SELECT_PATCH_0010
#//////////////////////////////////
#[SQL statements that cannot be executed in the ACCESS ODBC system]
#  SELECT column-name-list FROM [django_admin_log] INNER JOIN [accounts_user] ON ([django_admin_log].[user_id] = [accounts_user].[id]) LEFT OUTER JOIN [django_content_type] ON ([django_admin_log].[content_type_id] = [django_content_type].[id]) WHERE ... ORDER BY ...
#
#[SQL statements that have been modified to be executable]
#  SELECT column-name-list FROM ( [django_admin_log] INNER JOIN [accounts_user] ON ([django_admin_log].[user_id] = [accounts_user].[id]) ) LEFT OUTER JOIN [django_content_type] ON ([django_admin_log].[content_type_id] = [django_content_type].[id]) WHERE ... ORDER BY ...
#                              ^^^                                                                                                      ^^^                  
# The FROM clause must be immediately followed by parentheses.
# The first join clause must be enclosed in parentheses.
#
SELECT_PATCH_0010_regex = rf"""
  ^SELECT\s+(?P<columns>.+?)
    \s+FROM\s+(?P<table_name>{NAME_PATTERN})
    \s+(?P<join1_type>{JOIN_TYPES})\s+JOIN\s+(?P<join1_cond>.+?)
    \s+(?P<join2_type>{JOIN_TYPES})\s+JOIN\s+(?P<join2_cond>.+?)
    (?:\s+WHERE\s+(?P<where_clause>.+?))?
    (?:\s+ORDER\s+BY\s+(?P<order_by_clause>.+?))?
    $
"""
SELECT_PATCH_0010_cpl = re.compile(SELECT_PATCH_0010_regex,
                            re.IGNORECASE | re.VERBOSE | re.DOTALL)

def SELECT_PATCH_0010(input_sql):
    match = SELECT_PATCH_0010_cpl.match(input_sql.strip())
    if not match:
        return False, "Parsing failed (pattern not matched)", None

    p = match.groupdict()
    
    # Reconstructing SQL statements
    reconstructed = (
        f"SELECT {p['columns']} FROM ( {p['table_name']} "
        f" {p['join1_type']} JOIN {p['join1_cond']} )"
        f" {p['join2_type']} JOIN {p['join2_cond']}  "
    )
    
    # Add any part in order
    if p['where_clause']:
        reconstructed += f" WHERE {p['where_clause']}"
    if p['order_by_clause']:
        reconstructed += f" ORDER BY {p['order_by_clause']}"
    
    return True, reconstructed, p

#
#//////////////////////////////
#      Name Truncation
#//////////////////////////////
#
TruncateName_SQLStmt = [
 {'SMP': 'ALTER TABLE  [TableName]   ADD CONSTRAINT [ConstraintName]          FOREIGN KEY ([ColumnList],[ ]) REFERENCES [TableName] ([ColumnList]);',
  'fmt':r'ALTER TABLE \[([^\[\]]+)\] ADD CONSTRAINT \[([^\[\]]{64})[^\[\]]*\] FOREIGN KEY ([\s\S]+)$',
  'sql':r'ALTER TABLE [\1] ADD CONSTRAINT [\2] FOREIGN KEY \3'},

 {'SMP': 'CREATE INDEX [ConstraintName] ON [TableName] ([ColumnList]);',
  'fmt':r'CREATE INDEX \[([^\[\]]{64})[^\[\]]*\] ON ([\s\S]+)$',
  'sql':r'CREATE INDEX [\1] ON \2'},

 {'SMP': 'CREATE UNIQUE INDEX [ConstraintName] ON [TableName] ([ColumnList]);',
  'fmt':r'CREATE UNIQUE INDEX \[([^\[\]]{64})[^\[\]]*\] ON ([\s\S]+)$',
  'sql':r'CREATE UNIQUE INDEX [\1] ON \2'},

]

TruncateName_SQLStmt_cpl = [
  re.compile(item['fmt']) for item in TruncateName_SQLStmt
]


def TRUNCATE_NAME_PATCH(sql):
    idx = 0
    for item in TruncateName_SQLStmt_cpl:
        if item.match(sql):
            trunc_sql =item.sub(TruncateName_SQLStmt[idx]['sql'], sql)
            return True, trunc_sql
        else:
            idx = idx + 1
            continue
    return False, ''


#
#/////////////////////////////////////////////////////////////////////////////////
#             Creating a table fails when a column has a default value.
# When you register a default value for a column, the following SQL statement is generated:  
#   CREATE TABLE [tableName] ([id] COUNTER NOT NULL PRIMARY KEY,
#                             [columnName] varchar(30)  DEFAULT ? NOT NULL)
#   params=('ABC',)
#
# This is the format of a parameterized SQL statement.
# Microsoft Access SQL statements do not recognize parameter queries in table creation SQL.
#
# NOTE:
#   https://learn.microsoft.com/en-us/office/vba/access/concepts/structured-query-language/modify-a-table-s-design-using-access-sql
#
# The DEFAULT statement can be executed only through the Access OLE DB provider and ADO.
# It will return an error message if used through the Access SQL View user interface.
#
#
#/////////////////////////////////////////////////////////////////////////////////
#
def patch_create_table(sql, params):
    if params is None:
        return sql
    if len(sql) < 13:
        return sql
    st = sql[:13].upper()
    if st != 'CREATE TABLE ':
        return sql

    patched_sql = sql

    for param in params:
        # replace
        ret = patched_sql.replace('DEFAULT ?', '', 1)
        if ret != patched_sql:
            patched_sql = ret
        else:
            raise ValueError('*** ToDo ***')

    return  patched_sql

    #
    # This is the process of embedding parameters into a string.
    # Unfortunately, this doesn't work on ODBC systems.
    #
    for param in params:
        if param is None:
            val = "NULL"
        
        elif isinstance(param, bool):
            # Access: True=-1, False=0
            val = "-1" if param else "0"
        
        elif isinstance(param, (int, float)):
            val = str(param)
        
        elif isinstance(param, (datetime, date)):
            # Access: #YYYY-MM-DD HH:MM:SS#
            val = f"#{param.strftime('%Y-%m-%d %H:%M:%S')}#"
        
        else:
            # Strings
            p_str = str(param)
            
            # LIKE operator 
            # SQL: '%' -> Access: '*'
            # SQL: '_' -> Access: '?'
            p_str = p_str.replace('%', '*').replace('_', '?')
            
            # Escaping single quotes
            safe_val = p_str.replace("'", "''")
            #val = f"'{safe_val}'"
            val = f"{safe_val}"

        
        # replace
        ret = patched_sql.replace("? NOT NULL", val, 1)
        if ret != patched_sql:
            patched_sql = ret
        else:
            patched_sql = patched_sql.replace("?", val, 1)

    return patched_sql



#
#/////////////////////////////////////////////////////////////
#
#     Excel Select Patch
#
#/////////////////////////////////////////////////////////////
#

clng_cpl = re.compile(r'CLNG\((\w+)\)')

def excel_select_patch(sql):
    if not pkg.__excel_odbc_driver__:
        return sql


    new_sql = sql
    sql_len = len(sql) 



    #(before)SELECT MAX(CLNG(id)) FROM [Sheet1$]
    #( after)SELECT MAX(CLNG(IIF(ISNULL(id),0,id))) FROM [Sheet1$] 
    if sql_len > 26:
        st = sql[:26].upper()
        if st == 'SELECT MAX(CLNG(ID)) FROM ':
            new_sql = clng_cpl.sub(r'CLNG(IIF(ISNULL(\1),0,\1))', sql)
            return new_sql
        

    return new_sql



#//////////////////////////////
if __name__ == '__main__':
#//////////////////////////////
    print("*"*30)
    print("       SELECT_PATCH_0010")
    print("*"*30)
    test_select_0010 = [
        'SELECT shop_id, COUNT(*) FROM Shops INNER JOIN Staffs ON s1=s2 LEFT OUTER JOIN Sales ON s2=s3',
        'SELECT category, price FROM Products INNER JOIN Tags ON t1=t2 INNER JOIN Stock ON s1=s2 ORDER BY price DESC',
        'SELECT dept_id, salary FROM Dept INNER JOIN Emp ON e1=e2 INNER JOIN Project ON p1=p2 where salary > 50000',
        'SELECT a, b FROM T1 INNER JOIN T2 ON a=b INNER JOIN T3 ON b=c WHERE a > 10 ORDER BY a ASC'
    ]
    print(f"{'Status':<4} | {'Extraction summary'}")
    print("-" * 60)
    for sql in test_select_0010:
        success, rebuilt, data = SELECT_PATCH_0010(sql)
        status = "✅OK" if success else "❌NG"
        summary = f"WHERE BY: {data['where_clause'] or '❌'} / ORDER BY: {data['order_by_clause'] or '❌'}"
        print(f"{status:<4} | {summary}")
        if success:
            print(f"{rebuilt}\n")
            for key, val in data.items():
                if val: print(f"  {key}: {val}")
            print("-"*30,"\n")

    sql_test = [
        'ALTER TABLE [TableName] ADD CONSTRAINT [C123456789012345678901234567890123456789012345678901234567890123456789] FOREIGN KEY ([Col1], [Col2], [Col3]) REFERENCES [TableName] ([Col1], [Col2], [Col3]);',
        'CREATE INDEX [C123456789012345678901234567890123456789012345678901234567890123456789] ON [tableName] ([ColumnList);',
        'CREATE UNIQUE INDEX [C123456789012345678901234567890123456789012345678901234567890123456789] ON [tableName] ([Col1], [Col2], [Col3]);',
        'End'
    ]
    for sql in  sql_test:
        flag, trunc_sql= TRUNCATE_NAME_PATCH(sql)
        print(f"flag={flag}")
        print(f"sql ={sql}")
        print(f"tsql={trunc_sql}\n")

